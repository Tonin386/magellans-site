from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path("<slug:slug>", CategoryDetailView.as_view(), name="category-detail"),
]