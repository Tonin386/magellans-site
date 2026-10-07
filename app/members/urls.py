from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "members"

urlpatterns = [
    path("", views.home, name="home"),
    path("profil/", views.profile, name="profile"),
    path("mot-de-passe/", views.member_password_change, name="password-change"),
    path("annuaire/", views.directory, name="directory"),
    path("mes-donnees.json", views.export_data, name="export-data"),
    path("supprimer-mon-compte/", views.delete_account, name="delete-account"),
    # Anciennes adresses (liens présents dans d'anciens e-mails)
    path("mon-profil", RedirectView.as_view(pattern_name="members:home", permanent=True)),
    path("profil/<int:pk>/", views.legacy_member_detail),
    path("personne/<int:pk>/", views.legacy_person_detail),
    path("note-de-frais/nouveau", RedirectView.as_view(pattern_name="bank:invoice-create", permanent=True)),
    path("demande-de-financement/nouveau", RedirectView.as_view(pattern_name="funding:create", permanent=True)),
    path("ressources/", RedirectView.as_view(pattern_name="resources:list", permanent=True)),
]
