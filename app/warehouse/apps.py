from django.apps import AppConfig


class WarehouseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "warehouse"
    verbose_name = "Magasin"

    def ready(self):
        from core.permissions import has_capability
        from core.private_files import register_private_file

        from .models import Contract

        def can_see_contract(user, contract):
            return contract.order.user_id == user.pk or has_capability(user, "warehouse")

        register_private_file(Contract, "pdf", can_see_contract)
        register_private_file(Contract, "signature_image", can_see_contract)
