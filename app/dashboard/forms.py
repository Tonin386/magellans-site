from django import forms

from core.forms import StyledFormMixin, validate_upload
from core.models import SiteSettings

from .models import ProjectFundingRequest

FUNDING_EXTENSIONS = ["pdf", "doc", "docx", "odt"]


class FundingRequestForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectFundingRequest
        fields = [
            "name", "role", "directors", "production", "genre", "duration",
            "previsional_shoot_start_date", "previsional_shoot_end_date",
            "funding_value", "explanation",
            "script", "intention_note", "previsional_budget_plan", "contact_list",
        ]
        widgets = {
            "previsional_shoot_start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "previsional_shoot_end_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "explanation": forms.Textarea(attrs={"rows": 6, "placeholder": "Le projet, ce que l'aide permettrait de financer, l'équipe…"}),
            "script": forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx,.odt"}),
            "intention_note": forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx,.odt"}),
            "previsional_budget_plan": forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx,.odt"}),
            "contact_list": forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx,.odt"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_amount = SiteSettings.load().funding_max_amount
        self.fields["funding_value"].help_text = f"Jusqu'à {self.max_amount} €."
        self.fields["funding_value"].widget.attrs["max"] = self.max_amount

    def clean_funding_value(self):
        value = self.cleaned_data["funding_value"]
        if value > self.max_amount:
            raise forms.ValidationError(f"Le montant maximum d'une aide est de {self.max_amount} €.")
        if value <= 0:
            raise forms.ValidationError("Indique un montant positif.")
        return value

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("previsional_shoot_start_date"), cleaned.get("previsional_shoot_end_date")
        if start and end and end < start:
            self.add_error("previsional_shoot_end_date", "La fin du tournage doit être après son début.")
        for field in ("script", "intention_note", "previsional_budget_plan", "contact_list"):
            upload = cleaned.get(field)
            if upload and hasattr(upload, "size"):
                try:
                    validate_upload(upload, extensions=FUNDING_EXTENSIONS)
                except forms.ValidationError as error:
                    self.add_error(field, error)
        return cleaned
