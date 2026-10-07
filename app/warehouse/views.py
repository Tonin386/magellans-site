"""Magasin côté membres : catalogue, demande de réservation, suivi, contrat."""

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from core.audit import log_activity
from core.emails import send_templated_email
from core.models import SiteSettings
from core.permissions import has_capability
from core.threads import MessageForm, post_message, thread_for
from core.http import smart_redirect
from core.utils import client_ip

from . import contracts, services
from .forms import CheckoutForm, ContractInfoForm, DatesForm, SignForm
from .models import BLOCKING_STATUSES, Contract, Item, Order, OrderLine, OrderStatus, Tag
from .services import BookingError


def _order_for(request, pk):
    order = get_object_or_404(Order.objects.select_related("user", "user__site_person"), pk=pk)
    if order.user_id != request.user.pk and not has_capability(request.user, "warehouse"):
        raise PermissionDenied
    return order


def _catalogue_context(request, draft=None):
    items = list(
        Item.objects.filter(is_archived=False).prefetch_related("tags").order_by("name")
    )
    start = draft.date_start if draft else None
    end = draft.date_end if draft else None
    stock = services.availability(items, start, end, exclude_order=draft)
    in_cart = {line.item_id: line.quantity for line in draft.lines.all()} if draft else {}
    for item in items:
        item.stock = stock[item.pk]
        item.in_cart = in_cart.get(item.pk, 0)
    return {
        "items": items,
        "tags": Tag.objects.filter(items__is_archived=False).distinct().order_by("name"),
        "draft": draft,
        "blockers": services.booking_blockers(request.user),
        "has_dates": bool(start and end),
    }


def catalogue(request):
    draft = services.get_draft(request.user, create=False) if request.user.is_authenticated else None
    context = _catalogue_context(request, draft)
    initial = (
        {"start": timezone.localtime(draft.date_start), "end": timezone.localtime(draft.date_end)}
        if draft and draft.date_start
        else DatesForm.suggested_initial()
    )
    context["dates_form"] = DatesForm(initial=initial)
    context["base_template"] = "layouts/app.html" if request.user.is_authenticated else "layouts/public.html"
    context["notice"] = SiteSettings.load().warehouse_notice
    return render(request, "warehouse/catalogue.html", context)


@login_required
@require_POST
def set_dates(request):
    draft = services.get_draft(request.user)
    form = DatesForm(request.POST)
    if form.is_valid():
        services.set_dates(draft, form.cleaned_data["start"], form.cleaned_data["end"])
        problems = services.draft_problems(draft)
        if problems:
            messages.warning(request, "Certains objets de ta demande ne sont pas disponibles en totalité sur ces dates : vérifie les quantités.")
        else:
            messages.success(request, "Dates enregistrées : les disponibilités sont à jour.")
    if request.htmx:
        context = _catalogue_context(request, draft)
        context["dates_form"] = form
        response = render(request, "warehouse/partials/catalogue_body.html", context)
        response["HX-Trigger"] = "cart-updated"
        return response
    if not form.is_valid():
        for error in form.non_field_errors() or [e for errors in form.errors.values() for e in errors]:
            messages.error(request, error)
            break
    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse("warehouse:catalogue")
    return redirect(next_url)


@login_required
@require_POST
def cart_change(request, item_pk):
    """Ajoute / retire une unité d'un objet (ou fixe une quantité)."""
    item = get_object_or_404(Item, pk=item_pk, is_archived=False)
    blockers = services.booking_blockers(request.user)
    draft = services.get_draft(request.user)
    if blockers:
        messages.error(request, blockers[0])
    else:
        try:
            if "quantity" in request.POST:
                services.set_quantity(draft, item, int(request.POST.get("quantity") or 0))
            else:
                services.change_quantity(draft, item, int(request.POST.get("delta", 1)))
        except (BookingError, ValueError) as error:
            messages.error(request, str(error) if isinstance(error, BookingError) else "Quantité invalide.")
    if request.htmx:
        target = request.POST.get("target", "card")
        if target == "line":
            response = render(request, "warehouse/partials/cart_lines.html", _cart_context(draft))
        else:
            stock = services.availability([item], draft.date_start, draft.date_end, exclude_order=draft)
            item.stock = stock[item.pk]
            line = OrderLine.objects.filter(order=draft, item=item).first()
            item.in_cart = line.quantity if line else 0
            response = render(
                request,
                "warehouse/partials/item_card.html",
                {"item": item, "draft": draft, "blockers": blockers, "has_dates": bool(draft.date_start)},
            )
        response["HX-Trigger"] = "cart-updated"
        return response
    return redirect(request.POST.get("next") or "warehouse:catalogue")


