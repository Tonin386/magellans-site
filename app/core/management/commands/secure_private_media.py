"""Déplace les fichiers sensibles du dossier public vers le dossier privé.

Avant la refonte, les justificatifs de dépenses, les dossiers de demande d'aide et
les ressources membres étaient servis publiquement par nginx (adresses devinables).
Les chemins enregistrés en base ne changent pas : seuls les fichiers sont déplacés,
de MEDIA_ROOT vers PRIVATE_MEDIA_ROOT (même arborescence).

    python manage.py secure_private_media            # simulation
    python manage.py secure_private_media --apply    # déplacement
"""

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

PRIVATE_DIRECTORIES = ["img/proofs", "funding_requests", "resources", "contracts", "bank"]


class Command(BaseCommand):
    help = "Met à l'abri les fichiers privés (justificatifs, dossiers, ressources)."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Effectuer le déplacement (sinon simulation).")

    def handle(self, *args, **options):
        public_root = Path(settings.MEDIA_ROOT)
        private_root = Path(settings.PRIVATE_MEDIA_ROOT)
        moved = conflicts = 0
        for relative in PRIVATE_DIRECTORIES:
            source_dir = public_root / relative
            if not source_dir.exists():
                continue
            for source in sorted(p for p in source_dir.rglob("*") if p.is_file()):
                target = private_root / source.relative_to(public_root)
                if target.exists():
                    conflicts += 1
                    self.stdout.write(self.style.WARNING(f"Déjà présent, laissé en place : {source.relative_to(public_root)}"))
                    continue
                if options["apply"]:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(target))
                moved += 1
            if options["apply"]:
                # Supprime les dossiers devenus vides (jamais un dossier contenant encore un fichier).
                for directory in sorted((p for p in source_dir.rglob("*") if p.is_dir()), reverse=True):
                    if not any(directory.iterdir()):
                        directory.rmdir()
                if source_dir.exists() and not any(source_dir.iterdir()):
                    source_dir.rmdir()
        verb = "déplacé(s)" if options["apply"] else "à déplacer (simulation : relancer avec --apply)"
        self.stdout.write(self.style.SUCCESS(f"{moved} fichier(s) {verb} vers {private_root}."))
        if conflicts:
            self.stdout.write(self.style.WARNING(f"{conflicts} fichier(s) déjà présents côté privé : à vérifier manuellement."))
