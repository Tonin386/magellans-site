from django import forms

from core.antispam import AntiSpamFormMixin, spam_reasons
from core.forms import StyledFormMixin


class ContactForm(StyledFormMixin, AntiSpamFormMixin, forms.Form):
    antispam_min_seconds = 5  # personne n'écrit un message en moins de 5 secondes

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spam_reasons = []

    def clean(self):
        cleaned = super().clean()
        self.spam_reasons = spam_reasons(cleaned.get("name", ""), cleaned.get("message", ""))
        if self.spam_reasons:
            raise forms.ValidationError(
                "Ton message ressemble à un message automatique (liens, publicité…) et n'a pas été envoyé. "
                "Reformule-le sans liens, ou écris-nous directement par e-mail.",
                code="spam",
            )
        return cleaned
