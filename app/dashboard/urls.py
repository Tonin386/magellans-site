from django.urls import path
from .views import *

urlpatterns = [
    path("", dashboard_home, name="dashboard-home"),
    path("utilisateurs", dashboard_members, name="dashboard-members"),
    path("projets", dashboard_projects, name="dashboard-projects"),
    path("projets/<slug:slug>/", ProjectDetailView.as_view(), name="project-detail")
]