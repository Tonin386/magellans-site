from django.urls import path
from .views import *

urlpatterns = [
    path('', members, name='members'),
]