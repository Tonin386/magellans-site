from django import forms
from .models import *

class CreateOperationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreateOperationForm, self).__init__(*args, **kwargs)
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control my-1 col-lg-12', 'placeholder': self.fields[field_name].label})
            if field_name in ['type', 'third_party']:
                self.fields[field_name].widget.attrs.update({'style': 'width:100%;','class': 'form-control my-1 col-lg-12', 'placeholder': self.fields[field_name].label})


    class Meta:
        model = Operation
        fields = ['desc', 'type', 'third_party', 'amount', 'date']
        widgets = {
            'desc': forms.Textarea(attrs={'rows': 5}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'})
        }

class CreateInvoiceForm(forms.ModelForm):
    expenses_ids = forms.HiddenInput()
    
    def __init__(self, *args, **kwargs):
        super(CreateInvoiceForm, self).__init__(*args, **kwargs)
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control', 'placeholder': self.fields[field_name].label, 'required': True})

        self.fields['project'].widget.attrs.update({'style': 'padding: 0'})

    class Meta:
        model = Invoice
        fields = ['title', 'project', 'role', 'comm']
        

class CreateExpenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreateExpenseForm, self).__init__(*args, **kwargs)
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control my-1 col-lg-12', 'placeholder': self.fields[field_name].label})

    class Meta:
        model = Expense
        fields = ['title', 'date', 'comm', 'amount', 'proof']
