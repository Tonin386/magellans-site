from django.urls import path
from .views import *

urlpatterns = [
    path("bank", api_bank, name="api-bank"),
    path("dashboard", api_dashboard, name="api-dashboard"),
    path("members", api_members, name="api-members"),
    path("warehouse", api_warehouse, name="api-warehouse"),
]