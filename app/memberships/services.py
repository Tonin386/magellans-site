"""Enregistrement des adhésions HelloAsso (webhook et synchronisation)."""

import logging
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from core.audit import log_activity
from core.emails import send_templated_email
from core.models import SiteSettings
from core.utils import normalize_phone
from members.models import Member, Person

from .helloasso import HelloAssoClient, HelloAssoError
from .models import Membership, Season

logger = logging.getLogger("magellans.memberships")

VALID_STATES = {"Processed", "Registered"}
REFUNDED_STATES = {"Refunded", "Refunding", "Contested"}


@dataclass
class ProcessReport:
    created: list = field(default_factory=list)
    updated: list = field(default_factory=list)
    unchanged: int = 0
    cancelled: list = field(default_factory=list)
    ignored: list = field(default_factory=list)
    accounts: list = field(default_factory=list)

    def merge(self, other):
        self.created += other.created
        self.updated += other.updated
        self.unchanged += other.unchanged
        self.cancelled += other.cancelled
        self.ignored += other.ignored
        self.accounts += other.accounts

    def summary(self):
        parts = []
        if self.created:
            parts.append(f"{len(self.created)} nouvelle(s) adhésion(s)")
        if self.updated:
            parts.append(f"{len(self.updated)} mise(s) à jour")
        if self.unchanged:
            parts.append(f"{self.unchanged} déjà à jour")
        if self.cancelled:
            parts.append(f"{len(self.cancelled)} annulée(s) ou remboursée(s)")
        if self.accounts:
            parts.append(f"{len(self.accounts)} compte(s) créé(s)")
        if self.ignored:
            parts.append(f"{len(self.ignored)} ignorée(s)")
        return ", ".join(parts) or "rien à faire"


