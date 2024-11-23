from django.urls import path
from .views import *

urlpatterns = [
    path("utilisateurs", dashboard_members, name="dashboard-members"),
    path("projets", dashboard_projects, name="dashboard-projects"),
    path("commandes", dashboard_orders, name="dashboard-orders"),
    path("projets/<slug:slug>/", ProjectDetailView.as_view(), name="project-detail")
]