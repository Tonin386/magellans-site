from members.decorators import staff_required
from django.views.generic import DetailView
from .forms import CreateOperationForm
from django.contrib import messages
from django.shortcuts import render
from .models import *

@staff_required("Trésorerie", "Page de gestion de la trésorerie de l'association Magellans.")
def bank(request):
    title = request.title
    og_description = request.og_description
    operations = Operation.objects.all()
    invoices = Invoice.objects.all()
    account_money = 0
    for operation in operations:
        if operation.type == 'C':
            account_money += operation.amount
        else:
            account_money -= operation.amount

    account_money = ("+%.2f" % account_money) if account_money > 0 else ("%.2f" % account_money)
    operation_form = CreateOperationForm()
    if request.method == "POST":
        operation_form = CreateOperationForm(request.POST)
        if operation_form.is_valid():
            if request.user.site_person.role in ['P', 'T'] or request.user.is_superuser:
                operation_form.save()
                messages.success(request, 'Opération ajoutée.')
            else:
                messages.error(request, "Vous n'avez pas les permissions suffisantes pour gérer les opérations de trésorerie.<br>Seuls les Prédsident.e et Trésorier.ère peuvent les gérer.")
        else:
            messages.error(request, "Erreur lors de l'ajout de l'opération.")

    return render(request, "bank.html", locals())

class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = "invoice_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        expenses = self.object.expense_set.all()
        
        context['expenses'] = expenses
        context['title'] = f"Note de frais { self.object.title }"
        context['og_description'] = "Page détaillant une note de frais pour l'association Magellans."

        return context