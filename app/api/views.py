"""Réception des notifications HelloAsso (webhook).

Les notifications HelloAsso ne sont pas signées pour les associations : le contenu
reçu n'est donc jamais cru sur parole. La commande concernée est relue auprès de
l'API officielle HelloAsso (avec nos identifiants) avant d'être enregistrée.
À défaut d'identifiants API, seule l'URL secrète est acceptée.
"""

import hmac
import json
import logging

from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.utils import client_ip
from memberships.helloasso import HelloAssoClient, HelloAssoError
from memberships.models import HelloAssoEvent
from memberships.services import process_order

logger = logging.getLogger("magellans.helloasso")


def _order_id(event_type, data):
    if event_type == "Order":
        return data.get("id")
    if event_type == "Payment":
        return (data.get("order") or {}).get("id")
    return None


@csrf_exempt
@require_POST
def helloasso_webhook(request, secret=None):
    conf = settings.HELLOASSO
    expected = conf.get("WEBHOOK_SECRET") or ""
    secret_ok = bool(expected) and secret is not None and hmac.compare_digest(secret, expected)
    if secret is not None and not secret_ok:
        raise Http404

    try:
        payload = json.loads(request.body or b"{}")
    except ValueError:
        return JsonResponse({"status": "error", "message": "JSON invalide"}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"status": "error", "message": "Contenu inattendu"}, status=400)

    event_type = str(payload.get("eventType") or "")[:40]
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    order_id = _order_id(event_type, data)
    ip = client_ip(request)
    event = HelloAssoEvent.objects.create(
        event_type=event_type,
        order_id=order_id if isinstance(order_id, int) else None,
        form_slug=str(data.get("formSlug") or (data.get("order") or {}).get("formSlug") or "")[:200],
        payload=payload,
        source_ip=ip,
        secret_ok=secret_ok,
    )
    notes = []
    if ip and conf.get("WEBHOOK_IPS") and ip not in conf["WEBHOOK_IPS"]:
        notes.append(f"IP {ip} différente de celles annoncées par HelloAsso.")

    if event_type not in ("Order", "Payment") or not order_id:
        event.status = HelloAssoEvent.Status.IGNORED
        event.result = "Notification sans adhésion à traiter."
        event.save(update_fields=["status", "result"])
        return JsonResponse({"status": "ignored"})

    client = HelloAssoClient()
    verified = False
    if client.configured:
        try:
            order = client.order(order_id)
            verified = True
        except HelloAssoError as error:
            event.status = HelloAssoEvent.Status.ERROR
            event.result = f"Vérification impossible auprès de l'API HelloAsso : {error}"
            event.save(update_fields=["status", "result"])
            logger.warning("Webhook HelloAsso : %s", error)
            # Code 503 : HelloAsso renverra la notification plus tard.
            return JsonResponse({"status": "retry"}, status=503)
    elif secret_ok and event_type == "Order":
        order = data
    else:
        event.status = HelloAssoEvent.Status.REJECTED
        event.result = (
            "Notification non vérifiable : configurez les identifiants de l'API HelloAsso "
            "ou utilisez l'URL secrète du webhook."
        )
        event.save(update_fields=["status", "result"])
        return JsonResponse({"status": "rejected"}, status=403)

    try:
        report = process_order(order, verified=verified)
    except Exception as error:  # on garde une trace exploitable par le CA
        logger.exception("Erreur lors du traitement de la commande HelloAsso %s", order_id)
        event.status = HelloAssoEvent.Status.ERROR
        event.result = f"Erreur interne : {error}"
        event.save(update_fields=["status", "result"])
        return JsonResponse({"status": "error"}, status=500)

    event.verified = verified
    event.status = HelloAssoEvent.Status.PROCESSED if (report.created or report.updated or report.cancelled or report.unchanged) else HelloAssoEvent.Status.IGNORED
    event.result = "; ".join([report.summary(), *report.ignored, *notes])[:2000]
    event.save(update_fields=["verified", "status", "result"])
    return JsonResponse({"status": "ok"})
