"""Aligne l'historique des migrations d'une base existante sur les migrations de référence.

Avant la refonte 2026, les fichiers de migration n'étaient pas versionnés : chaque
serveur générait les siens (``makemigrations`` en production). Les noms enregistrés
dans la table ``django_migrations`` de la production ne correspondent donc pas à
ceux du dépôt.

Cette commande :

1. vérifie que le schéma réel de la base contient bien toutes les tables et colonnes
   décrites par les migrations de référence (``0001_initial``…) ;
2. sauvegarde les anciennes lignes de ``django_migrations`` dans un fichier JSON ;
3. remplace ces lignes par les migrations de référence, marquées comme appliquées.

Elle ne modifie AUCUNE table de données : uniquement la table interne
``django_migrations``, dans une transaction. On lance ensuite ``migrate`` normalement.

Usage ::

    python manage.py baseline_migrations            # diagnostic (aucune modification)
    python manage.py baseline_migrations --apply    # application
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone

BASELINE = {
    "members": ["0001_initial"],
    "warehouse": ["0001_initial"],
    "dashboard": ["0001_initial", "0002_initial"],
    "bank": ["0001_initial", "0002_initial"],
    "api": ["0001_initial", "0002_initial"],
}
NEW_APPS = ["core", "memberships"]


class Command(BaseCommand):
    help = "Aligne l'historique des migrations d'une base existante (refonte 2026)."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Appliquer (sinon simple diagnostic).")
        parser.add_argument(
            "--status",
            action="store_true",
            help="Code de sortie seulement : 0 si la base est prête pour « migrate », 3 si la mise à niveau est requise.",
        )
        parser.add_argument(
            "--backup-dir",
            default=str(Path(settings.BASE_DIR) / "backups"),
            help="Dossier où sauvegarder l'ancien historique (JSON).",
        )

    def handle(self, *args, **options):
        if options["status"]:
            if self.needs_baseline():
                raise SystemExit(3)
            return
        recorder = MigrationRecorder(connection)
        if not recorder.has_table():
            self.stdout.write(self.style.SUCCESS("Base neuve : rien à faire, lancez simplement « migrate »."))
            return

        loader = MigrationLoader(connection, ignore_no_migrations=True)
        applied = recorder.applied_migrations()
        ours = {key for key in applied if key[0] in BASELINE}
        legacy = sorted(key for key in ours if key not in loader.disk_migrations)
        baseline_keys = [(app, name) for app, names in BASELINE.items() for name in names]
        missing_baseline = [key for key in baseline_keys if key not in applied]

        if not ours:
            self.stdout.write(self.style.SUCCESS("Aucune migration de l'application enregistrée : lancez « migrate »."))
            return
        if not legacy and not missing_baseline:
            self.stdout.write(self.style.SUCCESS("L'historique est déjà aligné : lancez « migrate »."))
            return

        self.stdout.write(f"Anciennes migrations enregistrées à remplacer : {len(legacy)}")
        for app, name in legacy:
            self.stdout.write(f"  - {app}.{name}")

        problems = self.check_schema(loader)
        tables = connection.introspection.table_names()
        unexpected = [table for table in tables if table.split("_")[0] in NEW_APPS]
        if unexpected:
            problems.append(f"Des tables des nouvelles applications existent déjà : {', '.join(unexpected)}")
        if problems:
            for problem in problems:
                self.stderr.write(self.style.ERROR(f"✗ {problem}"))
            raise CommandError(
                "Le schéma de la base ne correspond pas aux migrations de référence : aucune modification faite."
            )
        self.stdout.write(self.style.SUCCESS("✓ Le schéma de la base correspond aux migrations de référence."))

        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Diagnostic uniquement. Relancez avec --apply pour appliquer."))
            return

        backup_dir = Path(options["backup_dir"])
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"django_migrations-avant-refonte-{timezone.now():%Y%m%d-%H%M%S}.json"
        rows = list(recorder.migration_qs.order_by("id").values("id", "app", "name", "applied"))
        backup_file.write_text(json.dumps(rows, default=str, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(f"Ancien historique sauvegardé dans {backup_file}")

        with transaction.atomic():
            for app, name in legacy:
                recorder.migration_qs.filter(app=app, name=name).delete()
            for app, name in baseline_keys:
                if not recorder.migration_qs.filter(app=app, name=name).exists():
                    recorder.record_applied(app, name)
        self.stdout.write(
            self.style.SUCCESS("✓ Historique aligné. Étape suivante : « python manage.py migrate ».")
        )

    def needs_baseline(self):
        """Vrai si la base contient l'historique de migrations de l'ancien site."""
        recorder = MigrationRecorder(connection)
        if not recorder.has_table():
            return False
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        applied = recorder.applied_migrations()
        ours = [key for key in applied if key[0] in BASELINE]
        if not ours:
            return False
        legacy = [key for key in ours if key not in loader.disk_migrations]
        missing = [(app, name) for app, names in BASELINE.items() for name in names if (app, name) not in applied]
        return bool(legacy or missing)

    def check_schema(self, loader):
        """Vérifie que tables et colonnes attendues par les migrations de référence existent."""
        problems = []
        nodes = [(app, names[-1]) for app, names in BASELINE.items()]
        state = loader.project_state(nodes=nodes, at_end=True)
        historical_apps = state.apps
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))
            for app_label in BASELINE:
                for model in historical_apps.get_app_config(app_label).get_models():
                    table = model._meta.db_table
                    if table not in tables:
                        problems.append(f"Table manquante : {table}")
                        continue
                    columns = {col.name for col in connection.introspection.get_table_description(cursor, table)}
                    for field in model._meta.local_concrete_fields:
                        if field.column not in columns:
                            problems.append(f"Colonne manquante : {table}.{field.column}")
                    for field in model._meta.local_many_to_many:
                        through = field.remote_field.through._meta.db_table
                        if through not in tables:
                            problems.append(f"Table de liaison manquante : {through}")
        return problems
