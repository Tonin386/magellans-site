from django.contrib import admin
from .models import *

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('time', 'title', 'application', 'status', 'message', 'user', 'extra_field')
    list_filter = ('time', 'title', 'application', 'status', 'user')
    search_fields = ('time', 'title', 'application', 'status', 'message', 'user__site_person__first_name', 'user__site_person__last_name', 'user__site_person__email', 'extra_field')
    ordering = ('-time', 'status', 'user')
    
admin.site.register(Notification, NotificationAdmin)