from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import *
from .forms import *

def warehouse(request):
    tags = Tag.objects.all().order_by('name')
    items = Item.objects.all().order_by('name')
    return render(request, "warehouse.html", locals())

class EditItemDetailView(UpdateView):
    model = Item
    form_class = EditItemForm
    template_name = "edit_item_detail.html"
    success_url = reverse_lazy('warehouse')
    
    def get_object(self, queryset=None):
        return Item.objects.get(pk=self.kwargs['pk'])
    
class EditTagDetailView(UpdateView):
    model = Tag
    form_class = EditTagForm
    template_name = "edit_tag_detail.html"
    success_url = reverse_lazy('warehouse')
    
    def get_object(self, queryset=None):
        return Tag.objects.get(pk=self.kwargs['pk'])
    