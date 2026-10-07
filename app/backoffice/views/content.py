"""Contenus du site : paramètres généraux, accès aux contenus éditables."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.audit import log_activity
from core.models import FAQEntry, Page, Service, SiteSettings, TeamMember, TimelineEntry
from core.permissions import capability_required, has_capability
from memberships.models import Season

from ..forms import SETTINGS_SECTIONS, settings_form_class


@capability_required("content")
def content_hub(request):
    season = Season.current()
    cards = [
        {"url": "backoffice:settings", "icon": "settings", "title": "Paramètres du site", "text": "Textes de l'accueil, contacts, réseaux, annonce, magasin, contrat, notifications…"},
        {"url": "backoffice:team", "icon": "users", "title": "Équipe (CA)", "text": f"{TeamMember.objects.filter(season=season).count() if season else 0} personne(s) pour la saison {season.label if season else ''}."},
        {"url": "backoffice:timeline", "icon": "history", "title": "Historique", "text": f"{TimelineEntry.objects.count()} étapes dans le carnet de bord."},
        {"url": "backoffice:services", "icon": "sparkles", "title": "Services", "text": f"{Service.objects.count()} cartes « Ce qu'on fait ensemble »."},
        {"url": "backoffice:pages", "icon": "file-text", "title": "Pages", "text": f"{Page.objects.count()} pages, dont {Page.objects.filter(needs_review=True).count()} à relire."},
        {"url": "backoffice:faq", "icon": "circle-help", "title": "Questions fréquentes", "text": f"{FAQEntry.objects.count()} questions."},
        {"url": "backoffice:seasons", "icon": "calendar-range", "title": "Saisons & HelloAsso", "text": "Campagne d'adhésion, saison en cours, tarif."},
    ]
    return render(request, "backoffice/content/hub.html", {"cards": cards})


@capability_required("content")
def site_settings(request, section=None):
    site = SiteSettings.load()
    sections = [s for s in SETTINGS_SECTIONS if has_capability(request.user, s.get("capability", "content"))]
    current = next((s for s in sections if s["key"] == section), sections[0])
    if section and current["key"] != section:
        raise PermissionDenied
    form_class = settings_form_class(current)
    form = form_class(request.POST or None, request.FILES or None, instance=site)
    if request.method == "POST" and form.is_valid():
        changed = form.changed_data
        form.save()
        SiteSettings.objects.filter(pk=1).update(updated_by=request.user)
        SiteSettings.load()  # rafraîchit le cache
        log_activity(request, "settings-updated", f"Paramètres « {current['label']} » modifiés.", category="content", data={"champs": changed})
        messages.success(request, "Paramètres enregistrés : le site est à jour.")
        return redirect("backoffice:settings-section", section=current["key"])
    return render(
        request,
        "backoffice/content/settings.html",
        {"form": form, "sections": sections, "current": current, "site_obj": site},
    )


@capability_required("content")
@require_POST
def team_copy(request):
    """Copie l'équipe de la saison précédente vers la saison en cours (point de départ)."""
    season = Season.current()
    previous = Season.objects.filter(start_date__lt=season.start_date).order_by("-start_date").first() if season else None
    if not (season and previous):
        messages.error(request, "Aucune saison précédente à copier.")
        return redirect("backoffice:team")
    if TeamMember.objects.filter(season=season).exists():
        messages.error(request, f"L'équipe {season.label} contient déjà des personnes.")
        return redirect("backoffice:team")
    count = 0
    for member in TeamMember.objects.filter(season=previous):
        member.pk = None
        member.season = season
        member.save()
        count += 1
    log_activity(request, "team-copied", f"Équipe {previous.label} copiée vers {season.label} ({count} personnes).", category="content")
    messages.success(request, f"{count} personne(s) copiée(s) : mets à jour les fonctions et retire les sortant·es.")
    return redirect(f"/espace-ca/contenus/equipe/?saison={season.label}")
