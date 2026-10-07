"""Gestion du magasin : inventaire, réservations, calendrier."""

import calendar
import datetime

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.audit import log_activity
from core.emails import send_templated_email
from core.http import smart_redirect
from core.permissions import capability_required
from core.threads import MessageForm, post_message, thread_for
from warehouse import services
from warehouse.forms import ItemForm
from warehouse.models import BLOCKING_STATUSES, Item, Order, OrderLine, OrderStatus, Tag

from ..forms import OrderDecisionForm, OrderNotesForm
from ..tables import table

ORDER_FILTERS = [
    ("todo", "À traiter", [OrderStatus.PENDING]),
    ("to-sign", "Contrat à signer", [OrderStatus.ACCEPTED, OrderStatus.ACCEPTED_MODIFIED]),
    ("ongoing", "Validées", [OrderStatus.SIGNED]),
    ("done", "Terminées", [OrderStatus.RETURNED]),
    ("closed", "Refusées / annulées", [OrderStatus.REFUSED, OrderStatus.CANCELLED]),
    ("all", "Toutes", None),
]


# ------------------------------------------------------------------- Inventaire
@capability_required("warehouse")
def items(request):
    queryset = Item.objects.prefetch_related("tags").annotate(
        bookings=Count("order_lines", filter=Q(order_lines__order__status__in=BLOCKING_STATUSES), distinct=True)
    )
    state = request.GET.get("etat", "")
    if state == "archives":
        queryset = queryset.filter(is_archived=True)
    else:
        queryset = queryset.filter(is_archived=False)
        if state == "indisponibles":
            queryset = queryset.filter(Q(availability=0) | Q(state__lt=1))
    tag = request.GET.get("tag", "")
    if tag.isdigit():
        queryset = queryset.filter(tags__pk=int(tag))
    context = table(
        request,
        queryset,
        search_fields=["name", "owner", "description", "tags__name"],
        sorts={"nom": "name", "stock": "max_stock", "etat": "state", "ajout": "created_at"},
        default_sort="nom",
        per_page=60,
    )
    context.update({"tags": Tag.objects.all(), "tag": tag, "state": state})
    if request.htmx and request.htmx.target == "table":
        return render(request, "backoffice/warehouse/partials/items_table.html", context)
    return render(request, "backoffice/warehouse/items.html", context)


@capability_required("warehouse")
def item_form(request, pk=None):
    item = get_object_or_404(Item, pk=pk) if pk else None
    form = ItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        log_activity(request, "item-saved", f"Objet « {item.name} » {'modifié' if pk else 'ajouté'}.", target=item, category="warehouse", data={"champs": form.changed_data})
        messages.success(request, f"« {item.name} » enregistré.")
        if request.POST.get("again"):
            return redirect("backoffice:item-create")
        return redirect("backoffice:items")
    upcoming = services.upcoming_bookings(item, limit=10) if item else []
    return render(request, "backoffice/warehouse/item_form.html", {"form": form, "item": item, "upcoming": upcoming})


@capability_required("warehouse")
@require_POST
def item_archive(request, pk):
    item = get_object_or_404(Item, pk=pk)
    item.is_archived = not item.is_archived
    item.save(update_fields=["is_archived"])
    log_activity(request, "item-archived", f"Objet « {item.name} » {'archivé' if item.is_archived else 'réactivé'}.", target=item, category="warehouse")
    messages.success(request, f"« {item.name} » {'archivé : il n’apparaît plus dans le catalogue' if item.is_archived else 'de retour dans le catalogue'}.")
    return smart_redirect(request, "backoffice:items")


@capability_required("warehouse")
@require_POST
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.order_lines.exists():
        messages.error(request, "Cet objet figure dans des réservations : archive-le plutôt que de le supprimer.")
        return smart_redirect(request, "backoffice:item-edit", pk=item.pk)
    name = item.name
    item.delete()
    log_activity(request, "item-deleted", f"Objet « {name} » supprimé.", category="warehouse")
    messages.success(request, f"« {name} » supprimé.")
    return smart_redirect(request, "backoffice:items")


# ------------------------------------------------------------------ Réservations
@capability_required("warehouse")
def orders(request):
    key = request.GET.get("vue", "todo")
    statuses = next((s for k, _l, s in ORDER_FILTERS if k == key), [OrderStatus.PENDING])
    queryset = Order.objects.submitted().select_related("user", "user__site_person").annotate(nb_items=Sum("lines__quantity"))
    if request.GET.get("statut", "").isdigit():
        queryset = queryset.filter(status=int(request.GET["statut"]))
    elif statuses is not None:
        queryset = queryset.filter(status__in=statuses)
    context = table(
        request,
        queryset,
        search_fields=["project_name", "user__email", "user__site_person__first_name", "user__site_person__last_name", "pickup_last_name", "id"],
        sorts={"numero": "pk", "debut": "date_start", "envoi": "date_created"},
        default_sort="debut" if key in ("todo", "to-sign", "ongoing") else "-envoi",
        per_page=40,
    )
    counts = {k: (Order.objects.submitted().filter(status__in=s).count() if s else None) for k, _l, s in ORDER_FILTERS}
    stale = services.stale_orders()
    context.update(
        {
            "filters": [(k, l, counts[k]) for k, l, _s in ORDER_FILTERS],
            "view": key,
            "stale_finished": stale["finished"].count(),
            "stale_expired": stale["expired"].count(),
        }
    )
    if request.htmx and request.htmx.target == "table":
        return render(request, "backoffice/warehouse/partials/orders_table.html", context)
    return render(request, "backoffice/warehouse/orders.html", context)