@login_required
@require_GET
def cart_panel(request):
    draft = services.get_draft(request.user, create=False)
    return render(request, "warehouse/partials/cart_panel.html", {"draft": draft})


def _cart_context(draft):
    lines = list(draft.lines.select_related("item").order_by("item__name"))
    problems = services.draft_problems(draft)
    for line in lines:
        line.max_available = problems.get(line.item_id)
    return {"draft": draft, "lines": lines, "problems": problems}


@login_required
def cart(request):
    """Récapitulatif et envoi de la demande."""
    draft = services.get_draft(request.user)
    blockers = services.booking_blockers(request.user)
    person = request.user.person
    initial = {
        "pickup_first_name": person.clean_first_name if person else "",
        "pickup_last_name": person.clean_last_name if person else "",
        "pickup_phone": person.phone if person else "",
        "project_name": draft.project_name or "",
        "message": draft.message or "",
    }
    form = CheckoutForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid() and not blockers:
        data = form.cleaned_data
        try:
            order = services.submit(
                draft,
                project_name=data["project_name"],
                pickup_first_name=data["pickup_first_name"] or initial["pickup_first_name"],
                pickup_last_name=data["pickup_last_name"] or initial["pickup_last_name"],
                pickup_phone=data["pickup_phone"] or initial["pickup_phone"],
                message=data["message"],
                request=request,
            )
        except BookingError as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, "Ta demande est envoyée ! L'équipe du magasin te répond très vite par e-mail.")
            return redirect(order.get_absolute_url())
    context = {**_cart_context(draft), "form": form, "blockers": blockers, "site": SiteSettings.load()}
    context["dates_form"] = DatesForm(
        initial={"start": timezone.localtime(draft.date_start), "end": timezone.localtime(draft.date_end)}
        if draft.date_start
        else DatesForm.suggested_initial()
    )
    return render(request, "warehouse/cart.html", context)


@login_required
def orders(request):
    order_list = (
        Order.objects.filter(user=request.user)
        .exclude(status=OrderStatus.DRAFT)
        .prefetch_related(Prefetch("lines", queryset=OrderLine.objects.select_related("item")))
        .select_related("contract")
        .order_by("-date_start")
    )
    return render(request, "warehouse/orders.html", {"orders": order_list})


def status_steps(order):
    """Frise d'avancement d'une réservation."""
    def fmt(value):
        return timezone.localtime(value).strftime("%d/%m/%Y") if value else ""

    refused = order.status in (OrderStatus.REFUSED, OrderStatus.CANCELLED)
    steps = [
        {"label": "Demande envoyée", "state": "done", "date": fmt(order.date_created)},
        {
            "label": "Réponse du magasin" if not refused else order.get_status_display(),
            "state": "failed" if refused else ("done" if order.status >= OrderStatus.ACCEPTED else "current"),
            "date": fmt(order.date_validated),
        },
        {
            "label": "Contrat signé",
            "state": "done" if order.status in (OrderStatus.SIGNED, OrderStatus.RETURNED) else ("current" if order.is_accepted else "todo"),
            "date": fmt(getattr(getattr(order, "contract", None), "signed_at", None)),
        },
        {
            "label": "Matériel rendu",
            "state": "done" if order.status == OrderStatus.RETURNED else ("current" if order.status == OrderStatus.SIGNED else "todo"),
            "date": fmt(order.returned_at),
        },
    ]
    if refused:
        steps = steps[:2]
    return steps


