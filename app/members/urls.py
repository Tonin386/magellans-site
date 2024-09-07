from django.urls import path
from .views import *

urlpatterns = [
    path('', members, name='members'),
    path('profil/<int:pk>/', MemberDetailView.as_view(), name='member-detail'),
    path('personne/<int:pk>/', PersonDetailView.as_view(), name='person-detail'),
    path('mon-profil', my_profile, name="my-profile"),
    path('note-de-frais/nouveau', create_invoice, name="create-invoice"),
    path('demande-de-financement/nouveau', create_funding_request, name="create-funding-request"),
    path('inscription/', register, name="register"),
    path('devenir-membre/', join_magellans, name="join-magellans"),
    path('activation-reussie', activation_done, name="activation_done"),
    path('activation-echec', activation_failed, name='activation_failed'),
    path('activate/<str:uidb64>/<str:token>/', activate, name='activate'),
]