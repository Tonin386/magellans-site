"""Journal d'activité : trace « qui a fait quoi, quand » pour le CA."""

import logging

from django.contrib.contenttypes.models import ContentType

from .utils import client_ip

logger = logging.getLogger("magellans.audit")


def log_activity(actor_or_request, verb, message, *, target=None, category="system", data=None):
    """Enregistre une action. ``actor_or_request`` : requête HTTP, utilisateur ou None."""
    from .models import ActivityLog

    request = actor_or_request if hasattr(actor_or_request, "META") else None
    actor = getattr(request, "user", None) if request is not None else actor_or_request
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None
    entry = ActivityLog(
        actor=actor,
        verb=verb,
        message=message[:2000],
        category=category,
        data=data or {},
        ip_address=client_ip(request) if request is not None else None,
    )
    if target is not None and getattr(target, "pk", None) is not None:
        entry.target_type = ContentType.objects.get_for_model(target)
        entry.target_id = str(target.pk)
        entry.target_repr = str(target)[:255]
    try:
        entry.save()
    except Exception:  # le journal ne doit jamais bloquer une action
        logger.exception("Impossible d'enregistrer l'entrée du journal : %s", message)
    return entry
