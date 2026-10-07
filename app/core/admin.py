from django.contrib import admin

from .models import ActivityLog, FAQEntry, Message, Page, Service, SiteSettings, TeamMember, TimelineEntry


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role_title", "season", "order", "is_visible")
    list_filter = ("season", "is_visible")


admin.site.register(TimelineEntry)
admin.site.register(Service)
admin.site.register(FAQEntry)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "show_in_footer", "needs_review", "updated_at")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "category", "verb", "message")
    list_filter = ("category", "verb")
    search_fields = ("message", "target_repr")

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "author", "content_type", "object_id", "is_internal")
