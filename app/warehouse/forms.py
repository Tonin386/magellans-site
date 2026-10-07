import datetime

from django import forms
from django.utils import timezone

from core.forms import IMAGE_EXTENSIONS, StyledFormMixin, validate_upload
from core.utils import normalize_phone, optimize_image

from .models import Contract, Item, Tag
from .services import BookingError, validate_dates

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format=DATETIME_FORMAT)


class DatesForm(StyledFormMixin, forms.Form):
    start = forms.DateTimeField(label="Retrait", widget=DateTimeLocalInput(), input_formats=[DATETIME_FORMAT])
    end = forms.DateTimeField(label="Retour", widget=DateTimeLocalInput(), input_formats=[DATETIME_FORMAT])

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start"), cleaned.get("end")
        if start and end:
            try:
                validate_dates(start, end)
            except BookingError as error:
                raise forms.ValidationError(str(error))
        return cleaned

    @staticmethod
    def suggested_initial():
        """Proposition par défaut : vendredi prochain 18 h → lundi 10 h."""
        today = timezone.localdate()
        days_until_friday = (4 - today.weekday()) % 7 or 7
        friday = today + datetime.timedelta(days=days_until_friday)
        start = timezone.make_aware(datetime.datetime.combine(friday, datetime.time(18, 0)))
        end = timezone.make_aware(datetime.datetime.combine(friday + datetime.timedelta(days=3), datetime.time(10, 0)))
        return {"start": start, "end": end}


class CheckoutForm(StyledFormMixin, forms.Form):
    project_name = forms.CharField(
        label="Projet", max_length=255, help_text="Le film ou l'évènement pour lequel tu empruntes ce matériel."
    )
    pickup_first_name = forms.CharField(label="Prénom", max_length=100, required=False)
    pickup_last_name = forms.CharField(label="Nom", max_length=100, required=False)
    pickup_phone = forms.CharField(label="Téléphone", max_length=20, required=False)
    message = forms.CharField(
        label="Message pour l'équipe du magasin",
        required=False,
        max_length=4000,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Précisions, besoins particuliers…"}),
    )
    tos = forms.BooleanField(label="J'ai lu et j'accepte les conditions d'utilisation du magasin.")

    def clean_pickup_phone(self):
        return normalize_phone(self.cleaned_data.get("pickup_phone"))


class ContractInfoForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            "director_name",
            "director_phone",
            "director_email",
            "production_name",
            "production_address",
            "production_phone",
            "production_email",
        ]
        labels = {
            "director_name": "Nom du / de la réalisateur·ice",
            "director_phone": "Téléphone",
            "director_email": "E-mail",
            "production_name": "Nom de la production",
            "production_address": "Adresse (si personne morale)",
            "production_phone": "Téléphone",
            "production_email": "E-mail",
        }


class SignForm(StyledFormMixin, forms.Form):
    signer_name = forms.CharField(label="Ton nom complet", max_length=200)
    signature = forms.CharField(widget=forms.HiddenInput, required=False)
    approve = forms.BooleanField(label="J'ai lu le contrat et j'en accepte les conditions (« lu et approuvé »).")


class ItemForm(StyledFormMixin, forms.ModelForm):
    photo = forms.ImageField(label="Photo", required=False, help_text="Elle sera recadrée et optimisée automatiquement.")
    remove_photo = forms.BooleanField(label="Retirer la photo actuelle", required=False)

    class Meta:
        model = Item
        fields = ["name", "tags", "description", "max_stock", "state", "availability", "buy_price", "owner"]
        widgets = {
            "tags": forms.SelectMultiple(attrs={"data-searchable": ""}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_photo(self):
        return validate_upload(self.cleaned_data.get("photo"), max_size=12 * 1024 * 1024, extensions=IMAGE_EXTENSIONS)

    def save(self, commit=True):
        item = super().save(commit=False)
        if self.cleaned_data.get("remove_photo"):
            item.image = ""
        if commit:
            item.save()
            self.save_m2m()
        upload = self.cleaned_data.get("photo")
        if upload:
            image = optimize_image(upload, max_size=900)
            if image:
                item.image.save(f"objet-{item.pk}.webp", image, save=True)
        return item


class TagForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name", "color"]
        widgets = {"color": forms.TextInput(attrs={"type": "color", "class": "h-11 w-20 cursor-pointer p-1"})}
