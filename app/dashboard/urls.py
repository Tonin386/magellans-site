from django.urls import path
from .views import *

urlpatterns = [
    path("", dashboard_home, name="dashboard"),
]