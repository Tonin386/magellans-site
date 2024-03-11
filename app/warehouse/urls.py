from django.urls import path
from .views import *

urlpatterns = [
    path("", warehouse, name="warehouse"),
    path("objet/<int:pk>/", ItemDetailView.as_view(), name="item-detail"),
]