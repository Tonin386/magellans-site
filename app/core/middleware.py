import json

from django.contrib import messages
from django.shortcuts import render

from .models import SiteSettings
from .permissions import has_capability

# Chemins toujours accessibles, même en maintenance.
MAINTENANCE_EXEMPT_PREFIXES = (
    "/static/",
    "/media/",
    "/admin/",
    "/api/",
    "/connexion/",
    "/deconnexion/",
    "/espace-ca/",
    "/sante/",
    "/robots.txt",
)


class MaintenanceModeMiddleware:
    """Affiche une page de maintenance au public quand le CA l'a activée."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith(MAINTENANCE_EXEMPT_PREFIXES):
            site = SiteSettings.load()
            if site.maintenance_mode and not has_capability(request.user, "backoffice"):
                response = render(request, "maintenance.html", {"site": site}, status=503)
                response["Retry-After"] = "3600"
                return response
        return self.get_response(request)


class HtmxMessagesMiddleware:
    """Transforme les messages Django en notifications « toast » pour les requêtes HTMX.

    Lors d'une requête HTMX, la page n'est pas rechargée : les messages sont donc
    transmis dans l'en-tête ``HX-Trigger`` et affichés par le JavaScript.
    """

    TONES = {
        messages.DEBUG: "info",
        messages.INFO: "info",
        messages.SUCCESS: "success",
        messages.WARNING: "warning",
        messages.ERROR: "error",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(request, "htmx", False):
            return response
        # Une redirection HTMX recharge la page : les messages y seront affichés normalement.
        if 300 <= response.status_code < 400 or "HX-Redirect" in response or "HX-Refresh" in response:
            return response
        toasts = [
            {"message": str(message), "tone": self.TONES.get(message.level, "info")}
            for message in messages.get_messages(request)
        ]
        if not toasts:
            return response
        triggers = {}
        if "HX-Trigger" in response:
            try:
                triggers = json.loads(response["HX-Trigger"])
            except ValueError:
                triggers = {response["HX-Trigger"]: None}
        triggers["toast"] = toasts
        response["HX-Trigger"] = json.dumps(triggers)
        return response
