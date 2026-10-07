"""Contrats de prêt : génération du PDF (WeasyPrint), signature et vérification.

La signature électronique « simple » repose sur :
- l'identification de la personne (compte connecté),
- son consentement explicite (case « lu et approuvé » + nom saisi + signature manuscrite),
- l'horodatage, l'adresse IP et le navigateur enregistrés,
- l'empreinte SHA-256 du PDF final et un code de vérification lié à la clé secrète du site.
"""

import base64
import binascii
import hashlib
import hmac
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

from core.audit import log_activity
from core.emails import send_templated_email
from core.models import SiteSettings

from .models import Contract, OrderStatus
from .services import BookingError, warehouse_recipients

MAX_SIGNATURE_BYTES = 600 * 1024


def current_terms():
    site = SiteSettings.load()
    return {
        "association": site.site_name.upper(),
        "address": site.full_address,
        "rna": site.rna_number,
        "intro": site.contract_intro,
        "commitments": site.contract_commitment_list,
        "counterparts": site.contract_counterpart_list,
        "signatory_name": site.contract_signatory_name,
        "signatory_title": site.contract_signatory_title,
        "pickup_address": site.pickup_address,
        "city": site.city,
    }


def verification_code(contract):
    if not contract.signed_at:
        return ""
    message = f"{contract.pk}:{contract.order_id}:{contract.signed_at.isoformat()}:{contract.signer_name}"
    digest = hmac.new(settings.SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()[:16].upper()
    return "-".join(digest[i : i + 4] for i in range(0, 16, 4))


def find_by_code(code):
    normalized = code.strip().upper().replace(" ", "")
    for contract in Contract.objects.exclude(signed_at=None).select_related("order"):
        if hmac.compare_digest(verification_code(contract), normalized):
            return contract
    return None


def _data_uri(field_file, mime="image/png"):
    if not field_file:
        return ""
    try:
        with field_file.storage.open(field_file.name, "rb") as handle:
            data = handle.read()
    except (FileNotFoundError, OSError):
        return ""
    if field_file.name.lower().endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    elif field_file.name.lower().endswith(".webp"):
        mime = "image/webp"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def render_pdf(contract, *, preview=False):
    """Retourne le PDF du contrat (aperçu non signé ou version finale)."""
    from weasyprint import HTML

    site = SiteSettings.load()
    order = contract.order
    terms = contract.terms if (contract.is_signed and contract.terms) else current_terms()
    lines = [line for line in order.lines.select_related("item") if line.available]
    html = render_to_string(
        "warehouse/contract_pdf.html",
        {
            "contract": contract,
            "order": order,
            "lines": lines,
            "terms": terms,
            "preview": preview,
            "board_signature": _data_uri(site.contract_signature) if not preview else "",
            "member_signature": _data_uri(contract.signature_image) if not preview else "",
            "verification_code": verification_code(contract),
            "verification_url": settings.SITE_URL + reverse("warehouse:contract-verify"),
            "generated_at": timezone.now(),
        },
    )
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()


def decode_signature(data_url):
    """Valide et normalise la signature dessinée (data URL PNG)."""
    prefix = "data:image/png;base64,"
    if not data_url or not data_url.startswith(prefix):
        raise BookingError("Signature manquante : signe dans le cadre prévu.")
    try:
        raw = base64.b64decode(data_url[len(prefix) :], validate=True)
    except (binascii.Error, ValueError):
        raise BookingError("Signature illisible, recommence.")
    if len(raw) > MAX_SIGNATURE_BYTES:
        raise BookingError("Signature trop volumineuse.")
    try:
        with Image.open(BytesIO(raw)) as image:
            image = image.convert("RGBA")
            if image.width < 50 or image.height < 30:
                raise BookingError("Signature trop petite.")
            bbox = image.getbbox()
            if bbox is None:
                raise BookingError("Signature vide : signe dans le cadre prévu.")
            image = image.crop(bbox)
            output = BytesIO()
            image.save(output, format="PNG", optimize=True)
    except (UnidentifiedImageError, OSError):
        raise BookingError("Signature illisible, recommence.")
    return output.getvalue()


@transaction.atomic
def sign(contract, *, signer_name, signature_data_url, ip=None, user_agent="", request=None):
    order = contract.order
    if contract.is_signed:
        raise BookingError("Ce contrat est déjà signé.")
    if order.status not in (OrderStatus.ACCEPTED, OrderStatus.ACCEPTED_MODIFIED):
        raise BookingError("Ce contrat ne peut plus être signé (la réservation a changé de statut).")
    signature_png = decode_signature(signature_data_url)

    contract.signer_name = signer_name.strip()[:200]
    contract.signer_ip = ip
    contract.signer_user_agent = (user_agent or "")[:400]
    contract.signed_at = timezone.now()
    contract.terms = current_terms()
    contract.signature_image.save(f"signature-{order.pk}.png", ContentFile(signature_png), save=False)
    contract.save()

    pdf = render_pdf(contract)
    contract.sha256 = hashlib.sha256(pdf).hexdigest()
    contract.pdf.save(f"contrat-{contract.reference}.pdf", ContentFile(pdf), save=False)
    contract.save()

    order.status = OrderStatus.SIGNED
    order.save(update_fields=["status", "updated_at"])

    log_activity(
        request or order.user,
        "contract-signed",
        f"Contrat {contract.reference} signé par {contract.signer_name}.",
        target=order,
        category="warehouse",
        data={"sha256": contract.sha256},
    )
    attachment = [(f"Contrat {contract.reference}.pdf", pdf, "application/pdf")]
    transaction.on_commit(
        lambda: (
            send_templated_email("contract_signed", {"order": order, "contract": contract}, [order.user.email], attachments=attachment),
            send_templated_email(
                "contract_signed_team", {"order": order, "contract": contract}, warehouse_recipients(), attachments=attachment
            ),
        )
    )
    return contract
