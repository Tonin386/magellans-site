"""Petites fonctions utilitaires partagées."""

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

PHONE_DIGITS = re.compile(r"\D+")


def normalize_phone(value):
    """Nettoie un numéro saisi librement (espaces, points, tirets)."""
    value = (value or "").strip()
    if not value:
        return ""
    prefix = "+" if value.startswith("+") else ""
    digits = PHONE_DIGITS.sub("", value)
    if prefix and digits.startswith("33") and len(digits) == 11:
        return "+33" + digits[2:]
    return prefix + digits


def format_phone(value):
    """Affichage lisible : « 06 12 34 56 78 » ou « +33 6 12 34 56 78 »."""
    value = normalize_phone(value)
    if not value or value.lower() in {"indéfini", "non-renseigné"}:
        return ""
    if re.fullmatch(r"0\d{9}", value):
        return " ".join(value[i : i + 2] for i in range(0, 10, 2))
    if re.fullmatch(r"\+33\d{9}", value):
        rest = value[3:]
        return "+33 " + rest[0] + " " + " ".join(rest[i : i + 2] for i in range(1, 9, 2))
    return value


def to_decimal(value, default=Decimal("0")):
    """Convertit un montant (float, str, Decimal) en Decimal arrondi au centime."""
    if value is None or value == "":
        return default
    try:
        amount = Decimal(str(value).replace(",", ".").replace(" ", ""))
    except (InvalidOperation, ValueError):
        return default
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_money(value, signed=False):
    """« 1 234,50 € » (espace fine insécable comme séparateur de milliers)."""
    amount = to_decimal(value)
    sign = ""
    if amount < 0:
        sign = "−"
        amount = -amount
    elif signed and amount > 0:
        sign = "+"
    integer, _, cents = f"{amount:.2f}".partition(".")
    groups = []
    while integer:
        groups.insert(0, integer[-3:])
        integer = integer[:-3]
    return f"{sign}{' '.join(groups) or '0'},{cents} €"


def optimize_image(uploaded_file, max_size=1600, quality=82, fmt="WEBP"):
    """Redimensionne et convertit une image envoyée (WebP par défaut).

    Retourne un ``ContentFile`` nommé, ou ``None`` si le fichier n'est pas une image.
    L'orientation EXIF est appliquée puis les métadonnées sont supprimées
    (pas de coordonnées GPS publiées par erreur).
    """
    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as img:
            img = ImageOps.exif_transpose(img)
            if fmt.upper() in {"WEBP", "PNG"}:
                img = img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else img.convert("RGB")
            else:
                img = img.convert("RGB")
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            options = {"quality": quality}
            if fmt.upper() == "WEBP":
                options["method"] = 6
            img.save(buffer, format=fmt, **options)
    except (UnidentifiedImageError, OSError, ValueError):
        return None
    base = (getattr(uploaded_file, "name", "") or "image").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    extension = {"WEBP": "webp", "PNG": "png", "JPEG": "jpg"}[fmt.upper()]
    return ContentFile(buffer.getvalue(), name=f"{base or 'image'}.{extension}")


def client_ip(request):
    """Adresse IP du visiteur (nginx transmet X-Real-IP)."""
    forwarded = request.META.get("HTTP_X_REAL_IP") or request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "")
    return ip or None
