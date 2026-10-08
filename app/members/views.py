"""Espace membre : tableau de bord, profil, annuaire, données personnelles."""

import json

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from bank.models import Invoice
from core.audit import log_activity
from core.emails import send_templated_email
from core.models import SiteSettings
from core.permissions import has_capability
from dashboard.models import ProjectFundingRequest
from memberships.models import Membership, Season
from warehouse.models import OPEN_STATUSES, Order, OrderStatus

from .forms import AccountDeletionForm, ProfileForm, StyledPasswordChangeForm
from .models import Member, Person


def ensure_person(user):
    person = user.person
    if person is None:
        person = Person.objects.create(site_profile=user, email=user.email, role="E")
    return person


@login_required
def home(request):
    person = ensure_person(request.user)
    season = Season.current()
    orders = list(
        Order.objects.filter(user=request.user, status__in=OPEN_STATUSES)
        .select_related("contract")
        .prefetch_related("lines__item")
        .order_by("date_start")
    )
    context = {
        "person": person,
        "season": season,
        "membership": person.membership_for(season),
        "memberships": person.memberships.select_related("season").order_by("-season__start_date")[:6],
        "orders": orders,
        "orders_to_sign": [order for order in orders if order.needs_contract],
        "draft": Order.objects.filter(user=request.user, status=OrderStatus.DRAFT).prefetch_related("lines").first(),
        "invoices": Invoice.objects.filter(author=request.user).prefetch_related("expense_set")[:5],
        "funding_requests": ProjectFundingRequest.objects.filter(asker=request.user)[:3],
    }
    if has_capability(request.user, "backoffice"):
        context["board_todo"] = {
            "orders": Order.objects.filter(status=OrderStatus.PENDING).count(),
            "invoices": Invoice.objects.filter(status__in=["V", "F"]).count(),
            "funding": ProjectFundingRequest.objects.filter(status__in=["submitted", "reviewing"]).count(),
        }
    return render(request, "members/home.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    person = ensure_person(request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=person)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ton profil est à jour.")
        return redirect("members:profile")
    return render(request, "members/profile.html", {"form": form, "person": person, "season": Season.current()})


class MemberPasswordChangeView(PasswordChangeView):
    form_class = StyledPasswordChangeForm
    template_name = "members/password_change.html"
    success_url = reverse_lazy("members:profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, "Ton mot de passe a bien été modifié.")
        return response


member_password_change = login_required(MemberPasswordChangeView.as_view())


@login_required
def directory(request):
    """Annuaire des membres (réservé aux adhérent·es à jour et au CA)."""
    person = ensure_person(request.user)
    allowed = person.is_current_member or has_capability(request.user, "backoffice")
    people = Person.objects.none()
    query = (request.GET.get("q") or "").strip()
    skill = (request.GET.get("competence") or "").strip()
    if allowed:
        people = Person.objects.in_directory().order_by("first_name", "last_name")
        if query:
            people = people.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(bio__icontains=query)
            )
        if skill:
            people = [p for p in people if skill in (p.skills or [])]
    all_skills = sorted(
        {s for skills in Person.objects.in_directory().values_list("skills", flat=True) for s in (skills or [])}
    ) if allowed else []
    template = "members/partials/directory_results.html" if request.htmx else "members/directory.html"
    return render(
        request,
        template,
        {
            "people": people,
            "allowed": allowed,
            "query": query,
            "skill": skill,
            "all_skills": all_skills,
            "me": person,
            "season": Season.current(),
        },
    )


@login_required
def export_data(request):
    """Export des données personnelles (droit à la portabilité, RGPD)."""
    person = ensure_person(request.user)
    data = {
        "export": timezone.now().isoformat(),
        "compte": {"email": request.user.email, "inscription": request.user.date_joined.isoformat()},
        "profil": {
            "prenom": person.first_name,
            "nom": person.last_name,
            "telephone": person.phone,
            "genre": person.get_gender_display() if person.gender else None,
            "presentation": person.bio,
            "competences": person.skills,
            "portfolio": person.portfolio_url,
            "instagram": person.instagram_url,
            "annuaire": person.show_in_directory,
        },
        "adhesions": [
            {"saison": m.season.label, "statut": m.get_status_display(), "date": m.joined_at.isoformat(), "montant": str(m.amount)}
            for m in person.memberships.select_related("season")
        ],
        "reservations": [
            {
                "numero": order.pk,
                "statut": order.get_status_display(),
                "debut": order.date_start.isoformat() if order.date_start else None,
                "fin": order.date_end.isoformat() if order.date_end else None,
                "projet": order.project_name,
                "materiel": [f"{line.quantity} × {line.item.name}" for line in order.lines.all()],
            }
            for order in Order.objects.filter(user=request.user).prefetch_related("lines__item")
        ],
        "notes_de_frais": [
            {"intitule": inv.title, "statut": inv.get_status_display(), "date": inv.date_created.isoformat(), "total": str(inv.total_amount)}
            for inv in Invoice.objects.filter(author=request.user)
        ],
        "demandes_aide": [
            {"projet": fr.name, "montant": fr.funding_value, "statut": fr.get_status_display(), "date": fr.deposit_date.isoformat()}
            for fr in ProjectFundingRequest.objects.filter(asker=request.user)
        ],
    }
    response = HttpResponse(json.dumps(data, ensure_ascii=False, indent=2), content_type="application/json; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="mes-donnees-magellans.json"'
    return response


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request):
    """Demande de suppression du compte : traitée par le CA (obligations comptables)."""
    form = AccountDeletionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        site = SiteSettings.load()
        send_templated_email(
            "account_deletion_request",
            {"member": request.user, "reason": form.cleaned_data["reason"]},
            site.recipients("contact"),
            reply_to=[request.user.email],
        )
        log_activity(request, "deletion-request", f"Demande de suppression de compte : {request.user}.", target=request.user.person, category="account")
        messages.success(request, "Ta demande a été transmise au CA, qui reviendra vers toi par e-mail.")
        return redirect("members:profile")
    return render(request, "members/delete_account.html", {"form": form})


# --- Anciennes adresses ---------------------------------------------------------
def legacy_member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if not has_capability(request.user, "people"):
        raise PermissionDenied
    return redirect("backoffice:person-detail", pk=ensure_person(member).pk)


def legacy_person_detail(request, pk):
    if not has_capability(request.user, "people"):
        raise PermissionDenied
    return redirect("backoffice:person-detail", pk=pk)
