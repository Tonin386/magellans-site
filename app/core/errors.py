"""Pages d'erreur personnalisées."""

from django.shortcuts import render
from django.template.loader import get_template


def page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def server_error(request):
    # Rendu minimal : pas de base de données ni de processeur de contexte.
    from django.http import HttpResponseServerError

    return HttpResponseServerError(get_template("errors/500.html").render())
