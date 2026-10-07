"""Synchronise les adhésions depuis HelloAsso.

    python manage.py helloasso_sync              # saison en cours
    python manage.py helloasso_sync --all        # toutes les saisons liées à HelloAsso
    python manage.py helloasso_sync --season 2025-2026
    python manage.py helloasso_sync --invite     # envoie aussi les e-mails (invitations, bienvenue)
"""

from django.core.management.base import BaseCommand, CommandError

from memberships.helloasso import HelloAssoError
from memberships.models import Season
from memberships.services import sync_season


class Command(BaseCommand):
    help = "Synchronise les adhésions depuis les campagnes HelloAsso."

    def add_arguments(self, parser):
        parser.add_argument("--season", help="Libellé de la saison (ex. 2026-2027).")
        parser.add_argument("--all", action="store_true", help="Toutes les saisons liées à HelloAsso.")
        parser.add_argument("--invite", action="store_true", help="Envoyer les e-mails (invitations, bienvenue).")

    def handle(self, *args, **options):
        if options["all"]:
            seasons = [s for s in Season.objects.order_by("start_date") if s.has_helloasso]
        elif options["season"]:
            seasons = list(Season.objects.filter(label=options["season"]))
            if not seasons:
                raise CommandError(f"Saison inconnue : {options['season']}")
        else:
            current = Season.current()
            if current is None:
                raise CommandError("Aucune saison en cours.")
            seasons = [current]
        for season in seasons:
            try:
                report = sync_season(season, send_emails=options["invite"])
            except HelloAssoError as error:
                self.stderr.write(self.style.ERROR(f"{season.label} : {error}"))
                continue
            self.stdout.write(self.style.SUCCESS(f"{season.label} : {report.summary()}"))
            for warning in season.helloasso_warnings():
                self.stdout.write(self.style.WARNING(f"  ⚠ {warning}"))
