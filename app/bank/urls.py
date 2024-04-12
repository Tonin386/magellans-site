from django.urls import path
from .views import *

urlpatterns = [
    path('', bank, name='bank'),
    path('note-de-frais/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
]