@login_required
def order_detail(request, pk):
    order = _order_for(request, pk)
    if order.status == OrderStatus.DRAFT and order.user_id == request.user.pk:
        return redirect("warehouse:cart")
    is_manager = has_capability(request.user, "warehouse")
    context = {
        "order": order,
        "lines": order.lines.select_related("item").order_by("item__name"),
        "steps": status_steps(order),
        "thread": thread_for(order, include_internal=is_manager),
        "message_form": MessageForm(allow_internal=is_manager),
        "contract": getattr(order, "contract", None),
        "is_owner": order.user_id == request.user.pk,
        "is_manager": is_manager,
    }
    return render(request, "warehouse/order_detail.html", context)


@login_required
@require_POST
def order_message(request, pk):
    order = _order_for(request, pk)
    is_manager = has_capability(request.user, "warehouse")
    form = MessageForm(request.POST, allow_internal=is_manager)
    if form.is_valid():
        internal = form.cleaned_data.get("is_internal", False)
        from_board = is_manager and order.user_id != request.user.pk
        post_message(order, author=request.user, body=form.cleaned_data["body"], is_internal=internal, is_from_board=from_board)
        if not internal:
            if from_board:
                send_templated_email("order_message", {"order": order, "body": form.cleaned_data["body"], "from_board": True}, [order.user.email])
            else:
                send_templated_email("order_message", {"order": order, "body": form.cleaned_data["body"], "from_board": False}, services.warehouse_recipients())
        form = MessageForm(allow_internal=is_manager)
    return render(
        request,
        "warehouse/partials/thread.html",
        {"order": order, "thread": thread_for(order, include_internal=is_manager), "message_form": form, "is_manager": is_manager},
    )


@login_required
@require_POST
def order_cancel(request, pk):
    order = _order_for(request, pk)
    if order.user_id != request.user.pk:
        raise PermissionDenied
    if not order.owner_can_cancel:
        messages.error(request, "Cette réservation ne peut plus être annulée en ligne : contacte le magasin.")
        return smart_redirect(request, order.get_absolute_url())
    order.status = OrderStatus.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    post_message(order, author=request.user, body="Réservation annulée par le demandeur.")
    send_templated_email("order_cancelled", {"order": order}, services.warehouse_recipients())
    log_activity(request, "order-cancelled", f"Réservation #{order.pk} annulée par le demandeur.", target=order, category="warehouse")
    messages.success(request, "Ta réservation est annulée. L'équipe du magasin est prévenue.")
    return smart_redirect(request, order.get_absolute_url())


