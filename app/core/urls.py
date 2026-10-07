from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("prive/<str:model>/<str:pk>/<str:field>/", views.private_file, name="private-file"),
]
