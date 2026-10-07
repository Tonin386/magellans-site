from django.contrib import admin

from .models import Project, ProjectFundingRequest, ResourceFile, RoleMap


class RoleMapInline(admin.TabularInline):
    model = RoleMap
    extra = 0
    autocomplete_fields = ("person",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "genre", "status", "public", "featured", "release_date")
    list_filter = ("public", "featured", "status")
    search_fields = ("name", "genre", "desc")
    inlines = [RoleMapInline]


@admin.register(ProjectFundingRequest)
class ProjectFundingRequestAdmin(admin.ModelAdmin):
    list_display = ("deposit_date", "name", "asker", "funding_value", "status", "granted_amount")
    list_filter = ("status",)
    search_fields = ("name", "asker__email", "directors", "production")


@admin.register(ResourceFile)
class ResourceFileAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "associated_file", "external_url")
