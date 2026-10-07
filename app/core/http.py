"""Réponses HTTP adaptées aux requêtes HTMX."""

from django.shortcuts import redirect, resolve_url
from django_htmx.http import HttpResponseClientRedirect


def smart_redirect(request, to, *args, **kwargs):
    """Redirection classique, ou rechargement complet de page pour une requête HTMX."""
    if getattr(request, "htmx", False):
        return HttpResponseClientRedirect(resolve_url(to, *args, **kwargs))
    return redirect(to, *args, **kwargs)
