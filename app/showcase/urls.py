from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('projets/', projects, name="projects"),
    # path('nous-rejoindre/', join_us, name='join-us')
]