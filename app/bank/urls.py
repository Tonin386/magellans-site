from django.urls import path

from . import views

app_name = "bank"

urlpatterns = [
    path("", views.invoice_list, name="list"),
    path("nouvelle/", views.invoice_create, name="invoice-create"),
    path("<int:pk>/", views.invoice_detail, name="invoice-detail"),
    path("<int:pk>/message/", views.invoice_message, name="invoice-message"),
    path("depense/<int:pk>/justificatif/", views.expense_proof, name="expense-proof"),
]
