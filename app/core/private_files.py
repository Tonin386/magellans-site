"""Accès contrôlé aux fichiers privés.

Chaque champ fichier privé est déclaré avec une règle d'accès::

    register_private_file(Expense, "proof", lambda user, obj: obj.author_id == user.pk or ...)

Le lien vers un fichier s'obtient avec ``{{ obj|private_url:"proof" }}`` dans
un gabarit ou :func:`private_url` en Python.
"""

import mimetypes
import os
import re
from urllib.parse import quote

from django.apps import apps
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.urls import reverse
from django.utils.http import content_disposition_header

_RULES = {}

# L'ancien site nommait certains fichiers d'après leur type MIME :
# « expense14.data:application/pdf » ou « resource2.vnd.openxmlformats-…sheet ».
LEGACY_DATA_NAME = re.compile(r"(?P<base>[^/]+)\.data:(?P<type>[\w.+-]+)/(?P<subtype>[\w.+-]+)$")
LEGACY_MIME_SUFFIX = re.compile(r"^(?P<base>[^.]+)\.(?P<subtype>vnd\.[\w.+-]+|msword|pdf|zip|octet-stream)$")


def describe_file(name):
    """Type de contenu et nom de téléchargement d'un fichier stocké."""
    match = LEGACY_DATA_NAME.search(name)
    if match:
        content_type = f"{match['type']}/{match['subtype']}"
        base = match["base"]
    else:
        filename = os.path.basename(name)
        match = LEGACY_MIME_SUFFIX.match(filename)
        if match and not mimetypes.guess_type(filename)[0]:
            content_type = f"application/{match['subtype']}"
            base = match["base"]
        else:
            return mimetypes.guess_type(filename)[0] or "application/octet-stream", filename
    extension = mimetypes.guess_extension(content_type) or ""
    if content_type == "application/octet-stream":
        extension = ""
    return content_type, base + extension


def register_private_file(model, field_name, check):
    _RULES[(model._meta.label_lower, field_name)] = check


def private_url(obj, field_name, download=False):
    field_file = getattr(obj, field_name, None)
    if not field_file:
        return ""
    url = reverse(
        "core:private-file",
        kwargs={"model": obj._meta.label_lower, "pk": obj.pk, "field": field_name},
    )
    return url + ("?download=1" if download else "")


def serve_private_file(request, model, pk, field):
    check = _RULES.get((model, field))
    if check is None:
        raise Http404
    if not request.user.is_authenticated:
        raise PermissionDenied
    try:
        model_class = apps.get_model(model)
    except (LookupError, ValueError):
        raise Http404
    obj = model_class._default_manager.filter(pk=pk).first()
    if obj is None:
        raise Http404
    if not check(request.user, obj):
        raise PermissionDenied
    field_file = getattr(obj, field)
    if not field_file:
        raise Http404
    storage = field_file.storage
    if not storage.exists(field_file.name):
        raise Http404("Fichier introuvable sur le serveur.")

    content_type, filename = describe_file(field_file.name)
    inline_types = ("application/pdf", "image/")
    as_attachment = request.GET.get("download") == "1" or not content_type.startswith(inline_types)

    if settings.PRIVATE_MEDIA_SERVER == "nginx":
        response = HttpResponse(content_type=content_type)
        # Les noms peuvent contenir des accents : nginx décode l'adresse encodée.
        response["X-Accel-Redirect"] = settings.PRIVATE_MEDIA_INTERNAL_URL + quote(field_file.name.lstrip("/"))
    else:
        response = FileResponse(storage.open(field_file.name, "rb"), content_type=content_type)
    response["Content-Disposition"] = content_disposition_header(as_attachment, filename)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    # Un fichier téléversé ne doit jamais pouvoir exécuter de script s'il est ouvert dans le navigateur.
    response["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; sandbox"
    return response
