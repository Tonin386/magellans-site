from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from core.forms import DOCUMENT_EXTENSIONS, StyledFormMixin, validate_upload
from dashboard.models import Project

from .models import OPERATION_CATEGORIES, Expense, Invoice, Operation


class InvoiceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["title", "project", "role", "comm"]
        labels = {
            "title": "Intitulé de la note de frais",
            "project": "Projet concerné",
            "role": "Ton rôle sur le projet",
            "comm": "Commentaire pour la trésorerie",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex. Tournage « La Noyade » — régie"}),
            "comm": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.order_by("name")
        self.fields["project"].empty_label = "Choisis un projet…"
        self.fields["project"].help_text = "Ton projet n'apparaît pas ? Écris à la trésorerie."
        self.fields["role"].required = True


class ExpenseForm(StyledFormMixin, forms.ModelForm):
    amount = forms.DecimalField(label="Montant (€)", min_value=0.01, max_digits=9, decimal_places=2)

    class Meta:
        model = Expense
        fields = ["title", "date", "amount", "proof", "comm"]
        labels = {"title": "Dépense", "date": "Date", "proof": "Justificatif", "comm": "Précisions"}
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "comm": forms.TextInput(attrs={"placeholder": "Facultatif"}),
            "proof": forms.ClearableFileInput(attrs={"accept": ".pdf,image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["proof"].help_text = "Facture ou ticket détaillé (PDF ou photo). Un ticket de carte bancaire n'est pas un justificatif."

    def clean_proof(self):
        return validate_upload(self.cleaned_data.get("proof"), extensions=DOCUMENT_EXTENSIONS)


class BaseExpenseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        valid = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        if not valid:
            raise forms.ValidationError("Ajoute au moins une dépense.")


ExpenseFormSet = inlineformset_factory(
    Invoice,
    Expense,
    form=ExpenseForm,
    formset=BaseExpenseFormSet,
    fk_name="linked_invoice",
    extra=1,
    can_delete=True,
    max_num=40,
)


class ProofUploadForm(StyledFormMixin, forms.Form):
    proof = forms.FileField(label="Justificatif", widget=forms.ClearableFileInput(attrs={"accept": ".pdf,image/*"}))

    def clean_proof(self):
        return validate_upload(self.cleaned_data.get("proof"), extensions=DOCUMENT_EXTENSIONS)


class OperationForm(StyledFormMixin, forms.ModelForm):
    amount = forms.DecimalField(label="Montant (€)", min_value=0.01, max_digits=10, decimal_places=2)

    class Meta:
        model = Operation
        fields = ["date", "type", "category", "amount", "third_party", "desc", "invoice", "attachment"]
        labels = {"desc": "Libellé", "third_party": "Tiers", "invoice": "Note de frais remboursée (facultatif)"}
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "desc": forms.TextInput(),
            "third_party": forms.Select(attrs={"data-searchable": ""}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["invoice"].queryset = Invoice.objects.order_by("-date_created")
        self.fields["invoice"].required = False
        self.fields["category"].choices = OPERATION_CATEGORIES
        self.fields["third_party"].help_text = "La personne ou l'organisation concernée (adhérent·e, fournisseur, partenaire…)."

    def clean_attachment(self):
        return validate_upload(self.cleaned_data.get("attachment"), extensions=DOCUMENT_EXTENSIONS)
