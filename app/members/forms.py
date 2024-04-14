from django import forms
from .models import *
from django_registration.forms import RegistrationFormTermsOfService
from django_registration.validators import TOS_REQUIRED
class LogoutForm(forms.Form):
    pass

class RegisterForm(RegistrationFormTermsOfService):
    first_name = forms.CharField(label="Prénom")
    last_name = forms.CharField(label="Nom")
    gender = forms.ChoiceField(label="Sexe", choices=GENDER_CHOICES)
    phone = forms.CharField(label="Téléphone")
    class Meta:
        model = Member
        fields = [
            'email'
        ]
        
    def save(self, commit=True):
        return super(RegisterForm, self).save(commit=commit)
    
class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Prénom")
    last_name = forms.CharField(label="Nom")
    gender = forms.ChoiceField(label="Sexe", choices=GENDER_CHOICES)
    phone = forms.CharField(label="Téléphone")

    def __init__(self, instance=None, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control', 'placeholder': self.fields[field_name].label})
        
        if instance:
            self.fields['first_name'].widget.attrs.update({"value": instance.first_name})
            self.fields['last_name'].widget.attrs.update({"value": instance.last_name})
            self.fields['phone'].widget.attrs.update({"value": instance.phone})
            self.fields['gender'].widget.attrs.update({"value": instance.gender})

    class Meta:
        model = Person
        fields = [
            'first_name', 
            'last_name', 
            'phone', 
            'gender'
        ]

class EditPersonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditPersonForm, self).__init__(*args, **kwargs)
        instance = kwargs.pop('instance', None)
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control', 'placeholder': self.fields[field_name].label})

        if instance:
            self.fields['first_name'].widget.attrs.update({"value": instance.first_name})
            self.fields['last_name'].widget.attrs.update({"value": instance.last_name})
            self.fields['phone'].widget.attrs.update({"value": instance.phone})
            self.fields['gender'].widget.attrs.update({"value": instance.gender})
            self.fields['email'].widget.attrs.update({"value": instance.email})

    class Meta:
        model = Person
        fields = [
            'first_name', 
            'last_name', 
            'phone', 
            'gender',
            'email'
        ]