from django.urls import path
from .views import *

urlpatterns = [
    path('', home_public, name='home'),
    path('preview/', home, name='home_preview'),
    path('contact/', contact, name="contact"),
    path('projets/', projects, name="projects"),
    path('nous-rejoindre/', join_us, name='join-us')
]