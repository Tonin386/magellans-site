"""Projets (catalogue de films) et demandes d'aide."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.audit import log_activity
from core.emails import send_templated_email
from core.http import smart_redirect
from core.permissions import capability_required, has_capability
from core.threads import MessageForm, thread_for
from dashboard.models import FundingStatus, Project, ProjectFundingRequest, RoleMap

from ..forms import CreditForm, FundingDecisionForm, ProjectForm
from ..tables import table


@capability_required("projects")
def projects(request):
    queryset = Project.objects.select_related("director")
    visibility = request.GET.get("visibilite", "")
    if visibility == "publics":
        queryset = queryset.filter(public=True)
    elif visibility == "prives":
        queryset = queryset.filter(public=False)
    context = table(
        request,
        queryset,
        search_fields=["name", "genre", "desc", "director__first_name", "director__last_name"],
        sorts={"nom": "name", "sortie": "release_date", "tournage": "shoot_date"},
        default_sort="-sortie",
        per_page=40,
    )
    context["visibility"] = visibility
    if request.htmx and request.htmx.target == "table":
        return render(request, "backoffice/projects/partials/table.html", context)
    return render(request, "backoffice/projects/list.html", context)


@capability_required("projects")
def project_form(request, pk=None):
    project = get_object_or_404(Project, pk=pk) if pk else None
    form = ProjectForm(request.POST or None, request.FILES or None, instance=project)
    if request.method == "POST" and form.is_valid():
        project = form.save()
        log_activity(request, "project-saved", f"Projet « {project.name} » {'modifié' if pk else 'créé'}.", target=project, category="projects", data={"champs": form.changed_data})
        messages.success(request, f"Projet « {project.name} » enregistré.")
        return redirect("backoffice:project-edit", pk=project.pk)
    credits = RoleMap.objects.filter(project=project).select_related("person") if project else []
    return render(
        request,
        "backoffice/projects/form.html",
        {"form": form, "project": project, "credits": credits, "credit_form": CreditForm(prefix="credit")},
    )


@capability_required("projects")
@require_POST
def project_credit_add(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = CreditForm(request.POST, prefix="credit")
    if form.is_valid():
        credit = form.save(commit=False)
        credit.project = project
        credit.order = RoleMap.objects.filter(project=project).count()
        if RoleMap.objects.filter(project=project, person=credit.person, role_name=credit.role_name).exists():
            messages.error(request, "Cette personne a déjà ce poste sur le projet.")
        else:
            credit.save()
            messages.success(request, f"{credit.person.display_name} ajouté·e au générique.")
    else:
        messages.error(request, "Choisis une personne et un poste.")
    return render(
        request,
        "backoffice/projects/partials/credits.html",
        {"project": project, "credits": RoleMap.objects.filter(project=project).select_related("person"), "credit_form": CreditForm(prefix="credit")},
    )


@capability_required("projects")
@require_POST
def project_credit_delete(request, pk, credit_pk):
    project = get_object_or_404(Project, pk=pk)
    RoleMap.objects.filter(project=project, pk=credit_pk).delete()
    return render(
        request,
        "backoffice/projects/partials/credits.html",
        {"project": project, "credits": RoleMap.objects.filter(project=project).select_related("person"), "credit_form": CreditForm(prefix="credit")},
    )


@capability_required("projects")
@require_POST
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.invoices.exists():
        messages.error(request, "Des notes de frais sont rattachées à ce projet : rends-le privé plutôt que de le supprimer.")
        return smart_redirect(request, "backoffice:project-edit", pk=project.pk)
    name = project.name
    project.delete()
    log_activity(request, "project-deleted", f"Projet « {name} » supprimé.", category="projects")
    messages.success(request, f"Projet « {name} » supprimé.")
    return smart_redirect(request, "backoffice:projects")


# ------------------------------------------------------------- Demandes d'aide
@capability_required("funding")
def funding(request):
    queryset = ProjectFundingRequest.objects.select_related("asker", "asker__site_person")
    status = request.GET.get("statut", "todo")
    if status == "todo":
        queryset = queryset.filter(status__in=[FundingStatus.SUBMITTED, FundingStatus.REVIEWING])
    elif status in FundingStatus.values:
        queryset = queryset.filter(status=status)
    context = table(
        request,
        queryset,
        search_fields=["name", "directors", "production", "asker__email", "asker__site_person__last_name"],
        sorts={"date": "deposit_date", "montant": "funding_value"},
        default_sort="-date",
        per_page=40,
    )
    context.update({"status": status, "statuses": FundingStatus.choices})
    if request.htmx and request.htmx.target == "table":
        return render(request, "backoffice/projects/partials/funding_table.html", context)
    return render(request, "backoffice/projects/funding.html", context)


@capability_required("funding")
def funding_manage(request, pk):
    funding_request = get_object_or_404(ProjectFundingRequest.objects.select_related("asker"), pk=pk)
    can_decide = has_capability(request.user, "funding_decide")
    form = FundingDecisionForm(request.POST or None, instance=funding_request, prefix="decision")
    if request.method == "POST" and can_decide and form.is_valid():
        previous = ProjectFundingRequest.objects.get(pk=funding_request.pk).get_status_display()
        funding_request = form.save(commit=False)
        funding_request.decided_at = timezone.now()
        funding_request.decided_by = request.user
        funding_request.save()
        if form.cleaned_data["notify"] and funding_request.asker:
            send_templated_email("funding_decision", {"funding": funding_request}, [funding_request.asker.email])
        log_activity(
            request,
            "funding-decision",
            f"Demande d'aide « {funding_request.name} » : {previous} → {funding_request.get_status_display()}.",
            target=funding_request,
            category="funding",
        )
        messages.success(request, "Décision enregistrée.")
        return redirect("backoffice:funding-detail", pk=funding_request.pk)
    return render(
        request,
        "backoffice/projects/funding_manage.html",
        {
            "funding": funding_request,
            "form": form,
            "can_decide": can_decide,
            "thread": thread_for(funding_request, include_internal=True),
            "message_form": MessageForm(allow_internal=True),
        },
    )
