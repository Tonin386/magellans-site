from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("time", "title", "application", "status", "user")
    list_filter = ("application", "status")

    def has_add_permission(self, request):
        return False
