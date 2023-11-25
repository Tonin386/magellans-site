from django.urls import path
from .views import *

urlpatterns = [
    path("", warehouse, name="warehouse"),
]