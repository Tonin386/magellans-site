from django.views.generic import DetailView
from django.shortcuts import render
from .models import *

def bank(request):
    operations = Operation.objects.all()
    invoices = Invoice.objects.all()
    return render(request, "bank.html", locals())

class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = "invoice_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        expenses = self.object.expense_set.all()
        
        context['expenses'] = expenses

        return context