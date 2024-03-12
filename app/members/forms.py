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
    
class EditProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
                        
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'phone', 'gender']