@login_required
def order_ics(request, pk):
    """Ajout du retrait et du retour du matériel à son agenda."""
    order = _order_for(request, pk)
    if not (order.date_start and order.date_end):
        raise PermissionDenied
    site = SiteSettings.load()

    def ics_date(value):
        return value.astimezone(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")

    def event(uid, start, summary):
        end = start + datetime.timedelta(minutes=30)
        return [
            "BEGIN:VEVENT",
            f"UID:{uid}@magellans.fr",
            f"DTSTAMP:{ics_date(timezone.now())}",
            f"DTSTART:{ics_date(start)}",
            f"DTEND:{ics_date(end)}",
            f"SUMMARY:{summary}",
            f"LOCATION:{site.pickup_address}",
            f"URL:{request.build_absolute_uri(order.get_absolute_url())}",
            "END:VEVENT",
        ]

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Magellans//Magasin//FR", "CALSCALE:GREGORIAN"]
    lines += event(f"order-{order.pk}-pickup", order.date_start, f"Retrait du matériel Magellans (réservation #{order.pk})")
    lines += event(f"order-{order.pk}-return", order.date_end, f"Retour du matériel Magellans (réservation #{order.pk})")
    lines.append("END:VCALENDAR")
    response = HttpResponse("\r\n".join(lines) + "\r\n", content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="reservation-magellans-{order.pk}.ics"'
    return response


def item_detail(request, pk):
    item = get_object_or_404(Item.objects.prefetch_related("tags"), pk=pk, is_archived=False)
    draft = services.get_draft(request.user, create=False) if request.user.is_authenticated else None
    stock = services.availability([item], draft.date_start if draft else None, draft.date_end if draft else None, exclude_order=draft)
    item.stock = stock[item.pk]
    context = {
        "item": item,
        "draft": draft,
        "upcoming": services.upcoming_bookings(item),
        "has_dates": bool(draft and draft.date_start),
    }
    template = "warehouse/partials/item_modal.html" if request.htmx else "warehouse/item_detail.html"
    if not request.htmx:
        context["base_template"] = "layouts/app.html" if request.user.is_authenticated else "layouts/public.html"
    return render(request, template, context)


# ---------------------------------------------------------------------- Contrat
@login_required
def contract(request, pk):
    order = _order_for(request, pk)
    contract_obj = getattr(order, "contract", None)
    if contract_obj and contract_obj.is_signed:
        return redirect(order.get_absolute_url())
    if not order.is_accepted:
        messages.info(request, "Le contrat sera disponible quand ta réservation aura été acceptée.")
        return redirect(order.get_absolute_url())
    if order.user_id != request.user.pk:
        raise PermissionDenied("Seule la personne qui a réservé peut signer le contrat.")

    info_form = ContractInfoForm(request.POST or None, instance=contract_obj or Contract(order=order), prefix="info")
    sign_form = None
    step = "info"
    if contract_obj and request.GET.get("modifier") is None:
        step = "sign"
    if request.method == "POST" and request.POST.get("step") == "info":
        if info_form.is_valid():
            contract_obj = info_form.save(commit=False)
            contract_obj.order = order
            contract_obj.save()
            return redirect("warehouse:contract", pk=order.pk)
        step = "info"
    if step == "sign":
        person = request.user.person
        sign_form = SignForm(request.POST or None, initial={"signer_name": person.full_name if person else ""}, prefix="sign")
        if request.method == "POST" and request.POST.get("step") == "sign" and sign_form.is_valid():
            try:
                contracts.sign(
                    contract_obj,
                    signer_name=sign_form.cleaned_data["signer_name"],
                    signature_data_url=sign_form.cleaned_data["signature"],
                    ip=client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    request=request,
                )
            except BookingError as error:
                sign_form.add_error(None, str(error))
            else:
                messages.success(request, "Contrat signé ! Tu le reçois aussi par e-mail. Bon tournage 🎬")
                return redirect(order.get_absolute_url())
    return render(
        request,
        "warehouse/contract.html",
        {
            "order": order,
            "contract": contract_obj,
            "info_form": info_form,
            "sign_form": sign_form,
            "step": step,
            "terms": contracts.current_terms(),
            "lines": [line for line in order.lines.select_related("item") if line.available],
        },
    )


@login_required
def contract_pdf(request, pk):
    """Aperçu du contrat (non signé) ou version signée."""
    order = _order_for(request, pk)
    contract_obj = getattr(order, "contract", None)
    if contract_obj is None:
        raise PermissionDenied
    if contract_obj.is_signed and contract_obj.pdf:
        return redirect(reverse("core:private-file", kwargs={"model": "warehouse.contract", "pk": contract_obj.pk, "field": "pdf"}))
    pdf = contracts.render_pdf(contract_obj, preview=True)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="apercu-contrat-{contract_obj.reference}.pdf"'
    response["Cache-Control"] = "private, no-store"
    return response


def contract_verify(request):
    """Vérification publique de l'authenticité d'un contrat à partir de son code."""
    code = (request.GET.get("code") or "").strip()
    found = contracts.find_by_code(code) if len(code.replace("-", "")) >= 16 else None
    base_template = "layouts/app.html" if request.user.is_authenticated else "layouts/public.html"
    return render(
        request,
        "warehouse/contract_verify.html",
        {"code": code, "found": found, "searched": bool(code), "base_template": base_template},
    )
