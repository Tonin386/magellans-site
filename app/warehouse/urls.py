from django.urls import path
from .views import *

urlpatterns = [
    path("", warehouse, name="warehouse"),
    path("objet/modifier/<int:pk>/", EditItemDetailView.as_view(), name="edit-item-detail"),
    path("tag/modifier/<int:pk>/", EditTagDetailView.as_view(), name="edit-tag-detail"),
]