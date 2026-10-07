"""Stockage des fichiers privés.

Les fichiers sensibles (justificatifs de dépenses, dossiers de demande d'aide,
contrats signés, ressources réservées aux membres…) sont rangés hors du dossier
``media`` public et ne sont servis que par :func:`core.views.private_file`,
après vérification des droits.
"""

import os
import uuid

from django.core.files.storage import FileSystemStorage, storages
from django.utils.text import slugify


class MediaStorage(FileSystemStorage):
    """Stockage disque qui accepte les chemins de l'ancien site.

    Certains fichiers étaient enregistrés avec une barre initiale
    (``/img/items/12.jpg``) que Django refuse par sécurité. La barre est retirée à
    la lecture : la base n'est pas modifiée et ``safe_join`` continue d'interdire
    toute sortie du dossier.
    """

    def path(self, name):
        return super().path(name.lstrip("/"))


def private_storage():
    return storages["private"]


def random_filename(filename, prefix=""):
    """Nom de fichier non devinable qui conserve un nom lisible et l'extension."""
    base, ext = os.path.splitext(os.path.basename(filename))
    readable = slugify(base)[:40] or "fichier"
    token = uuid.uuid4().hex[:10]
    return f"{prefix}{readable}-{token}{ext.lower()}"


def upload_to(directory):
    """Fabrique une fonction ``upload_to`` sérialisable pour les migrations."""
    return UploadTo(directory)


class UploadTo:
    def __init__(self, directory):
        self.directory = directory.rstrip("/")

    def __call__(self, instance, filename):
        return f"{self.directory}/{random_filename(filename)}"

    def deconstruct(self):
        return ("core.storage.UploadTo", (self.directory,), {})

    def __eq__(self, other):
        return isinstance(other, UploadTo) and other.directory == self.directory
