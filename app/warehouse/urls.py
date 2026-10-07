from django.shortcuts import redirect
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "warehouse"

urlpatterns = [
    path("", views.catalogue, name="catalogue"),
    path("objet/<int:pk>/", views.item_detail, name="item-detail"),
    path("dates/", views.set_dates, name="set-dates"),
    path("demande/", views.cart, name="cart"),
    path("demande/objet/<int:item_pk>/", views.cart_change, name="cart-change"),
    path("demande/resume/", views.cart_panel, name="cart-panel"),
    path("mes-reservations/", views.orders, name="orders"),
    path("commande/<int:pk>/", views.order_detail, name="order-detail"),
    path("commande/<int:pk>/message/", views.order_message, name="order-message"),
    path("commande/<int:pk>/annuler/", views.order_cancel, name="order-cancel"),
    path("commande/<int:pk>/agenda.ics", views.order_ics, name="order-ics"),
    path("commande/<int:pk>/contrat/", views.contract, name="contract"),
    path("commande/<int:pk>/contrat.pdf", views.contract_pdf, name="contract-pdf"),
    path("contrat/verifier/", views.contract_verify, name="contract-verify"),
    # Anciennes adresses
    path("commande/finaliser/<int:pk>/", lambda request, pk: redirect("warehouse:cart", permanent=True)),
    path("objet/modifier/<int:pk>/", RedirectView.as_view(pattern_name="backoffice:item-edit", permanent=True)),
]
