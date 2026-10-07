"""Saisons et adhésions (synchronisées avec les campagnes HelloAsso)."""

import datetime
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

CURRENT_SEASON_CACHE_KEY = "memberships:current-season:v1"

# Correspondance entre le type de formulaire HelloAsso et le segment d'URL public.
FORM_TYPE_PATHS = {
    "Membership": "adhesions",
    "Donation": "formulaires",
    "Event": "evenements",
    "CrowdFunding": "collectes",
    "PaymentForm": "paiements",
    "Shop": "boutiques",
}
PATH_FORM_TYPES = {path: form_type for form_type, path in FORM_TYPE_PATHS.items()}


def parse_helloasso_url(url):
    """Extrait (organisation, type de formulaire, slug) d'une URL de campagne HelloAsso.

    Accepte aussi bien l'ancienne interface que la nouvelle (préfixe ``/beta/``) et
    les URL de widget : ``https://www.helloasso.com/beta/associations/magellans/adhesions/adhesions-2026-2027``.
    """
    if not url:
        return None
    parsed = urlparse(url.strip())
    if not (parsed.hostname or "").endswith("helloasso.com"):
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if parts and parts[0] == "beta":
        parts = parts[1:]
    if len(parts) < 4 or parts[0] != "associations":
        return None
    organization, type_path, slug = parts[1], parts[2], parts[3]
    form_type = PATH_FORM_TYPES.get(type_path)
    if not form_type:
        return None
    return organization, form_type, slug


