from django.contrib import admin
from .models import *

class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'now_available', 'max_stock', 'availability', 'owner')
    list_filter = ('availability', )
    search_fields = ('name', 'now_available', 'max_stock', 'availability', 'owner')
    ordering = ('name', 'now_available', 'max_stock', 'availability', 'tags')
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name', 'color')
    ordering = ('name', 'color')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'status', 'date_start', 'date_end', 'user')
    list_filter = ('status', 'user')
    search_fields = ('__all__',)
    ordering = ('date_start', 'status')

admin.site.register(Item, ItemAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Order, OrderAdmin)