@capability_required("warehouse")
@require_POST
def orders_close_stale(request):
    finished, expired = services.close_stale_orders(request)
    messages.success(request, f"{finished} réservation(s) marquée(s) rendue(s), {expired} demande(s) périmée(s) annulée(s).")
    return smart_redirect(request, "backoffice:orders")


def _lines_with_conflicts(order):
    lines = list(order.lines.select_related("item"))
    if order.date_start and order.date_end:
        stock = services.availability([line.item for line in lines], order.date_start, order.date_end, exclude_order=order)
        for line in lines:
            line.stock = stock[line.item_id]
            line.conflict = line.available and line.quantity > line.stock["available"]
    return lines


@capability_required("warehouse")
def order_manage(request, pk):
    order = get_object_or_404(Order.objects.select_related("user", "user__site_person"), pk=pk)
    decision = OrderDecisionForm(request.POST or None, initial={"status": order.status}, prefix="decision")
    if request.method == "POST" and request.POST.get("action") == "decision" and decision.is_valid():
        new_status = decision.cleaned_data["status"]
        note = decision.cleaned_data["note"].strip()
        previous = order.get_status_display()
        order.status = new_status
        if new_status in (OrderStatus.ACCEPTED, OrderStatus.ACCEPTED_MODIFIED, OrderStatus.REFUSED):
            order.date_validated = timezone.now()
        if new_status == OrderStatus.RETURNED:
            order.returned_at = timezone.now()
        order.save()
        if note:
            post_message(order, author=request.user, body=note, is_from_board=True)
        if decision.cleaned_data["notify"] and order.user:
            send_templated_email("order_status_changed", {"order": order, "note": note}, [order.user.email])
        log_activity(request, "order-status", f"Réservation #{order.pk} : {previous} → {order.get_status_display()}.", target=order, category="warehouse")
        messages.success(request, f"Réservation #{order.pk} : {order.get_status_display()}.")
        return redirect("backoffice:order-detail", pk=order.pk)
    context = {
        "order": order,
        "lines": _lines_with_conflicts(order),
        "decision": decision,
        "notes_form": OrderNotesForm(instance=order),
        "thread": thread_for(order, include_internal=True),
        "message_form": MessageForm(allow_internal=True),
        "contract": getattr(order, "contract", None),
        "history": Order.objects.filter(user=order.user).exclude(pk=order.pk).exclude(status=0).order_by("-date_start")[:5] if order.user else [],
    }
    return render(request, "backoffice/warehouse/order_manage.html", context)


@capability_required("warehouse")
@require_POST
def order_line_toggle(request, pk, line_pk):
    line = get_object_or_404(OrderLine.objects.select_related("order", "item"), pk=line_pk, order_id=pk)
    if "quantity" in request.POST:
        try:
            line.quantity = max(1, min(int(request.POST["quantity"]), line.item.max_stock))
        except ValueError:
            pass
    else:
        line.available = not line.available
    line.save()
    line.order.save(update_fields=["updated_at"])
    lines = _lines_with_conflicts(line.order)
    return render(request, "backoffice/warehouse/partials/order_lines.html", {"order": line.order, "lines": lines})


@capability_required("warehouse")
@require_POST
def order_notes(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = OrderNotesForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
    return HttpResponse('<span class="text-xs text-emerald-600">Enregistré ✓</span>')


# --------------------------------------------------------------------- Calendrier
@capability_required("warehouse")
def calendar_view(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get("annee", today.year))
        month = int(request.GET.get("mois", today.month))
        first = datetime.date(year, month, 1)
    except ValueError:
        first = today.replace(day=1)
    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(first.year, first.month)
    start = timezone.make_aware(datetime.datetime.combine(weeks[0][0], datetime.time.min))
    end = timezone.make_aware(datetime.datetime.combine(weeks[-1][-1], datetime.time.max))
    month_orders = list(
        Order.objects.filter(status__in=[OrderStatus.PENDING, *BLOCKING_STATUSES])
        .overlapping(start, end)
        .select_related("user", "user__site_person")
        .order_by("date_start")
    )
    days = []
    for week in weeks:
        row = []
        for day in week:
            day_start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))
            day_end = timezone.make_aware(datetime.datetime.combine(day, datetime.time.max))
            row.append(
                {
                    "date": day,
                    "in_month": day.month == first.month,
                    "is_today": day == today,
                    "orders": [o for o in month_orders if o.date_start <= day_end and o.date_end >= day_start],
                }
            )
        days.append(row)
    previous = (first - datetime.timedelta(days=1)).replace(day=1)
    following = (first + datetime.timedelta(days=32)).replace(day=1)
    return render(
        request,
        "backoffice/warehouse/calendar.html",
        {"weeks": days, "month": first, "previous": previous, "following": following, "orders": month_orders},
    )
