"""Réponses HTTP adaptées aux requêtes HTMX."""

from django.shortcuts import redirect, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django_htmx.http import HttpResponseClientRedirect


def smart_redirect(request, to, *args, **kwargs):
    """Redirection classique, ou rechargement complet de page pour une requête HTMX."""
    if getattr(request, "htmx", False):
        return HttpResponseClientRedirect(resolve_url(to, *args, **kwargs))
    return redirect(to, *args, **kwargs)


def safe_next(request, default=None):
    """Adresse de retour (paramètre ``next``) si elle reste sur le site, sinon ``default``."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return default
