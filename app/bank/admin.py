from django.contrib import admin
from .models import *

class OperationAdmin(admin.ModelAdmin):
    list_display = ('date', 'type', 'id', 'amount', 'desc', 'third_party')
    list_filter = ('type', 'third_party')
    search_fields = ('date', 'type', 'id', 'amount', 'desc', 'third_party__email', 'third_party__first_name', 'third_party__last_name')
    ordering = ('-date', 'type', 'id', 'amount')
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'title', 'project', 'author', 'role', 'status')
    list_filter = ('date_created', 'project', 'author', 'role', 'status')
    search_fields = ('author__site_person__first_name', 'author__site_person__last_name', 'author__site_person__email', 'title', 'role', 'status', 'project__name')
    ordering = ('date_created', )
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'date', 'title', 'amount', 'author')
    list_filter = ('date_created', 'date', 'author')
    search_fields = ('author__site_person__first_name', 'author__site_person__last_name', 'author__site_person__email', 'title', 'amount')
    ordering = ('date_created', 'date')

admin.site.register(Operation, OperationAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Expense, ExpenseAdmin)