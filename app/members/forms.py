from django import forms
from .models import Member
from django_registration.forms import RegistrationForm

class LogoutForm(forms.Form):
    pass

class RegisterForm(RegistrationForm):
    
    class Meta:
        model = Member
        fields = [
            'email',
            'first_name',
            'last_name',
            'phone',
            'gender'
        ]
        
    def save(self, commit=True):
        return super(RegisterForm, self).save(commit=commit)