class Season(models.Model):
    label = models.CharField(
        "Saison", max_length=20, unique=True, help_text="Ex. « 2026-2027 ». Affiché sur tout le site."
    )
    start_date = models.DateField("Début de la saison")
    end_date = models.DateField("Fin de la saison")
    is_current = models.BooleanField(
        "Saison en cours",
        default=False,
        help_text="Une seule saison peut être « en cours » : c'est elle qui détermine qui est adhérent·e à jour.",
    )
    registrations_open = models.BooleanField("Adhésions ouvertes", default=True)
    helloasso_url = models.URLField(
        "Lien de la campagne HelloAsso",
        max_length=500,
        blank=True,
        help_text="Copier-coller le lien public de la campagne d'adhésion HelloAsso.",
    )
    helloasso_org_slug = models.CharField("Organisation HelloAsso", max_length=120, blank=True, editable=False)
    helloasso_form_type = models.CharField("Type de formulaire", max_length=30, blank=True, editable=False)
    helloasso_form_slug = models.CharField(
        "Identifiant de la campagne", max_length=200, blank=True, db_index=True, editable=False
    )
    helloasso_other_urls = models.TextField(
        "Autres campagnes HelloAsso de la saison",
        blank=True,
        help_text="Rarement utile : si une campagne a été recréée en cours de saison, coller ici le lien "
        "de l'ancienne (un lien par ligne) pour que ses adhésions comptent aussi dans cette saison.",
    )
    price = models.DecimalField(
        "Montant de la cotisation (€)", max_digits=8, decimal_places=2, null=True, blank=True
    )
    pitch = models.TextField(
        "Pourquoi adhérer ? (Markdown)",
        blank=True,
        help_text="Texte affiché sur la page d'adhésion pour cette saison.",
    )
    helloasso_title = models.CharField("Titre sur HelloAsso", max_length=200, blank=True, editable=False)
    helloasso_start = models.DateTimeField("Début de validité (HelloAsso)", null=True, blank=True, editable=False)
    helloasso_end = models.DateTimeField("Fin de validité (HelloAsso)", null=True, blank=True, editable=False)
    helloasso_state = models.CharField("État sur HelloAsso", max_length=30, blank=True, editable=False)
    last_synced_at = models.DateTimeField("Dernière synchronisation", null=True, blank=True, editable=False)
    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    updated_at = models.DateTimeField("Modifiée le", auto_now=True)

    class Meta:
        verbose_name = "Saison"
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_current"], condition=Q(is_current=True), name="unique_current_season"
            ),
            models.CheckConstraint(condition=Q(end_date__gt=models.F("start_date")), name="season_dates_order"),
        ]

    def __str__(self):
        return f"Saison {self.label}"

    # ------------------------------------------------------------------
    @classmethod
    def current(cls):
        season = cache.get(CURRENT_SEASON_CACHE_KEY, "missing")
        if season == "missing":
            season = cls.objects.filter(is_current=True).first()
            cache.set(CURRENT_SEASON_CACHE_KEY, season, 300)
        return season

    @classmethod
    def for_date(cls, day):
        return cls.objects.filter(start_date__lte=day, end_date__gte=day).order_by("-start_date").first()

    @classmethod
    def for_helloasso_form(cls, form_slug):
        """Saison rattachée à une campagne HelloAsso (campagne principale ou campagne secondaire)."""
        if not form_slug:
            return None
        season = cls.objects.filter(helloasso_form_slug=form_slug).first()
        if season is None:
            season = next(
                (s for s in cls.objects.exclude(helloasso_other_urls="") if any(f[2] == form_slug for f in s.helloasso_forms)),
                None,
            )
        return season

    @classmethod
    def guess_dates(cls, label):
        """« 2026-2027 » → (1er septembre 2026, 31 août 2027)."""
        try:
            first = int(label.split("-")[0])
        except (ValueError, IndexError):
            first = timezone.localdate().year
        return datetime.date(first, 9, 1), datetime.date(first + 1, 8, 31)

    def save(self, *args, **kwargs):
        parsed = parse_helloasso_url(self.helloasso_url)
        if parsed:
            self.helloasso_org_slug, self.helloasso_form_type, self.helloasso_form_slug = parsed
        elif not self.helloasso_url:
            self.helloasso_org_slug = self.helloasso_form_type = self.helloasso_form_slug = ""
        with transaction.atomic():
            if self.is_current:
                Season.objects.exclude(pk=self.pk).filter(is_current=True).update(is_current=False)
            super().save(*args, **kwargs)
        cache.delete(CURRENT_SEASON_CACHE_KEY)

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        cache.delete(CURRENT_SEASON_CACHE_KEY)
        return result

    # ------------------------------------------------------------------
    @property
    def has_helloasso(self):
        return bool(self.helloasso_form_slug and self.helloasso_org_slug)

    @property
    def helloasso_forms(self):
        """(organisation, type, identifiant) de chaque campagne de la saison, la principale en premier."""
        forms = []
        if self.has_helloasso:
            forms.append((self.helloasso_org_slug, self.helloasso_form_type or "Membership", self.helloasso_form_slug))
        for line in self.helloasso_other_urls.splitlines():
            parsed = parse_helloasso_url(line)
            if parsed and parsed not in forms:
                forms.append(parsed)
        return forms

    @property
    def helloasso_public_url(self):
        if not self.has_helloasso:
            return ""
        path = FORM_TYPE_PATHS.get(self.helloasso_form_type, "adhesions")
        return f"https://www.helloasso.com/associations/{self.helloasso_org_slug}/{path}/{self.helloasso_form_slug}"

    @property
    def join_url(self):
        """Lien « Adhérer » : celui saisi par le CA (éventuellement la nouvelle interface /beta/)."""
        return self.helloasso_url or self.helloasso_public_url

    @property
    def widget_url(self):
        return f"{self.helloasso_public_url}/widget" if self.has_helloasso else ""

    @property
    def is_open(self):
        return self.registrations_open and timezone.localdate() <= self.end_date and bool(self.join_url)

    @property
    def is_ongoing(self):
        return self.start_date <= timezone.localdate() <= self.end_date

    def stats(self):
        # Une personne qui a payé deux fois la même saison ne compte qu'une fois.
        return self.memberships.active().aggregate(
            count=Count("person", distinct=True), total=Sum("amount"), donations=Sum("donation")
        )

    def helloasso_warnings(self):
        """Incohérences détectées entre la saison et la campagne HelloAsso."""
        warnings = []
        if self.end_date < timezone.localdate():
            return warnings  # saison terminée : la campagne n'a plus à être cohérente
        if self.helloasso_start and self.helloasso_end:
            start, end = timezone.localtime(self.helloasso_start).date(), timezone.localtime(self.helloasso_end).date()
            if abs((start - self.start_date).days) > 45 or abs((end - self.end_date).days) > 45:
                warnings.append(
                    f"Les dates de validité configurées sur HelloAsso ({start:%d/%m/%Y} → {end:%d/%m/%Y}) "
                    f"ne correspondent pas à la saison {self.label} ({self.start_date:%d/%m/%Y} → "
                    f"{self.end_date:%d/%m/%Y})."
                )
        if self.helloasso_state and self.helloasso_state not in {"Public"} and self.registrations_open:
            warnings.append(
                f"La campagne est à l'état « {self.helloasso_state} » sur HelloAsso : elle n'est peut-être pas "
                "accessible au public."
            )
        return warnings


class MembershipQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=Membership.Status.ACTIVE)

    def current(self):
        season = Season.current()
        return self.active().filter(season=season) if season else self.none()


class Membership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Valide"
        REFUNDED = "refunded", "Remboursée"
        CANCELLED = "cancelled", "Annulée"

    class Source(models.TextChoices):
        HELLOASSO = "helloasso", "HelloAsso"
        MANUAL = "manual", "Saisie manuelle"
        LEGACY = "legacy", "Reprise de l'ancien site"

    PAYMENT_METHODS = [
        ("card", "Carte bancaire (HelloAsso)"),
        ("cash", "Espèces"),
        ("check", "Chèque"),
        ("transfer", "Virement"),
        ("free", "Gratuit / offert"),
        ("other", "Autre"),
    ]

    person = models.ForeignKey(
        "members.Person", verbose_name="Personne", on_delete=models.PROTECT, related_name="memberships"
    )
    season = models.ForeignKey(Season, verbose_name="Saison", on_delete=models.PROTECT, related_name="memberships")
    status = models.CharField("Statut", max_length=12, choices=Status.choices, default=Status.ACTIVE)
    source = models.CharField("Origine", max_length=12, choices=Source.choices, default=Source.MANUAL)
    amount = models.DecimalField("Cotisation (€)", max_digits=8, decimal_places=2, default=0)
    donation = models.DecimalField("Don associé (€)", max_digits=8, decimal_places=2, default=0)
    payment_method = models.CharField("Moyen de paiement", max_length=12, choices=PAYMENT_METHODS, blank=True)
    tier_label = models.CharField("Formule", max_length=200, blank=True)
    joined_at = models.DateTimeField("Date d'adhésion", default=timezone.now)
    helloasso_order_id = models.BigIntegerField("Commande HelloAsso", null=True, blank=True, db_index=True)
    helloasso_item_id = models.BigIntegerField("Ligne HelloAsso", null=True, blank=True, unique=True)
    membership_card_url = models.URLField("Carte d'adhérent·e HelloAsso", max_length=500, blank=True)
    payer_name = models.CharField("Payeur·se", max_length=200, blank=True)
    payer_email = models.EmailField("E-mail du payeur·se", blank=True)
    notes = models.TextField("Notes", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Saisie par",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField("Enregistrée le", auto_now_add=True)
    updated_at = models.DateTimeField("Modifiée le", auto_now=True)

    objects = MembershipQuerySet.as_manager()

    class Meta:
        verbose_name = "Adhésion"
        ordering = ["-joined_at"]
        indexes = [models.Index(fields=["season", "status"])]

    def __str__(self):
        return f"Adhésion {self.season.label} — {self.person}"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE


class HelloAssoEvent(models.Model):
    """Notification reçue de HelloAsso (conservée pour le suivi et le débogage)."""

    class Status(models.TextChoices):
        RECEIVED = "received", "Reçue"
        PROCESSED = "processed", "Traitée"
        IGNORED = "ignored", "Ignorée"
        REJECTED = "rejected", "Rejetée"
        ERROR = "error", "Erreur"

    received_at = models.DateTimeField("Reçue le", default=timezone.now, db_index=True)
    event_type = models.CharField("Type", max_length=40, blank=True)
    order_id = models.BigIntegerField("Commande", null=True, blank=True, db_index=True)
    form_slug = models.CharField("Campagne", max_length=200, blank=True)
    payload = models.JSONField("Contenu", default=dict, blank=True)
    source_ip = models.GenericIPAddressField("IP d'origine", null=True, blank=True)
    secret_ok = models.BooleanField("URL secrète utilisée", default=False)
    verified = models.BooleanField("Confirmée via l'API HelloAsso", default=False)
    status = models.CharField("Statut", max_length=12, choices=Status.choices, default=Status.RECEIVED)
    result = models.TextField("Résultat", blank=True)

    class Meta:
        verbose_name = "Notification HelloAsso"
        verbose_name_plural = "Notifications HelloAsso"
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.event_type or 'Notification'} #{self.order_id or '?'} ({self.get_status_display()})"
