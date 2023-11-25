from django.contrib import admin
from django import forms
from .models import *

class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        exclude = ['slug']
        
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm

admin.site.register(Site)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Section)