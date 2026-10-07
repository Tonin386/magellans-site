from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Member, Person, UnregisteredMember


class PersonInline(admin.StackedInline):
    model = Person
    fk_name = "site_profile"
    extra = 0
    fields = ("first_name", "last_name", "phone", "gender", "board_roles", "kind")
    can_delete = False


@admin.register(Member)
class MemberAdmin(UserAdmin):
    ordering = ("-date_joined",)
    list_display = ("email", "full_name", "is_active", "is_staff", "is_superuser", "date_joined", "last_login")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "site_person__first_name", "site_person__last_name")
    readonly_fields = ("date_joined", "last_login", "donation", "account")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Statut", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("date_joined", "last_login")}),
        ("Ancien site", {"classes": ("collapse",), "fields": ("donation", "account")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)
    inlines = [PersonInline]

    @admin.display(description="Nom")
    def full_name(self, obj):
        return obj.get_full_name()


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("display_name", "email", "phone", "kind", "board_roles", "role", "site_profile")
    list_filter = ("kind", "role", "show_in_directory")
    search_fields = ("email", "last_name", "first_name", "organisation_name", "phone")
    autocomplete_fields = ("site_profile",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(UnregisteredMember)
class UnregisteredMemberAdmin(admin.ModelAdmin):
    list_display = ("pk", "__str__")
