from django.contrib import admin

from .models import Expense, Invoice, Operation


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "type", "category", "amount", "desc", "third_party")
    list_filter = ("type", "category")
    search_fields = ("id", "desc", "third_party__last_name", "third_party__first_name", "third_party__email")
    autocomplete_fields = ("third_party",)


class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 0
    fk_name = "linked_invoice"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("pk", "date_created", "title", "project", "author", "status", "total")
    list_filter = ("status", "project")
    search_fields = ("title", "author__email", "author__site_person__last_name")
    inlines = [ExpenseInline]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("date", "title", "amount", "author", "linked_invoice")
    search_fields = ("title", "author__email")
