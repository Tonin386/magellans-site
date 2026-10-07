from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from core import views as core_views

admin.site.site_header = "Magellans — administration technique"
admin.site.site_title = "Magellans"
admin.site.index_title = "Administration technique (webmaster)"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("robots.txt", core_views.robots_txt, name="robots"),
    path("sitemap.xml", core_views.sitemap_xml, name="sitemap"),
    path("site.webmanifest", core_views.webmanifest, name="webmanifest"),
    path("sante/", core_views.health, name="health"),
    path("abuseipdb-verification.html", core_views.abuseipdb_verification),
    path("", include("core.urls")),
    path("", include("members.auth_urls")),
    path("", include("showcase.urls")),
    path("membres/notes-de-frais/", include("bank.urls")),
    path("membres/aides-projets/", include("dashboard.urls_funding")),
    path("membres/ressources/", include("dashboard.urls_resources")),
    path("membres/", include("members.urls")),
    path("magasin/", include("warehouse.urls")),
    path("espace-ca/", include("backoffice.urls")),
    path("api/", include("api.urls")),
    # Anciennes adresses de l'espace d'administration
    path("tresorerie/", RedirectView.as_view(pattern_name="backoffice:finance", permanent=False)),
    path("tresorerie/note-de-frais/<int:pk>/", RedirectView.as_view(pattern_name="bank:invoice-detail", permanent=True)),
    path("dashboard/utilisateurs", RedirectView.as_view(pattern_name="backoffice:people", permanent=False)),
    path("dashboard/projets", RedirectView.as_view(pattern_name="backoffice:projects", permanent=False)),
    path("dashboard/commandes", RedirectView.as_view(pattern_name="backoffice:orders", permanent=False)),
]

handler404 = "core.errors.page_not_found"
handler403 = "core.errors.permission_denied"
handler500 = "core.errors.server_error"

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
