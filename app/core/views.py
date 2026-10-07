"""Vues techniques : fichiers privés, robots.txt, plan du site, manifeste, santé."""

from django.conf import settings
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from dashboard.models import Project

from .models import Page, SiteSettings
from .private_files import serve_private_file


def private_file(request, model, pk, field):
    return serve_private_file(request, model, pk, field)


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /espace-ca/",
        "Disallow: /membres/",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /prive/",
        f"Sitemap: {settings.SITE_URL}{reverse('sitemap')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


@require_GET
@cache_page(60 * 30)
def sitemap_xml(request):
    urls = [reverse("home"), reverse("films"), reverse("join"), reverse("warehouse:catalogue")]
    urls += [project.get_absolute_url() for project in Project.objects.filter(public=True)]
    urls += [page.get_absolute_url() for page in Page.objects.filter(is_published=True)]
    body = "".join(f"<url><loc>{settings.SITE_URL}{url}</loc></url>" for url in urls)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'
    return HttpResponse(xml, content_type="application/xml")


@require_GET
def webmanifest(request):
    site = SiteSettings.load()
    return JsonResponse(
        {
            "name": site.site_name,
            "short_name": site.site_name,
            "description": site.tagline,
            "lang": "fr",
            "start_url": reverse("members:home"),
            "display": "standalone",
            "background_color": "#0b0907",
            "theme_color": "#0b0907",
            "icons": [
                {"src": static("img/icon-192.png"), "sizes": "192x192", "type": "image/png"},
                {"src": static("img/icon-512.png"), "sizes": "512x512", "type": "image/png"},
                {"src": static("img/icon-maskable-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
            ],
        },
        content_type="application/manifest+json",
    )


@require_GET
def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")


@require_GET
def abuseipdb_verification(request):
    # Fichier de vérification du compte AbuseIPDB (outil de sécurité du serveur).
    return HttpResponse("abuseipdb-verification-hEjoe0pn", content_type="text/plain")


def coming_soon(request, *args, **kwargs):  # pragma: no cover - échafaudage temporaire
    return HttpResponse("Bientôt disponible", content_type="text/plain")
