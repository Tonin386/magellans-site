from django.shortcuts import render
from .models import Operation

def bank(request):
    operations = Operation.objects.all()
    return render(request, "bank.html", locals())
