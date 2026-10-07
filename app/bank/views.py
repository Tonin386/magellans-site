"""Notes de frais côté membres : dépôt, suivi, échanges avec la trésorerie."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.audit import log_activity
from core.emails import send_templated_email
from core.models import SiteSettings
from core.permissions import has_capability
from core.threads import MessageForm, post_message, thread_for
from members.utils import board_emails

from .forms import ExpenseFormSet, InvoiceForm, ProofUploadForm
from .models import Expense, Invoice

MAX_ATTACHMENTS_BYTES = 15 * 1024 * 1024


def finance_recipients():
    return SiteSettings.load().recipients("finance") + board_emails("T")


def _invoice_for(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related("author", "project"), pk=pk)
    if invoice.author_id != request.user.pk and not has_capability(request.user, "finance"):
        raise PermissionDenied
    return invoice


@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(author=request.user).select_related("project").prefetch_related("expense_set")
    return render(request, "bank/invoice_list.html", {"invoices": invoices})


def _proof_attachments(invoice):
    attachments, total = [], 0
    for expense in invoice.expense_set.all():
        if not expense.proof:
            continue
        try:
            with expense.proof.storage.open(expense.proof.name, "rb") as handle:
                data = handle.read()
        except OSError:
            continue
        total += len(data)
        if total > MAX_ATTACHMENTS_BYTES:
            break
        attachments.append((expense.proof.name.rsplit("/", 1)[-1], data, None))
    return attachments


@login_required
def invoice_create(request):
    invoice = Invoice(author=request.user, status="V")
    form = InvoiceForm(request.POST or None, instance=invoice)
    formset = ExpenseFormSet(request.POST or None, request.FILES or None, instance=invoice, prefix="depenses")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            invoice = form.save()
            for expense_form in formset.forms:
                if not expense_form.cleaned_data or expense_form.cleaned_data.get("DELETE"):
                    continue
                expense = expense_form.save(commit=False)
                expense.author = request.user
                expense.linked_invoice = invoice
                expense.save()
            invoice.refresh_total()
        invoice.refresh_from_db()
        send_templated_email(
            "invoice_new",
            {"invoice": invoice, "expenses": list(invoice.expense_set.all())},
            finance_recipients(),
            reply_to=[request.user.email],
            attachments=_proof_attachments(invoice),
        )
        log_activity(request, "invoice-created", f"Nouvelle note de frais « {invoice.title} » ({invoice.total_amount} €).", target=invoice, category="finance")
        messages.success(request, "Ta note de frais est envoyée à la trésorerie. Tu seras prévenu·e à chaque étape.")
        return redirect(invoice.get_absolute_url())
    return render(
        request,
        "bank/invoice_form.html",
        {"form": form, "formset": formset, "site": SiteSettings.load()},
    )


@login_required
def invoice_detail(request, pk):
    invoice = _invoice_for(request, pk)
    is_treasury = has_capability(request.user, "finance")
    return render(
        request,
        "bank/invoice_detail.html",
        {
            "invoice": invoice,
            "expenses": invoice.expense_set.all(),
            "thread": thread_for(invoice, include_internal=is_treasury),
            "message_form": MessageForm(allow_internal=is_treasury),
            "proof_form": ProofUploadForm(),
            "is_author": invoice.author_id == request.user.pk,
            "is_treasury": is_treasury,
        },
    )


@login_required
@require_POST
def invoice_message(request, pk):
    invoice = _invoice_for(request, pk)
    is_treasury = has_capability(request.user, "finance")
    form = MessageForm(request.POST, allow_internal=is_treasury)
    if form.is_valid():
        internal = form.cleaned_data.get("is_internal", False)
        from_board = is_treasury and invoice.author_id != request.user.pk
        post_message(invoice, author=request.user, body=form.cleaned_data["body"], is_internal=internal, is_from_board=from_board)
        if not internal:
            recipients = [invoice.author.email] if from_board else finance_recipients()
            send_templated_email("invoice_message", {"invoice": invoice, "body": form.cleaned_data["body"], "from_board": from_board}, recipients)
        form = MessageForm(allow_internal=is_treasury)
    return render(
        request,
        "bank/partials/thread.html",
        {"invoice": invoice, "thread": thread_for(invoice, include_internal=is_treasury), "message_form": form, "is_treasury": is_treasury},
    )


@login_required
@require_POST
def expense_proof(request, pk):
    """Ajout d'un justificatif manquant par l'auteur·ice de la dépense."""
    expense = get_object_or_404(Expense.objects.select_related("linked_invoice"), pk=pk)
    if expense.author_id != request.user.pk:
        raise PermissionDenied
    invoice = expense.linked_invoice
    if invoice and invoice.status in ("R", "X"):
        messages.error(request, "Cette note de frais est clôturée.")
        return redirect(invoice.get_absolute_url())
    form = ProofUploadForm(request.POST, request.FILES)
    if form.is_valid():
        expense.proof = form.cleaned_data["proof"]
        expense.save(update_fields=["proof"])
        if invoice:
            post_message(invoice, author=request.user, body=f"Justificatif ajouté pour « {expense.title} ».")
            send_templated_email(
                "invoice_message",
                {"invoice": invoice, "body": f"Nouveau justificatif ajouté pour la dépense « {expense.title} ».", "from_board": False},
                finance_recipients(),
            )
        messages.success(request, "Justificatif ajouté, merci !")
    else:
        for error in form.errors.get("proof", []):
            messages.error(request, error)
    return redirect(invoice.get_absolute_url() if invoice else "bank:list")
