"""Tableau de bord de l'espace CA et journal d'activité."""

import datetime

from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from bank.models import Invoice, Operation, compute_balance
from core.models import ActivityLog, Page
from core.permissions import capability_required, has_capability
from dashboard.models import ProjectFundingRequest
from members.models import Member
from memberships.models import HelloAssoEvent, Season
from warehouse import services as warehouse_services
from warehouse.models import BLOCKING_STATUSES, Order, OrderStatus

from ..charts import season_progress
from ..tables import table


@capability_required("backoffice")
def dashboard(request):
    now = timezone.now()
    season = Season.current()
    previous = Season.objects.filter(start_date__lt=season.start_date).order_by("-start_date").first() if season else None
    week_end = now + datetime.timedelta(days=7)
    context = {
        "season": season,
        "previous": previous,
        "season_stats": season.stats() if season else None,
        "previous_stats": previous.stats() if previous else None,
        "chart": season_progress(season, previous),
        "pending_orders": Order.objects.filter(status=OrderStatus.PENDING).select_related("user", "user__site_person").order_by("date_start")[:6],
        "pending_orders_count": Order.objects.filter(status=OrderStatus.PENDING).count(),
        "to_sign_count": Order.objects.filter(status__in=[OrderStatus.ACCEPTED, OrderStatus.ACCEPTED_MODIFIED], date_end__gte=now).count(),
        "pickups": Order.objects.filter(status__in=BLOCKING_STATUSES, date_start__range=(now, week_end)).select_related("user", "user__site_person").order_by("date_start")[:8],
        "returns": Order.objects.filter(status__in=BLOCKING_STATUSES, date_end__range=(now - datetime.timedelta(days=2), week_end)).select_related("user", "user__site_person").order_by("date_end")[:8],
        "late_returns": Order.objects.filter(
            status__in=BLOCKING_STATUSES, date_end__range=(now - warehouse_services.STALE_AFTER, now - datetime.timedelta(hours=12))
        ).count(),
        "stale_orders": sum(qs.count() for qs in warehouse_services.stale_orders(now).values()),
        "invoices_todo": Invoice.objects.filter(status__in=["V", "F"]).count(),
        "funding_todo": ProjectFundingRequest.objects.filter(status__in=["submitted", "reviewing"]).count(),
        "pages_to_review": Page.objects.filter(needs_review=True),
        "new_accounts": Member.objects.filter(date_joined__gte=now - datetime.timedelta(days=30)).count(),
        "activity": ActivityLog.objects.select_related("actor", "actor__site_person")[:12],
        "last_webhook": HelloAssoEvent.objects.first(),
        "webhook_errors": HelloAssoEvent.objects.filter(status__in=["error", "rejected"], received_at__gte=now - datetime.timedelta(days=30)).count(),
        "helloasso_warnings": season.helloasso_warnings() if season else [],
    }
    if has_capability(request.user, "finance"):
        context["balance"] = compute_balance()
        context["last_operations"] = Operation.objects.select_related("third_party")[:5]
    return render(request, "backoffice/dashboard.html", context)


@capability_required("audit")
def activity(request):
    queryset = ActivityLog.objects.select_related("actor", "actor__site_person")
    category = request.GET.get("domaine", "")
    if category:
        queryset = queryset.filter(category=category)
    actor = request.GET.get("auteur", "")
    if actor.isdigit():
        queryset = queryset.filter(actor_id=int(actor))
    context = table(request, queryset, search_fields=["message", "target_repr", "verb"], per_page=50)
    context.update(
        {
            "categories": ActivityLog.CATEGORY_CHOICES,
            "category": category,
            "actors": Member.objects.filter(activity__isnull=False).distinct().select_related("site_person"),
            "actor": actor,
        }
    )
    template = "backoffice/partials/activity_table.html" if request.htmx and request.htmx.target == "table" else "backoffice/activity.html"
    return render(request, template, context)
