from django.views.generic import DetailView
from .forms import CreateOperationForm
from django.contrib import messages
from django.shortcuts import render
from .models import *

def bank(request):
    operations = Operation.objects.all()
    invoices = Invoice.objects.all()
    account_money = 0
    for operation in operations:
        if operation.type == 'C':
            account_money += operation.amount
        else:
            account_money -= operation.amount

    account_money = '"+%.2f" % account_money' if account_money > 0 else ("%.2f" % account_money)
    operation_form = CreateOperationForm()
    if request.method == "POST":
        operation_form = CreateOperationForm(request.POST)
        if operation_form.is_valid():
            operation_form.save()
            messages.success(request, 'Opération ajoutée.')
        else:
            messages.error(request, "Erreur lors de l'ajout de l'opération.")

            #success message
    return render(request, "bank.html", locals())

class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = "invoice_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        expenses = self.object.expense_set.all()
        
        context['expenses'] = expenses

        return context