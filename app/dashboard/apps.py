from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
    verbose_name = "Projets & ressources"

    def ready(self):
        from core.permissions import has_capability
        from core.private_files import register_private_file

        from .models import ProjectFundingRequest, ResourceFile

        def can_see_funding(user, request):
            return request.asker_id == user.pk or has_capability(user, "funding")

        for field in ("script", "intention_note", "previsional_budget_plan", "contact_list"):
            register_private_file(ProjectFundingRequest, field, can_see_funding)
        register_private_file(ResourceFile, "associated_file", lambda user, resource: user.is_authenticated)
