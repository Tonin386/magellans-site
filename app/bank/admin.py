from django.contrib import admin
from .models import *

class OperationAdmin(admin.ModelAdmin):
    list_display = ('date', 'type', 'id', 'amount', 'desc', 'src', 'dest', 'status')
    list_filter = ('type', 'status', 'src', 'dest')
    search_fields = ('date', 'type', 'id', 'amount', 'desc', 'src', 'dest', 'status')
    ordering = ('-date', 'type', 'id', 'amount', 'status')

admin.site.register(Operation)