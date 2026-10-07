from django import forms

from core.antispam import AntiSpamFormMixin
from core.forms import StyledFormMixin


class ContactForm(StyledFormMixin, AntiSpamFormMixin, forms.Form):
    name = forms.CharField(label="Ton nom", max_length=100, widget=forms.TextInput(attrs={"autocomplete": "name"}))
    email = forms.EmailField(label="Ton e-mail", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    phone = forms.CharField(
        label="Téléphone", max_length=20, required=False, widget=forms.TextInput(attrs={"autocomplete": "tel", "type": "tel"})
    )
    subject = forms.ChoiceField(
        label="Sujet",
        choices=[
            ("question", "Une question sur l'association"),
            ("membership", "Adhésion"),
            ("project", "Un projet, une captation, un partenariat"),
            ("warehouse", "Le magasin de matériel"),
            ("other", "Autre chose"),
        ],
    )
    message = forms.CharField(
        label="Ton message", max_length=5000, widget=forms.Textarea(attrs={"rows": 6, "placeholder": "Raconte-nous…"})
    )
