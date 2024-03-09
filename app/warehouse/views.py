from django.shortcuts import render
from .models import *

def warehouse(request):
    tags = Tag.objects.all()
    items = Item.objects.all()
    return render(request, "warehouse.html", locals())