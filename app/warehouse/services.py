"""Règles métier du magasin : disponibilités, brouillon de réservation, envoi."""

import datetime
from collections import defaultdict

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from core.audit import log_activity
from core.emails import send_templated_email
from core.models import SiteSettings
from members.utils import board_emails

from .models import BLOCKING_STATUSES, Item, Order, OrderLine, OrderStatus


class BookingError(Exception):
    """Erreur métier présentée telle quelle à l'utilisateur."""


# --------------------------------------------------------------------------- Droits
def booking_blockers(user):
    """Liste des raisons empêchant l'utilisateur de réserver (vide = autorisé)."""
    site = SiteSettings.load()
    reasons = []
    if not site.warehouse_enabled:
        reasons.append("Les réservations sont temporairement fermées.")
    if not user.is_authenticated:
        reasons.append("Connecte-toi pour réserver du matériel.")
        return reasons
    if not user.profile_complete:
        reasons.append("Complète ton profil (nom et téléphone) pour pouvoir réserver.")
    if site.warehouse_members_only and not (user.person and user.person.is_current_member):
        reasons.append("Le magasin est réservé aux adhérent·es à jour de cotisation.")
    return reasons


# ------------------------------------------------------------------- Disponibilités
def _overlapping_lines(start, end, statuses, exclude_order=None):
    lines = OrderLine.objects.filter(
        order__status__in=statuses,
        order__date_start__lt=end,
        order__date_end__gt=start,
        available=True,
    )
    if exclude_order is not None:
        lines = lines.exclude(order=exclude_order)
    return lines


def reserved_quantities(start, end, exclude_order=None):
    """Quantités déjà engagées (réservations acceptées) sur la période, par objet."""
    if not (start and end):
        return {}
    rows = (
        _overlapping_lines(start, end, BLOCKING_STATUSES, exclude_order)
        .values("item_id")
        .annotate(total=Sum("quantity"))
    )
    return {row["item_id"]: row["total"] for row in rows}


def pending_quantities(start, end, exclude_order=None):
    """Quantités demandées par d'autres réservations encore en attente de réponse."""
    if not (start and end):
        return {}
    rows = (
        _overlapping_lines(start, end, [OrderStatus.PENDING], exclude_order)
        .values("item_id")
        .annotate(total=Sum("quantity"))
    )
    return {row["item_id"]: row["total"] for row in rows}


def availability(items, start, end, exclude_order=None):
    """{item_id: {"available", "reserved", "pending"}} pour la période (ou le stock total sans dates)."""
    reserved = reserved_quantities(start, end, exclude_order)
    pending = pending_quantities(start, end, exclude_order)
    result = {}
    for item in items:
        taken = reserved.get(item.pk, 0)
        result[item.pk] = {
            "available": max(0, item.max_stock - taken) if item.is_bookable else 0,
            "reserved": taken,
            "pending": pending.get(item.pk, 0),
        }
    return result


def upcoming_bookings(item, limit=6):
    """Prochaines périodes où l'objet est sorti (pour la fiche objet)."""
    now = timezone.now()
    return (
        OrderLine.objects.filter(
            item=item, available=True, order__status__in=BLOCKING_STATUSES, order__date_end__gte=now
        )
        .select_related("order")
        .order_by("order__date_start")[:limit]
    )


# --------------------------------------------------------------------------- Dates
def validate_dates(start, end, *, now=None):
    site = SiteSettings.load()
    now = now or timezone.now()
    if not (start and end):
        raise BookingError("Indique une date de retrait et une date de retour.")
    if end <= start:
        raise BookingError("La date de retour doit être après la date de retrait.")
    if start < now + datetime.timedelta(hours=site.order_min_notice_hours):
        if site.order_min_notice_hours:
            raise BookingError(
                f"Le retrait doit être prévu au moins {site.order_min_notice_hours} h à l'avance, "
                "le temps que l'équipe du magasin réponde."
            )
        raise BookingError("La date de retrait est déjà passée.")
    if site.order_max_days and (end - start) > datetime.timedelta(days=site.order_max_days):
        raise BookingError(f"Un prêt ne peut pas dépasser {site.order_max_days} jours.")
    if start > now + datetime.timedelta(days=365):
        raise BookingError("On ne peut pas réserver plus d'un an à l'avance.")


# --------------------------------------------------------------------- Brouillon
def get_draft(user, create=True):
    draft = Order.objects.filter(user=user, status=OrderStatus.DRAFT).order_by("-pk").first()
    if draft is None and create:
        draft = Order.objects.create(user=user, status=OrderStatus.DRAFT, quantities="{}")
    return draft


def set_dates(order, start, end):
    validate_dates(start, end)
    order.date_start, order.date_end = start, end
    order.save(update_fields=["date_start", "date_end", "updated_at"])


def max_for(order, item):
    """Quantité maximale réservable de cet objet pour ce brouillon."""
    if not item.is_bookable:
        return 0
    if order.date_start and order.date_end:
        return availability([item], order.date_start, order.date_end, exclude_order=order)[item.pk]["available"]
    return item.max_stock


