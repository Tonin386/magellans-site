from django.contrib import admin

from .models import HelloAssoEvent, Membership, Season


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("label", "start_date", "end_date", "is_current", "registrations_open", "helloasso_form_slug")
    readonly_fields = ("helloasso_org_slug", "helloasso_form_type", "helloasso_form_slug", "last_synced_at")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("person", "season", "status", "source", "amount", "donation", "joined_at")
    list_filter = ("season", "status", "source")
    search_fields = ("person__first_name", "person__last_name", "person__email", "payer_email")
    autocomplete_fields = ("person",)


@admin.register(HelloAssoEvent)
class HelloAssoEventAdmin(admin.ModelAdmin):
    list_display = ("received_at", "event_type", "order_id", "form_slug", "status", "verified", "secret_ok")
    list_filter = ("status", "event_type", "verified")
    readonly_fields = [f.name for f in HelloAssoEvent._meta.fields]
