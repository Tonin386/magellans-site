from django.contrib import admin

from .models import Contract, Item, Order, OrderLine, Tag


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "max_stock", "state", "availability", "is_archived", "owner")
    list_filter = ("availability", "state", "is_archived", "tags")
    search_fields = ("name", "owner")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color")


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    autocomplete_fields = ("item",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "project_name", "status", "date_start", "date_end", "date_created")
    list_filter = ("status",)
    search_fields = ("pk", "project_name", "user__email", "user__site_person__last_name")
    inlines = [OrderLineInline]
    readonly_fields = ("quantities", "answer_message")


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("order", "director_name", "production_name", "signed_at", "sha256")
    readonly_fields = ("terms", "signed_at", "signer_ip", "signer_user_agent", "sha256")