# ------------------------------------------------------------------ Utilitaires
def _norm(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    return " ".join(text.lower().replace("-", " ").split())


def _cents(value):
    try:
        return (Decimal(int(value or 0)) / 100).quantize(Decimal("0.01"))
    except (TypeError, ValueError):
        return Decimal("0")


def _valid_email(value):
    value = (value or "").strip()
    try:
        validate_email(value)
    except ValidationError:
        return ""
    return value.lower()


def extract_contact(item, payer):
    """Identité de l'adhérent·e : le bénéficiaire de la ligne, complété par les champs personnalisés."""
    user = item.get("user") or {}
    first_name = (user.get("firstName") or payer.get("firstName") or "").strip()
    last_name = (user.get("lastName") or payer.get("lastName") or "").strip()
    email, phone = "", ""
    for custom in item.get("customFields") or []:
        name = _norm(custom.get("name"))
        kind = custom.get("type")
        answer = (custom.get("answer") or "").strip()
        if not answer:
            continue
        if kind == "Email" or "mail" in name:
            email = email or _valid_email(answer)
        elif kind == "Phone" or "phone" in name or "telephone" in name or name.startswith("tel"):
            phone = phone or normalize_phone(answer)
    if not email:
        email = _valid_email(payer.get("email"))
    return {"first_name": first_name[:30], "last_name": last_name[:30], "email": email, "phone": phone[:15]}


def _names_match(person, first_name, last_name):
    known_first, known_last = _norm(person.clean_first_name), _norm(person.clean_last_name)
    if not known_first and not known_last:
        return True
    return known_last == _norm(last_name) and (not known_first or known_first == _norm(first_name))


def find_person(contact):
    email = contact["email"]
    if email:
        account = Member.objects.filter(email__iexact=email).select_related("site_person").first()
        if account and account.person and _names_match(account.person, contact["first_name"], contact["last_name"]):
            return account.person
        for person in Person.objects.filter(email__iexact=email):
            if _names_match(person, contact["first_name"], contact["last_name"]):
                return person
    if contact["phone"] and contact["last_name"]:
        candidates = Person.objects.filter(last_name__iexact=contact["last_name"], phone=contact["phone"])
        if candidates.count() == 1:
            return candidates.first()
    return None


def get_or_create_person(contact):
    person = find_person(contact)
    if person is None:
        shared = bool(contact["email"]) and Person.objects.filter(email__iexact=contact["email"]).exists()
        person = Person.objects.create(
            first_name=contact["first_name"],
            last_name=contact["last_name"],
            email=contact["email"] or None,
            phone=contact["phone"],
            role="X",
            additional_notes=("Adresse e-mail partagée avec une autre fiche (adhésion HelloAsso)." if shared else None),
        )
        return person, True
    changed = []
    if not person.clean_first_name and contact["first_name"]:
        person.first_name = contact["first_name"]
        changed.append("first_name")
    if not person.clean_last_name and contact["last_name"]:
        person.last_name = contact["last_name"]
        changed.append("last_name")
    if not person.phone_display and contact["phone"]:
        person.phone = contact["phone"]
        changed.append("phone")
    if not person.email and contact["email"]:
        person.email = contact["email"]
        changed.append("email")
    if changed:
        person.save()
    return person, False


def ensure_account(person, membership, *, send_emails=True):
    """Crée un compte (inactif, invitation par e-mail) si la personne n'en a pas encore."""
    from members.auth_views import send_invitation_email

    if person.site_profile_id:
        account = person.site_profile
        if send_emails:
            if account.is_active and account.has_usable_password():
                send_templated_email("membership_welcome", {"membership": membership}, [account.email])
            else:
                send_invitation_email(account, membership)
        return None
    email = person.email
    if not email or Member.objects.filter(email__iexact=email).exists():
        return None
    if not SiteSettings.load().membership_auto_accounts:
        return None
    account = Member.objects.create_user(email, None, is_active=False, person=person)
    if send_emails:
        send_invitation_email(account, membership)
    return account


# --------------------------------------------------------------------- Traitement
def process_order(order, *, send_emails=True, request=None, verified=True):
    """Enregistre les adhésions d'une commande HelloAsso (structure de /v5/orders/{id})."""
    report = ProcessReport()
    form_slug = order.get("formSlug") or ""
    organization = order.get("organizationSlug") or ""
    season = Season.objects.filter(helloasso_form_slug=form_slug).first() if form_slug else None
    if season is None:
        report.ignored.append(f"Campagne « {form_slug or '?'} » non rattachée à une saison.")
        return report
    if organization and season.helloasso_org_slug and organization != season.helloasso_org_slug:
        report.ignored.append(f"Organisation inattendue : {organization}.")
        return report
    if order.get("formType") not in (None, "Membership"):
        report.ignored.append(f"Formulaire de type {order.get('formType')} ignoré.")
        return report

    payer = order.get("payer") or {}
    items = order.get("items") or []
    membership_items = [item for item in items if item.get("type") == "Membership"]
    donation = sum((_cents(item.get("amount")) for item in items if item.get("type") == "Donation" and item.get("state") in VALID_STATES), Decimal("0"))
    order_date = parse_datetime(order.get("date") or "") or timezone.now()
    if timezone.is_naive(order_date):
        order_date = timezone.make_aware(order_date)
    payer_name = f"{payer.get('firstName', '')} {payer.get('lastName', '')}".strip()

    for index, item in enumerate(membership_items):
        item_id = item.get("id")
        state = item.get("state")
        with transaction.atomic():
            existing = Membership.objects.select_for_update().filter(helloasso_item_id=item_id).first() if item_id else None
            if state not in VALID_STATES:
                if existing and existing.is_active:
                    existing.status = Membership.Status.REFUNDED if state in REFUNDED_STATES else Membership.Status.CANCELLED
                    existing.notes = (existing.notes + f"\nStatut HelloAsso : {state} ({timezone.now():%d/%m/%Y}).").strip()
                    existing.save()
                    report.cancelled.append(existing)
                    log_activity(request, "membership-cancelled", f"Adhésion {season.label} de {existing.person} : {state}.", target=existing, category="memberships")
                else:
                    report.ignored.append(f"Ligne {item_id} à l'état {state}.")
                continue

            card_url = item.get("membershipCardUrl") or ""
            if existing:
                fields = []
                if card_url and existing.membership_card_url != card_url:
                    existing.membership_card_url = card_url
                    fields.append("membership_card_url")
                if not existing.is_active:
                    existing.status = Membership.Status.ACTIVE
                    fields.append("status")
                if fields:
                    existing.save(update_fields=fields + ["updated_at"])
                    report.updated.append(existing)
                else:
                    report.unchanged += 1
                continue

            contact = extract_contact(item, payer)
            person, _created_person = get_or_create_person(contact)
            membership = (
                Membership.objects.select_for_update()
                .filter(person=person, season=season, helloasso_item_id__isnull=True, status=Membership.Status.ACTIVE)
                .first()
            )
            upgraded = membership is not None
            membership = membership or Membership(person=person, season=season)
            membership.status = Membership.Status.ACTIVE
            membership.source = Membership.Source.HELLOASSO
            membership.amount = _cents(item.get("amount"))
            membership.donation = donation if index == 0 else Decimal("0")
            membership.payment_method = "card"
            membership.tier_label = (item.get("name") or "")[:200]
            membership.joined_at = order_date
            membership.helloasso_order_id = order.get("id")
            membership.helloasso_item_id = item_id
            membership.membership_card_url = card_url
            membership.payer_name = payer_name[:200]
            membership.payer_email = _valid_email(payer.get("email"))
            if not verified:
                membership.notes = (membership.notes + "\nEnregistrée depuis une notification non vérifiée par l'API.").strip()
            membership.save()
            (report.updated if upgraded else report.created).append(membership)

        account = ensure_account(person, membership, send_emails=send_emails)
        if account:
            report.accounts.append(account)
        if not upgraded:
            log_activity(
                request,
                "membership-created",
                f"Nouvelle adhésion {season.label} : {person.display_name} ({membership.amount} €).",
                target=membership,
                category="memberships",
            )
            if send_emails:
                send_templated_email(
                    "membership_new_for_team",
                    {"membership": membership, "created_account": bool(account), "season_count": season.memberships.active().count()},
                    SiteSettings.load().recipients("memberships"),
                )
    return report


def _orders_from_items(items):
    """Regroupe les lignes renvoyées par /forms/.../items en commandes."""
    orders = {}
    for item in items:
        order_info = item.get("order") or {}
        order_id = order_info.get("id")
        order = orders.setdefault(
            order_id,
            {
                "id": order_id,
                "date": order_info.get("date"),
                "formSlug": order_info.get("formSlug"),
                "formType": order_info.get("formType"),
                "organizationSlug": order_info.get("organizationSlug"),
                "payer": item.get("payer") or {},
                "items": [],
            },
        )
        order["items"].append(item)
    return list(orders.values())


def refresh_season_from_helloasso(season, client=None):
    client = client or HelloAssoClient()
    form = client.form_public(season.helloasso_org_slug, season.helloasso_form_type or "Membership", season.helloasso_form_slug)
    tiers = [tier for tier in form.get("tiers") or [] if tier.get("tierType") == "Membership"]
    if tiers and tiers[0].get("price") is not None:
        season.price = _cents(tiers[0]["price"])
    season.helloasso_title = (form.get("title") or "")[:200]
    season.helloasso_start = parse_datetime(form.get("startDate") or "") if form.get("startDate") else None
    season.helloasso_end = parse_datetime(form.get("endDate") or "") if form.get("endDate") else None
    season.helloasso_state = (form.get("state") or "")[:30]
    return form


def sync_season(season, *, send_emails=False, client=None, request=None):
    """Récupère toutes les adhésions d'une campagne HelloAsso et complète la base."""
    if not season.has_helloasso:
        raise HelloAssoError("Cette saison n'est liée à aucune campagne HelloAsso.")
    client = client or HelloAssoClient()
    refresh_season_from_helloasso(season, client)
    items = list(client.form_items(season.helloasso_org_slug, season.helloasso_form_type or "Membership", season.helloasso_form_slug))
    report = ProcessReport()
    for order in _orders_from_items(items):
        report.merge(process_order(order, send_emails=send_emails, request=request))
    season.last_synced_at = timezone.now()
    season.save()
    log_activity(request, "helloasso-sync", f"Synchronisation HelloAsso de la saison {season.label} : {report.summary()}.", target=season, category="memberships")
    return report


def manual_membership(person, season, *, amount, payment_method, joined_at=None, notes="", created_by=None, request=None):
    membership = Membership.objects.create(
        person=person,
        season=season,
        source=Membership.Source.MANUAL,
        status=Membership.Status.ACTIVE,
        amount=amount or 0,
        payment_method=payment_method,
        joined_at=joined_at or timezone.now(),
        notes=notes,
        created_by=created_by,
    )
    log_activity(request or created_by, "membership-manual", f"Adhésion {season.label} saisie pour {person.display_name}.", target=membership, category="memberships")
    return membership


__all__ = [
    "HelloAssoError",
    "ProcessReport",
    "extract_contact",
    "manual_membership",
    "process_order",
    "refresh_season_from_helloasso",
    "sync_season",
]
