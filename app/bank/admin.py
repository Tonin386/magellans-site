from django.contrib import admin
from .models import *

class OperationAdmin(admin.ModelAdmin):
    list_display = ('date', 'type', 'id', 'amount', 'desc', 'src', 'dest')
    list_filter = ('type', 'src', 'dest')
    search_fields = ('date', 'type', 'id', 'amount', 'desc', 'src', 'dest')
    ordering = ('-date', 'type', 'id', 'amount')
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'title', 'project', 'author', 'role', 'status')
    list_filter = ('date_created', 'project', 'author', 'role', 'status')
    search_fields = ('__all__', )
    ordering = ('date_created', )
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'date', 'title', 'amount', 'author')
    list_filter = ('date_created', 'date', 'author')
    search_fields = ('__all__', )
    ordering = ('date_created', 'date')

admin.site.register(Operation, OperationAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Expense, ExpenseAdmin)