"""Fiches personnes (adhérent·es, inscrit·es, externes, organisations) et rôles du CA."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from bank.models import Invoice, Operation
from core.audit import log_activity
from core.http import smart_redirect
from core.models import TeamMember
from core.permissions import BOARD_ROLE_LABELS, capability_required, has_capability
from dashboard.models import Project, RoleMap
from members.auth_views import send_activation_email, send_invitation_email
from members.models import Member, Person
from memberships.models import Membership, Season
from warehouse.models import Order

from ..forms import BoardRolesForm, LinkAccountForm, PersonForm
from ..tables import csv_response, table

FILTERS = [
    ("", "Tout le monde"),
    ("adherents", "Adhérent·es à jour"),
    ("ca", "Membres du CA"),
    ("inscrits", "Inscrit·es sans adhésion"),
    ("externes", "Externes"),
    ("organisations", "Organisations"),
    ("sans-compte", "Adhérent·es sans compte"),
]


def _people_queryset(request):
    season = Season.current()
    current = Membership.objects.filter(person=OuterRef("pk"), season=season, status="active")
    queryset = Person.objects.select_related("site_profile").annotate(is_member=Exists(current))
    flt = request.GET.get("filtre", "")
    if flt == "adherents":
        queryset = queryset.filter(is_member=True)
    elif flt == "ca":
        queryset = queryset.exclude(board_roles=[])
    elif flt == "inscrits":
        queryset = queryset.filter(site_profile__isnull=False, is_member=False)
    elif flt == "externes":
        queryset = queryset.filter(site_profile__isnull=True, is_member=False, kind=Person.Kind.INDIVIDUAL)
    elif flt == "organisations":
        queryset = queryset.filter(kind=Person.Kind.ORGANISATION)
    elif flt == "sans-compte":
        queryset = queryset.filter(is_member=True, site_profile__isnull=True)
    return queryset, flt


@capability_required("people")
def people(request):
    queryset, flt = _people_queryset(request)
    context = table(
        request,
        queryset,
        search_fields=["first_name", "last_name", "email", "phone", "organisation_name", "site_profile__email"],
        sorts={"nom": ["last_name", "first_name"], "creation": "created_at"},
        default_sort="nom",
        per_page=40,
    )
    context.update({"filters": FILTERS, "filter": flt, "season": Season.current()})
    if request.htmx and request.htmx.target == "table":
        return render(request, "backoffice/people/partials/table.html", context)
    return render(request, "backoffice/people/list.html", context)


@capability_required("people")
def people_export(request):
    queryset, flt = _people_queryset(request)
    return csv_response(
        f"personnes{'-' + flt if flt else ''}.csv",
        ["Nom", "Prénom", "Organisation", "E-mail", "Téléphone", "Adhérent·e saison en cours", "Rôles CA", "Compte du site"],
        [
            [
                p.clean_last_name,
                p.clean_first_name,
                p.organisation_name,
                p.email or (p.site_profile.email if p.site_profile else ""),
                p.phone_display,
                "oui" if p.is_member else "non",
                ", ".join(p.board_role_labels),
                "oui" if p.site_profile_id else "non",
            ]
            for p in queryset.order_by("last_name", "first_name")
        ],
    )


@capability_required("people")
def person_detail(request, pk):
    person = get_object_or_404(Person.objects.select_related("site_profile"), pk=pk)
    form = PersonForm(request.POST or None, instance=person, prefix="person")
    if request.method == "POST" and request.POST.get("action") == "save" and form.is_valid():
        form.save()
        log_activity(request, "person-updated", f"Fiche de {person.display_name} modifiée.", target=person, category="people", data={"champs": form.changed_data})
        messages.success(request, "Fiche mise à jour.")
        return redirect("backoffice:person-detail", pk=person.pk)
    account = person.site_profile
    context = {
        "person": person,
        "form": form,
        "roles_form": BoardRolesForm(initial={"roles": person.board_roles}),
        "link_form": LinkAccountForm(),
        "memberships": person.memberships.select_related("season").order_by("-season__start_date"),
        "orders": Order.objects.filter(user=account).exclude(status=0).order_by("-date_start")[:20] if account else [],
        "invoices": Invoice.objects.filter(author=account).order_by("-date_created")[:20] if account else [],
        "operations": Operation.objects.filter(third_party=person).order_by("-date")[:30] if has_capability(request.user, "finance") else None,
        "credits": RoleMap.objects.filter(person=person).select_related("project"),
        "directed": Project.objects.filter(director=person),
        "can_edit_roles": has_capability(request.user, "roles"),
    }
    return render(request, "backoffice/people/detail.html", context)


@capability_required("people")
def person_create(request):
    form = PersonForm(request.POST or None, prefix="person")
    if request.method == "POST" and form.is_valid():
        person = form.save(commit=False)
        person.role = "O" if person.kind == Person.Kind.ORGANISATION else "X"
        person.save()
        log_activity(request, "person-created", f"Fiche créée : {person.display_name}.", target=person, category="people")
        messages.success(request, f"Fiche de {person.display_name} créée.")
        if request.GET.get("next") == "operation":
            return redirect("backoffice:operation-create")
        return redirect("backoffice:person-detail", pk=person.pk)
    return render(request, "backoffice/people/create.html", {"form": form})


@capability_required("roles")
@require_POST
def person_roles(request, pk):
    person = get_object_or_404(Person, pk=pk)
    form = BoardRolesForm(request.POST)
    if form.is_valid():
        before = set(person.board_roles or [])
        after = set(form.cleaned_data["roles"])
        if person.site_profile_id is None and after:
            messages.error(request, "Les rôles du CA nécessitent un compte sur le site : invite d'abord cette personne.")
            return redirect("backoffice:person-detail", pk=person.pk)
        if person.site_profile_id == request.user.pk and not request.user.is_superuser and not (after & {"P", "V", "W"}):
            messages.error(request, "Tu ne peux pas retirer tes propres droits de gestion des rôles.")
            return redirect("backoffice:person-detail", pk=person.pk)
        person.board_roles = sorted(after)
        person.save()
        added = ", ".join(BOARD_ROLE_LABELS[r] for r in sorted(after - before)) or "aucun"
        removed = ", ".join(BOARD_ROLE_LABELS[r] for r in sorted(before - after)) or "aucun"
        log_activity(request, "roles-updated", f"Rôles CA de {person.display_name} : ajoutés {added}, retirés {removed}.", target=person, category="people")
        messages.success(request, "Rôles mis à jour.")
    return redirect("backoffice:person-detail", pk=person.pk)


@capability_required("people")
@require_POST
def person_invite(request, pk):
    person = get_object_or_404(Person.objects.select_related("site_profile"), pk=pk)
    account = person.site_profile
    if account is None:
        if not person.email:
            messages.error(request, "Ajoute d'abord une adresse e-mail à cette fiche.")
            return smart_redirect(request, "backoffice:person-detail", pk=person.pk)
        if Member.objects.filter(email__iexact=person.email).exists():
            messages.error(request, "Un compte existe déjà avec cette adresse : utilise « Associer à un compte ».")
            return smart_redirect(request, "backoffice:person-detail", pk=person.pk)
        account = Member.objects.create_user(person.email, None, is_active=False, person=person)
    if account.is_active and account.has_usable_password():
        messages.info(request, "Cette personne a déjà un compte actif.")
    elif account.has_usable_password():
        send_activation_email(account)
        messages.success(request, f"Lien d'activation renvoyé à {account.email}.")
    else:
        send_invitation_email(account, person.current_membership)
        messages.success(request, f"Invitation envoyée à {account.email}.")
    log_activity(request, "person-invited", f"Invitation envoyée à {person.display_name}.", target=person, category="people")
    return smart_redirect(request, "backoffice:person-detail", pk=person.pk)


@transaction.atomic
def merge_people(source, target):
    """Rattache tout ce qui concerne ``source`` à ``target`` puis supprime le doublon."""
    Operation.objects.filter(third_party=source).update(third_party=target)
    Project.objects.filter(director=source).update(director=target)
    Project.objects.filter(money_handler=source).update(money_handler=target)
    for credit in RoleMap.objects.filter(person=source):
        if RoleMap.objects.filter(person=target, project=credit.project, role_name=credit.role_name).exists():
            credit.delete()
        else:
            credit.person = target
            credit.save(update_fields=["person"])
    Membership.objects.filter(person=source).update(person=target)
    TeamMember.objects.filter(person=source).update(person=target)
    for field in ("first_name", "last_name", "phone", "gender", "organisation_name"):
        if not getattr(target, field) and getattr(source, field):
            setattr(target, field, getattr(source, field))
    target.board_roles = sorted(set(target.board_roles or []) | set(source.board_roles or []))
    if source.additional_notes:
        target.additional_notes = "\n".join(filter(None, [target.additional_notes, source.additional_notes]))
    target.save()
    source.delete()


@capability_required("people")
@require_POST
def person_link_account(request, pk):
    person = get_object_or_404(Person, pk=pk)
    form = LinkAccountForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Choisis un compte.")
        return redirect("backoffice:person-detail", pk=person.pk)
    account = form.cleaned_data["account"]
    target = account.person
    if person.site_profile_id:
        raise PermissionDenied("Cette fiche est déjà liée à un compte.")
    if target is None:
        person.site_profile = account
        person.save()
        messages.success(request, "Fiche associée au compte.")
        return redirect("backoffice:person-detail", pk=person.pk)
    if target.pk == person.pk:
        return redirect("backoffice:person-detail", pk=person.pk)
    summary = f"{person.display_name} (fiche #{person.pk}) fusionnée dans {target.display_name} (fiche #{target.pk})"
    snapshot = {"email": person.email, "telephone": person.phone, "notes": person.additional_notes}
    merge_people(person, target)
    log_activity(request, "people-merged", summary + ".", target=target, category="people", data=snapshot)
    messages.success(request, summary + ".")
    return redirect("backoffice:person-detail", pk=target.pk)
