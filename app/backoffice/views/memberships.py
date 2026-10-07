"""Adhésions et saisons."""

import datetime

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.audit import log_activity
from core.http import smart_redirect
from core.permissions import capability_required
from members.models import Person
from memberships.helloasso import HelloAssoClient, HelloAssoError
from memberships.models import HelloAssoEvent, Membership, Season
from memberships.services import ensure_account, manual_membership, refresh_season_from_helloasso, sync_season

from ..forms import ManualMembershipForm, MembershipEditForm, SeasonForm
from ..tables import csv_response, table


def _selected_season(request):
    label = request.GET.get("saison")
    if label:
        season = Season.objects.filter(label=label).first()
        if season:
            return season
    return Season.current() or Season.objects.first()


@capability_required("memberships")
def memberships(request):
    season = _selected_season(request)
    queryset = Membership.objects.select_related("person", "person__site_profile", "season")
    if season:
        queryset = queryset.filter(season=season)
    status = request.GET.get("statut", "active")
    if status:
        queryset = queryset.filter(status=status)
    source = request.GET.get("origine", "")
    if source:
        queryset = queryset.filter(source=source)
    context = table(
        request,
        queryset,
        search_fields=["person__first_name", "person__last_name", "person__email", "payer_email", "payer_name"],
        sorts={"nom": ["person__last_name", "person__first_name"], "date": "joined_at", "montant": "amount"},
        default_sort="-date",
        per_page=50,
    )
    context.update(
        {
            "season": season,
            "seasons": Season.objects.all(),
            "stats": season.stats() if season else None,
            "status": status,
            "source": source,
            "statuses": Membership.Status.choices,
            "sources": Membership.Source.choices,
            "api_configured": HelloAssoClient().configured,
        }
    )
    if request.htmx and request.htmx.target == "table":
        return render(request, "backoffice/memberships/partials/table.html", context)
    return render(request, "backoffice/memberships/list.html", context)


@capability_required("memberships")
def memberships_export(request):
    season = _selected_season(request)
    rows = (
        Membership.objects.active()
        .filter(season=season)
        .select_related("person")
        .order_by("person__last_name", "person__first_name")
    )
    return csv_response(
        f"adhesions-{season.label if season else 'toutes'}.csv",
        ["Nom", "Prénom", "E-mail", "Téléphone", "Date d'adhésion", "Cotisation (€)", "Don (€)", "Origine", "Moyen de paiement"],
        [
            [
                m.person.clean_last_name,
                m.person.clean_first_name,
                m.person.email or "",
                m.person.phone_display,
                timezone.localtime(m.joined_at).strftime("%d/%m/%Y"),
                f"{m.amount:.2f}".replace(".", ","),
                f"{m.donation:.2f}".replace(".", ","),
                m.get_source_display(),
                m.get_payment_method_display() if m.payment_method else "",
            ]
            for m in rows
        ],
    )


@capability_required("memberships")
def membership_create(request):
    form = ManualMembershipForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            person = data["person"]
            if person is None:
                person = Person.objects.create(
                    first_name=data["new_first_name"],
                    last_name=data["new_last_name"],
                    email=data["new_email"] or None,
                    phone=data["new_phone"],
                    role="X",
                )
            joined_at = (
                timezone.make_aware(datetime.datetime.combine(data["joined_at"], datetime.time(12, 0)))
                if data.get("joined_at")
                else None
            )
            membership = manual_membership(
                person,
                data["season"],
                amount=data["amount"],
                payment_method=data["payment_method"],
                joined_at=joined_at,
                notes=data["notes"],
                created_by=request.user,
                request=request,
            )
        messages.success(request, f"Adhésion {membership.season.label} enregistrée pour {person.display_name}.")
        return redirect(f"{reverse('backoffice:memberships')}?saison={membership.season.label}")
    return render(request, "backoffice/memberships/create.html", {"form": form})


@capability_required("memberships")
def membership_edit(request, pk):
    membership = get_object_or_404(Membership.objects.select_related("person", "season"), pk=pk)
    form = MembershipEditForm(request.POST or None, instance=membership)
    if request.method == "POST" and form.is_valid():
        form.save()
        log_activity(request, "membership-updated", f"Adhésion {membership.season.label} de {membership.person.display_name} modifiée.", target=membership, category="memberships", data={"champs": form.changed_data})
        messages.success(request, "Adhésion mise à jour.")
        return redirect(f"{reverse('backoffice:memberships')}?saison={membership.season.label}")
    return render(request, "backoffice/memberships/edit.html", {"form": form, "membership": membership})


