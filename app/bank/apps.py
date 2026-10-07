from django.apps import AppConfig


class BankConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bank"
    verbose_name = "Trésorerie"

    def ready(self):
        from core.permissions import has_capability
        from core.private_files import register_private_file

        from .models import Expense, Operation

        register_private_file(
            Expense, "proof", lambda user, expense: expense.author_id == user.pk or has_capability(user, "finance")
        )
        register_private_file(Operation, "attachment", lambda user, operation: has_capability(user, "finance"))