def set_quantity(order, item, quantity):
    """Fixe la quantité d'un objet dans le brouillon (0 = retirer)."""
    if order.status != OrderStatus.DRAFT:
        raise BookingError("Cette réservation n'est plus modifiable.")
    quantity = max(0, int(quantity))
    if quantity == 0:
        OrderLine.objects.filter(order=order, item=item).delete()
        return 0
    limit = max_for(order, item)
    if limit <= 0:
        raise BookingError(f"« {item.name} » n'est pas disponible{' sur ces dates' if order.date_start else ''}.")
    quantity = min(quantity, limit)
    OrderLine.objects.update_or_create(order=order, item=item, defaults={"quantity": quantity, "available": True})
    return quantity


def change_quantity(order, item, delta):
    line = OrderLine.objects.filter(order=order, item=item).first()
    current = line.quantity if line else 0
    return set_quantity(order, item, current + delta)


def draft_problems(order):
    """Lignes du brouillon qui dépassent la disponibilité réelle sur les dates choisies."""
    if not (order.date_start and order.date_end):
        return {}
    lines = list(order.lines.select_related("item"))
    stock = availability([line.item for line in lines], order.date_start, order.date_end, exclude_order=order)
    return {
        line.item_id: stock[line.item_id]["available"]
        for line in lines
        if line.quantity > stock[line.item_id]["available"]
    }


# ------------------------------------------------------------------------- Envoi
def warehouse_recipients():
    """Gestionnaires du magasin + adresses configurées par le CA."""
    return SiteSettings.load().recipients("orders") + board_emails("G")


@transaction.atomic
def submit(order, *, project_name, pickup_first_name, pickup_last_name, pickup_phone, message, request=None):
    site = SiteSettings.load()
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != OrderStatus.DRAFT:
        raise BookingError("Cette demande a déjà été envoyée.")
    if not order.lines.exists():
        raise BookingError("Ajoute au moins un objet à ta demande.")
    validate_dates(order.date_start, order.date_end)
    problems = draft_problems(order)
    if problems:
        raise BookingError("Certains objets ne sont plus disponibles en quantité suffisante sur ces dates : ajuste ta demande.")
    if site.order_cooldown_minutes:
        recent = (
            Order.objects.filter(user=order.user, status__gt=OrderStatus.DRAFT)
            .exclude(pk=order.pk)
            .filter(date_created__gte=timezone.now() - datetime.timedelta(minutes=site.order_cooldown_minutes))
            .exists()
        )
        if recent:
            raise BookingError(
                f"Tu as déjà envoyé une demande il y a moins de {site.order_cooldown_minutes} minutes. "
                "Si tu as oublié quelque chose, écris un message sur ta demande précédente."
            )
    order.project_name = project_name
    order.pickup_first_name = pickup_first_name
    order.pickup_last_name = pickup_last_name
    order.pickup_phone = pickup_phone
    order.message = message
    order.tos = True
    order.status = OrderStatus.PENDING
    order.date_created = timezone.now()
    order.save()

    transaction.on_commit(lambda: _notify_submitted(order))
    log_activity(
        request or order.user,
        "order-submitted",
        f"Nouvelle demande de réservation #{order.pk} ({order.total_items} objets).",
        target=order,
        category="warehouse",
    )
    return order


def _notify_submitted(order):
    lines = list(order.lines.select_related("item"))
    send_templated_email("order_received", {"order": order, "lines": lines}, [order.user.email])
    send_templated_email("order_new_for_team", {"order": order, "lines": lines}, warehouse_recipients())


# ------------------------------------------------------------------------- Clôture
# Au-delà de ce délai après la fin, une réservation non clôturée est considérée
# comme terminée et non comme « en retard » (cas de toutes celles de l'ancien site,
# qui ne connaissait ni le statut « rendu » ni le statut « annulé »).
STALE_AFTER = datetime.timedelta(days=30)


def stale_orders(now=None):
    limit = (now or timezone.now()) - STALE_AFTER
    return {
        "finished": Order.objects.filter(status__in=BLOCKING_STATUSES, date_end__lt=limit),
        "expired": Order.objects.filter(status=OrderStatus.PENDING, date_end__lt=limit),
    }


def close_stale_orders(request):
    """Marque comme rendues les réservations passées et annule les demandes périmées."""
    stale = stale_orders()
    now = timezone.now()
    finished = expired = 0
    with transaction.atomic():
        for order in stale["finished"].select_for_update():
            order.status = OrderStatus.RETURNED
            order.returned_at = order.date_end
            order.save(update_fields=["status", "returned_at", "updated_at"])
            finished += 1
        expired = stale["expired"].update(status=OrderStatus.CANCELLED, updated_at=now)
    if finished or expired:
        log_activity(
            request,
            "orders-closed",
            f"Clôture des anciennes réservations : {finished} marquée(s) rendue(s), {expired} demande(s) périmée(s) annulée(s).",
            category="warehouse",
        )
    return finished, expired
