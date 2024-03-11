from django.views.generic import DetailView
from django.shortcuts import render
from .models import *

def warehouse(request):
    tags = Tag.objects.all().order_by('name')
    items = Item.objects.all().order_by('name')
    return render(request, "warehouse.html", locals())

class ItemDetailView(DetailView):
    model = Item
    template_name = "item_detail.html"
    context_object_name = 'item'