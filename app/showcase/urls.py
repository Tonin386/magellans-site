from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('contact/', contact, name="contact"),
    path('projets/', projects, name="projects")
]