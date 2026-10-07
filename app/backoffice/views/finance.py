"""Trésorerie : opérations et notes de frais."""

import datetime
from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from bank.forms import OperationForm
from bank.models import OPE_TYPES, OPERATION_CATEGORIES, STATUS, Invoice, Operation, compute_balance
from core.audit import log_activity
from core.emails import send_templated_email
from core.permissions import capability_required, has_capability
from core.threads import MessageForm, post_message, thread_for
from core.utils import to_decimal
from memberships.models import Season

from ..charts import monthly_bars
from ..forms import InvoiceStatusForm
from ..tables import csv_response, table

MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def _operations_queryset(request):
    queryset = Operation.objects.select_related("third_party", "invoice")
    kind = request.GET.get("type", "")
    if kind in dict(OPE_TYPES):
        queryset = queryset.filter(type=kind)
    category = request.GET.get("categorie", "")
    if category in dict(OPERATION_CATEGORIES):
        queryset = queryset.filter(category=category)
    season_label = request.GET.get("saison", "")
    season = Season.objects.filter(label=season_label).first() if season_label else None
    if season:
        queryset = queryset.filter(date__range=(season.start_date, season.end_date))
    return queryset, kind, category, season


@capability_required("finance")
def finance(request):
    queryset, kind, category, season = _operations_queryset(request)
    context = table(
        request,
        queryset,
        search_fields=["id", "desc", "third_party__first_name", "third_party__last_name", "third_party__organisation_name"],
        sorts={"date": ["date", "date_created"], "montant": "amount", "numero": "date_created"},
        default_sort="-date",
        per_page=50,
    )
    filtered_total = sum((op.signed_amount for op in queryset), Decimal("0"))
    context.update(
        {
            "kind": kind,
            "category": category,
            "season": season,
            "seasons": Season.objects.all(),
            "types": OPE_TYPES,
            "categories": OPERATION_CATEGORIES,
            "filtered_total": filtered_total,
            "can_edit": has_capability(request.user, "finance_edit"),
        }
    )
    if request.htmx and request.htmx.target == "table":
        return render(request, "backoffice/finance/partials/operations_table.html", context)
    today = timezone.localdate()
    months, year, month = [], today.year, today.month
    periods = []
    for _ in range(12):
        periods.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    for year, month in reversed(periods):
        first = datetime.date(year, month, 1)
        last = (first + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
        month_ops = Operation.objects.filter(date__range=(first, last))
        credit = sum((to_decimal(o.amount) for o in month_ops if o.type == "C"), Decimal("0"))
        debit = sum((to_decimal(o.amount) for o in month_ops if o.type != "C"), Decimal("0"))
        months.append((MONTHS[first.month - 1], credit, debit))
    current = Season.current()
    season_ops = Operation.objects.filter(date__range=(current.start_date, current.end_date)) if current else Operation.objects.none()
    context.update(
        {
            "balance": compute_balance(),
            "chart": monthly_bars(months),
            "season_credit": sum((to_decimal(o.amount) for o in season_ops if o.type == "C"), Decimal("0")),
            "season_debit": sum((to_decimal(o.amount) for o in season_ops if o.type != "C"), Decimal("0")),
            "current_season": current,
            "invoices_todo": Invoice.objects.filter(status__in=["V", "F", "C"]).count(),
        }
    )
    return render(request, "backoffice/finance/index.html", context)


@capability_required("finance")
def finance_export(request):
    queryset, *_ = _operations_queryset(request)
    rows = []
    balance = Decimal("0")
    for op in queryset.order_by("date", "date_created"):
        balance += op.signed_amount
        rows.append(
            [
                op.id,
                op.date.strftime("%d/%m/%Y"),
                op.get_type_display(),
                op.get_category_display(),
                op.third_party.display_name,
                op.desc,
                f"{op.signed_amount:.2f}".replace(".", ","),
                f"{balance:.2f}".replace(".", ","),
            ]
        )
    return csv_response(
        "tresorerie-magellans.csv",
        ["N°", "Date", "Type", "Catégorie", "Tiers", "Libellé", "Montant (€)", "Solde cumulé (€)"],
        rows,
    )


@capability_required("finance_edit")
def operation_form(request, pk=None):
    operation = get_object_or_404(Operation, pk=pk) if pk else None
    initial = {}
    if operation is None:
        initial["date"] = timezone.localdate()
        invoice_id = request.GET.get("note")
        if invoice_id and invoice_id.isdigit():
            invoice = Invoice.objects.filter(pk=int(invoice_id)).select_related("author").first()
            if invoice:
                initial.update(
                    {
                        "type": "R",
                        "category": "reimbursements",
                        "invoice": invoice.pk,
                        "amount": invoice.total_amount,
                        "desc": f"Remboursement note de frais « {invoice.title} »",
                        "third_party": invoice.author.person.pk if invoice.author and invoice.author.person else None,
                    }
                )
    form = OperationForm(request.POST or None, request.FILES or None, instance=operation, initial=initial)
    if request.method == "POST" and form.is_valid():
        operation = form.save(commit=False)
        if not pk:
            operation.created_by = request.user
        operation.save()
        log_activity(
            request,
            "operation-saved",
            f"Opération {operation.id} {'modifiée' if pk else 'saisie'} : {operation.desc} ({operation.signed_amount} €).",
            target=operation,
            category="finance",
            data={"champs": form.changed_data},
        )
        messages.success(request, f"Opération {operation.id} enregistrée.")
        return redirect("backoffice:finance")
    return render(request, "backoffice/finance/operation_form.html", {"form": form, "operation": operation})


@capability_required("finance")
def invoices(request):
    queryset = Invoice.objects.select_related("author", "author__site_person", "project").prefetch_related("expense_set")
    status = request.GET.get("statut", "todo")
    if status == "todo":
        queryset = queryset.filter(status__in=["V", "F", "D", "J", "C"])
    elif status in dict(STATUS):
        queryset = queryset.filter(status=status)
    context = table(
        request,
        queryset,
        search_fields=["title", "author__email", "author__site_person__first_name", "author__site_person__last_name", "project__name"],
        sorts={"date": "date_created", "titre": "title"},
        default_sort="-date",
        per_page=40,
    )
    context.update({"status": status, "statuses": STATUS})
    if request.htmx and request.htmx.target == "table":
        return render(request, "backoffice/finance/partials/invoices_table.html", context)
    return render(request, "backoffice/finance/invoices.html", context)


@capability_required("finance")
def invoice_manage(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related("author", "author__site_person", "project"), pk=pk)
    can_edit = has_capability(request.user, "finance_edit")
    form = InvoiceStatusForm(request.POST or None, initial={"status": invoice.status}, prefix="status")
    if request.method == "POST" and can_edit and form.is_valid():
        previous = invoice.get_status_display()
        invoice.status = form.cleaned_data["status"]
        invoice.save()
        note = form.cleaned_data["note"].strip()
        if note:
            post_message(invoice, author=request.user, body=note, is_from_board=True)
        if form.cleaned_data["notify"] and invoice.author:
            send_templated_email("invoice_status_changed", {"invoice": invoice, "note": note}, [invoice.author.email])
        log_activity(request, "invoice-status", f"Note de frais « {invoice.title} » : {previous} → {invoice.get_status_display()}.", target=invoice, category="finance")
        messages.success(request, "Statut mis à jour.")
        return redirect("backoffice:invoice-detail", pk=invoice.pk)
    return render(
        request,
        "backoffice/finance/invoice_manage.html",
        {
            "invoice": invoice,
            "expenses": invoice.expense_set.all(),
            "form": form,
            "can_edit": can_edit,
            "thread": thread_for(invoice, include_internal=True),
            "message_form": MessageForm(allow_internal=True),
            "operations": invoice.operations.all(),
            "reimburse_url": f"{reverse('backoffice:operation-create')}?note={invoice.pk}",
        },
    )
