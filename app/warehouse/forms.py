from django import forms
from .models import *

class EditItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            max_stock = instance.max_stock
            kwargs.setdefault('initial', {})['now_available'] = max_stock
        super(EditItemForm, self).__init__(*args, **kwargs)
        
        self.fields['image'].widget = forms.FileInput()
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
            
        self.fields['now_available'].widget.attrs.update({'max': max_stock})
    
    class Meta:
        model = Item
        fields = ['name', 'tags', 'image', 'max_stock', 'state', 'buy_price', 'owner', 'availability', 'now_available']
        
class EditTagForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditTagForm, self).__init__(*args, **kwargs)
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
            
        self.fields['color'].widget = forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'})
            
    class Meta:
        model = Tag
        fields = ['name', 'color']
        
class PlaceOrderForm(forms.Form):
    start_date = forms.DateTimeInput()
    end_date = forms.DateTimeInput()
    message = forms.TextInput()
    pks = forms.HiddenInput()
    quantities = forms.HiddenInput()
    pickup_first_name = forms.TextInput()
    pickup_last_name = forms.TextInput()
    pickup_phone = forms.TextInput()
    tos = forms.CheckboxInput()