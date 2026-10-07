"""Demandes d'aide à projet et ressources, côté membres."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.audit import log_activity
from core.emails import send_templated_email
from core.models import SiteSettings
from core.permissions import has_capability
from core.threads import MessageForm, post_message, thread_for

from .forms import FundingRequestForm
from .models import ProjectFundingRequest, ResourceFile

MAX_ATTACHMENTS_BYTES = 15 * 1024 * 1024


def funding_recipients():
    return SiteSettings.load().recipients("funding")


def _request_for(request, pk):
    funding = get_object_or_404(ProjectFundingRequest.objects.select_related("asker"), pk=pk)
    if funding.asker_id != request.user.pk and not has_capability(request.user, "funding"):
        raise PermissionDenied
    return funding


@login_required
def funding_list(request):
    requests_ = ProjectFundingRequest.objects.filter(asker=request.user)
    return render(request, "dashboard/funding_list.html", {"funding_requests": requests_, "site": SiteSettings.load()})


def _attachments(funding):
    files, total = [], 0
    for _field, field_file, label in funding.files:
        try:
            with field_file.storage.open(field_file.name, "rb") as handle:
                data = handle.read()
        except OSError:
            continue
        total += len(data)
        if total > MAX_ATTACHMENTS_BYTES:
            break
        extension = field_file.name.rsplit(".", 1)[-1]
        files.append((f"{label}.{extension}", data, None))
    return files


@login_required
def funding_create(request):
    form = FundingRequestForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        funding = form.save(commit=False)
        funding.asker = request.user
        funding.save()
        sent = send_templated_email(
            "funding_new", {"funding": funding}, funding_recipients(), reply_to=[request.user.email], attachments=_attachments(funding)
        )
        if sent:
            ProjectFundingRequest.objects.filter(pk=funding.pk).update(sent_by_mail=True)
        send_templated_email("funding_received", {"funding": funding}, [request.user.email])
        log_activity(request, "funding-created", f"Nouvelle demande d'aide « {funding.name} » ({funding.funding_value} €).", target=funding, category="funding")
        messages.success(request, "Ta demande est déposée ! Elle sera étudiée lors d'une prochaine réunion du CA.")
        return redirect(funding.get_absolute_url())
    return render(request, "dashboard/funding_form.html", {"form": form, "site": SiteSettings.load()})


@login_required
def funding_detail(request, pk):
    funding = _request_for(request, pk)
    is_board = has_capability(request.user, "funding")
    return render(
        request,
        "dashboard/funding_detail.html",
        {
            "funding": funding,
            "thread": thread_for(funding, include_internal=is_board),
            "message_form": MessageForm(allow_internal=is_board),
            "is_asker": funding.asker_id == request.user.pk,
            "is_board": is_board,
        },
    )


@login_required
@require_POST
def funding_message(request, pk):
    funding = _request_for(request, pk)
    is_board = has_capability(request.user, "funding")
    form = MessageForm(request.POST, allow_internal=is_board)
    if form.is_valid():
        internal = form.cleaned_data.get("is_internal", False)
        from_board = is_board and funding.asker_id != request.user.pk
        post_message(funding, author=request.user, body=form.cleaned_data["body"], is_internal=internal, is_from_board=from_board)
        if not internal:
            recipients = [funding.asker.email] if from_board and funding.asker else funding_recipients()
            send_templated_email("funding_message", {"funding": funding, "body": form.cleaned_data["body"], "from_board": from_board}, recipients)
        form = MessageForm(allow_internal=is_board)
    return render(
        request,
        "dashboard/partials/funding_thread.html",
        {"funding": funding, "thread": thread_for(funding, include_internal=is_board), "message_form": form},
    )


@login_required
def resource_list(request):
    resources = ResourceFile.objects.order_by("category", "name")
    categories = {}
    for resource in resources:
        categories.setdefault(resource.category or "Divers", []).append(resource)
    return render(request, "dashboard/resource_list.html", {"categories": categories, "count": len(resources)})
