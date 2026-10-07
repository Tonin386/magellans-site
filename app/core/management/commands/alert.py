"""Prévient le webmaster par e-mail (utilisé par les tâches automatiques de run.sh).

    python manage.py alert "Titre" "Message"
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.emails import send_templated_email
from members.utils import board_emails


class Command(BaseCommand):
    help = "Envoie une alerte serveur aux webmasters (à défaut, à l'adresse de contact)."

    def add_arguments(self, parser):
        parser.add_argument("title")
        parser.add_argument("message")

    def handle(self, *args, **options):
        recipients = board_emails("W") or [settings.DEFAULT_FROM_EMAIL]
        context = {"title": options["title"], "message": options["message"], "now": timezone.localtime()}
        if not send_templated_email("server_alert", context, recipients):
            raise CommandError("L'alerte n'a pas pu être envoyée.")
        self.stdout.write(self.style.SUCCESS(f"Alerte envoyée à {len(recipients)} destinataire(s)."))
