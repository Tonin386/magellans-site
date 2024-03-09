from django.contrib import admin
from .models import *

class ItemAdmin(admin.ModelAdmin):
    pass

class TagAdmin(admin.ModelAdmin):
    pass

admin.site.register(Item, ItemAdmin)
admin.site.register(Tag, TagAdmin)