@capability_required("memberships")
@require_POST
def membership_invite(request, pk):
    membership = get_object_or_404(Membership.objects.select_related("person", "season"), pk=pk)
    account = ensure_account(membership.person, membership, send_emails=True)
    if account or membership.person.site_profile_id:
        messages.success(request, f"E-mail envoyé à {membership.person.display_name}.")
    else:
        messages.error(request, "Impossible d'inviter cette personne : adresse e-mail manquante ou déjà utilisée par un autre compte.")
    return smart_redirect(request, f"{reverse('backoffice:memberships')}?saison={membership.season.label}")


# ---------------------------------------------------------------------- Saisons
@capability_required("memberships")
def seasons(request):
    items = list(Season.objects.all())
    for season in items:
        season.stat = season.stats()
    return render(request, "backoffice/memberships/seasons.html", {"seasons": items})


@capability_required("memberships")
def season_form(request, pk=None):
    season = get_object_or_404(Season, pk=pk) if pk else None
    initial = {}
    if season is None:
        latest = Season.objects.first()
        if latest:
            year = latest.end_date.year
            label = f"{year}-{year + 1}"
            start, end = Season.guess_dates(label)
            initial = {"label": label, "start_date": start, "end_date": end, "price": latest.price, "pitch": latest.pitch}
    form = SeasonForm(request.POST or None, instance=season, initial=initial)
    if request.method == "POST" and form.is_valid():
        season = form.save()
        if season.has_helloasso and HelloAssoClient().configured:
            try:
                refresh_season_from_helloasso(season)
                season.save()
            except HelloAssoError as error:
                messages.warning(request, f"Saison enregistrée, mais HelloAsso n'a pas pu être consulté : {error}")
        log_activity(request, "season-saved", f"Saison {season.label} enregistrée.", target=season, category="memberships", data={"champs": form.changed_data})
        messages.success(request, f"Saison {season.label} enregistrée.")
        for warning in season.helloasso_warnings():
            messages.warning(request, warning)
        return redirect("backoffice:seasons")
    return render(request, "backoffice/memberships/season_form.html", {"form": form, "season": season})


@capability_required("memberships")
@require_POST
def season_activate(request, pk):
    season = get_object_or_404(Season, pk=pk)
    season.is_current = True
    season.save()
    log_activity(request, "season-activated", f"La saison {season.label} devient la saison en cours.", target=season, category="memberships")
    messages.success(request, f"La saison {season.label} est maintenant la saison en cours sur tout le site.")
    return smart_redirect(request, "backoffice:seasons")


@capability_required("memberships")
@require_POST
def season_sync(request, pk):
    season = get_object_or_404(Season, pk=pk)
    try:
        report = sync_season(season, send_emails=request.POST.get("invite") == "1", request=request)
    except HelloAssoError as error:
        messages.error(request, f"Synchronisation impossible : {error}")
    else:
        messages.success(request, f"Synchronisation {season.label} terminée : {report.summary()}.")
        for warning in season.helloasso_warnings():
            messages.warning(request, warning)
    return smart_redirect(request, f"{reverse('backoffice:memberships')}?saison={season.label}")


@capability_required("memberships")
def helloasso(request):
    conf = settings.HELLOASSO
    secret = conf.get("WEBHOOK_SECRET")
    context = {
        "events": HelloAssoEvent.objects.all()[:50],
        "api_configured": HelloAssoClient().configured,
        "secret_configured": bool(secret),
        "legacy_url": settings.SITE_URL + reverse("api:helloasso"),
        "secret_url": settings.SITE_URL + reverse("api:helloasso-secret", kwargs={"secret": secret}) if secret else "",
        "can_see_secret": request.user.is_superuser or "W" in getattr(request.user.person, "board_roles", []) or "P" in getattr(request.user.person, "board_roles", []),
        "season": Season.current(),
    }
    return render(request, "backoffice/memberships/helloasso.html", context)
