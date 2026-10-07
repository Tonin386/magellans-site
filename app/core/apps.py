from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"
    verbose_name = "Site & contenus"

    def ready(self):
        from core.permissions import has_capability
        from core.private_files import register_private_file

        from .models import SiteSettings

        register_private_file(
            SiteSettings,
            "contract_signature",
            lambda user, obj: has_capability(user, "warehouse") or has_capability(user, "content"),
        )
