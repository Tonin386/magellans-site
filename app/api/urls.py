from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    # URL historique (configurée sur HelloAsso) : chaque commande est revérifiée auprès de l'API.
    path("helloasso", views.helloasso_webhook, name="helloasso"),
    path("helloasso/", views.helloasso_webhook),
    # URL recommandée, avec secret : https://magellans.fr/api/helloasso/<secret>/
    path("helloasso/<str:secret>/", views.helloasso_webhook, name="helloasso-secret"),
]
