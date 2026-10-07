from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),
    path("projets/", views.films, name="films"),
    path("projets/<slug:slug>/", views.film_detail, name="film-detail"),
    path("adherer/", views.join, name="join"),
    path("p/<slug:slug>/", views.page, name="page"),
    # Anciennes adresses
    path("dashboard/projets/<slug:slug>/", views.legacy_project_redirect),
    path("membres/devenir-membre/", RedirectView.as_view(pattern_name="join", permanent=True)),
]
