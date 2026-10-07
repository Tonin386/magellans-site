"""Pages publiques : accueil, films, adhésion, pages de contenu."""

from collections import Counter

from django.contrib import messages
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from core.antispam import rate_limited
from core.audit import log_activity
from core.emails import send_templated_email
from core.models import FAQEntry, Page, Service, SiteSettings, TeamMember, TimelineEntry
from core.permissions import has_capability
from dashboard.models import Project, RoleMap
from members.models import Person
from memberships.models import Season
from warehouse.models import Item

from .forms import ContactForm


def team_for_display():
    """Équipe de la saison en cours, ou à défaut celle de la saison la plus récente."""
    visible = TeamMember.objects.filter(is_visible=True).select_related("season")
    season = Season.current()
    if season and visible.filter(season=season).exists():
        return season, list(visible.filter(season=season))
    latest = visible.exclude(season=None).order_by("-season__start_date").first()
    if latest:
        return latest.season, list(visible.filter(season=latest.season))
    return None, list(visible.filter(season=None))


def home(request):
    site = SiteSettings.load()
    team_season, team = team_for_display()
    projects = list(
        Project.objects.filter(public=True).order_by("-featured", "-release_date", "-pk")[:8]
    )
    stats = {
        "years": max(1, timezone.localdate().year - site.founded_year),
        "films": Project.objects.filter(public=True).count(),
        "items": Item.objects.filter(is_archived=False).count(),
        "members": Person.objects.filter(memberships__status="active").distinct().count(),
    }
    return render(
        request,
        "showcase/home.html",
        {
            "projects": projects,
            "services": Service.objects.filter(is_visible=True),
            "timeline": TimelineEntry.objects.filter(is_visible=True),
            "team": team,
            "team_season": team_season,
            "stats": stats,
            "form": ContactForm(),
        },
    )


@require_http_methods(["POST"])
def contact(request):
    form = ContactForm(request.POST)
    if rate_limited(request, "contact", limit=5, period=3600):
        form.add_error(None, "Trop de messages envoyés depuis ta connexion. Réessaie dans une heure.")
    elif form.is_valid():
        site = SiteSettings.load()
        data = form.cleaned_data
        sent = send_templated_email(
            "contact_message",
            {"data": data, "subject_label": dict(form.fields["subject"].choices)[data["subject"]]},
            site.recipients("contact"),
            reply_to=[data["email"]],
        )
        log_activity(request, "contact", f"Message de contact reçu de {data['name']} ({data['email']}).", category="system")
        if sent:
            return render(request, "showcase/partials/contact_success.html", {"name": data["name"]})
        form.add_error(None, "Le message n'a pas pu être envoyé. Écris-nous directement par e-mail, désolé !")
    template = "showcase/partials/contact_form.html" if request.htmx else "showcase/contact_page.html"
    return render(request, template, {"form": form}, status=422 if request.htmx else 200)


def films(request):
    projects = Project.objects.filter(public=True).order_by("-release_date", "-pk")
    # Un filtre par genre, même saisi de plusieurs façons (« Court métrage », « Court-métrage »…).
    spellings = Counter(p.genre.strip() for p in projects if p.genre and p.genre != "Non-spécifié")
    by_slug = {}
    for genre, _count in spellings.most_common():
        by_slug.setdefault(slugify(genre), genre)
    genres = sorted(by_slug.values(), key=str.lower)
    return render(request, "showcase/films.html", {"projects": projects, "genres": genres})


def film_detail(request, slug):
    project = get_object_or_404(Project.objects.select_related("director"), slug=slug)
    if not project.public and not has_capability(request.user, "projects"):
        raise Http404
    credits = RoleMap.objects.filter(project=project).select_related("person")
    others = Project.objects.filter(public=True).exclude(pk=project.pk).order_by("-release_date")[:4]
    return render(
        request,
        "showcase/film_detail.html",
        {"project": project, "credits": credits, "others": others},
    )


def join(request):
    season = Season.current()
    membership = None
    if request.user.is_authenticated and getattr(request.user, "person", None):
        membership = request.user.person.membership_for(season)
    return render(
        request,
        "showcase/join.html",
        {
            "season": season,
            "membership": membership,
            "faq": FAQEntry.objects.filter(is_visible=True, topic="membership"),
        },
    )


def page(request, slug):
    page_obj = get_object_or_404(Page, slug=slug)
    if not page_obj.is_published and not has_capability(request.user, "content"):
        raise Http404
    return render(request, "showcase/page.html", {"page": page_obj})


def legacy_project_redirect(request, slug):
    return redirect("film-detail", slug=slug, permanent=True)
