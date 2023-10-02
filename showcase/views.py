from .models import Site, Category, Section
from django.views.generic import DetailView
from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html', locals())

class CategoryDetailView(DetailView):
    model = Category
    template_name = "category_detail.html"
    context_object_name = "category_detail"