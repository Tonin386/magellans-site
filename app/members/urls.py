from django.urls import path
from .views import *

urlpatterns = [
    path('', members, name='members'),
    path('<int:pk>/', MemberDetailView.as_view(), name='member-detail'),
    path('mon-profil', my_profile, name="my-profile"),
    path('inscription/', register, name="register"),
    path('activation-reussie', activation_done, name="activation_done"),
    path('activation-echec', activation_failed, name='activation_failed')
]