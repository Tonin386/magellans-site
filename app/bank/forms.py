from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from core.forms import DOCUMENT_EXTENSIONS, StyledFormMixin, validate_upload
from dashboard.models import Project

from .models import OPERATION_CATEGORIES, Expense, Invoice, Operation


NEW_PROJECT_PREFIX = "nouveau:"


class ProjectChoiceField(forms.ModelChoiceField):
    """Projet existant, ou titre d'un projet à créer (valeur « nouveau:Titre » saisie dans la liste)."""

    def to_python(self, value):
        if isinstance(value, str) and value.startswith(NEW_PROJECT_PREFIX):
            name = " ".join(value.removeprefix(NEW_PROJECT_PREFIX).split())
            if len(name) < 2:
                raise forms.ValidationError("Indique le titre du projet.")
            if len(name) > 255:
                raise forms.ValidationError("Titre trop long (255 caractères maximum).")
            # Un projet du même nom existe déjà : on le réutilise plutôt que de créer un doublon.
            return Project.objects.filter(name__iexact=name).first() or Project(name=name, desc="")
        return super().to_python(value)


class InvoiceForm(StyledFormMixin, forms.ModelForm):
    # Champ hors Meta.fields : le projet peut être à créer, il est rattaché dans save().
    project = ProjectChoiceField(
        queryset=Project.objects.order_by("name"),
        label="Projet concerné",
        empty_label="Choisis ou crée ton projet…",
        help_text="Ton projet n'est pas dans la liste ? Tape son titre puis choisis « Créer le projet ».",
        error_messages={"required": "Choisis le projet concerné, ou crée-le."},
        widget=forms.Select(
            attrs={
                "data-searchable": "",
                "data-create": "",
                "data-create-prefix": NEW_PROJECT_PREFIX,
                "data-create-label": "Créer le projet",
            }
        ),
    )

    class Meta:
        model = Invoice
        fields = ["title", "role", "comm"]
        labels = {
            "title": "Intitulé de la note de frais",
            "role": "Ton rôle sur le projet",
            "comm": "Commentaire pour la trésorerie",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex. Tournage « La Noyade » — régie"}),
            "role": forms.TextInput(attrs={"placeholder": "Ex. Régie, réalisation, production…"}),
            "comm": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].required = True
        self.new_project = None
        if self.instance.project_id:
            self.initial.setdefault("project", self.instance.project_id)
        # Après une erreur, le projet à créer reste sélectionné dans la liste.
        pending = self.data.get(self.add_prefix("project"), "") if self.is_bound else ""
        if pending.startswith(NEW_PROJECT_PREFIX):
            field = self.fields["project"]
            field.widget.choices = [*field.choices, (pending, pending.removeprefix(NEW_PROJECT_PREFIX))]

    def save(self, commit=True):
        project = self.cleaned_data["project"]
        if project.pk is None:
            project.save()
            self.new_project = project
        self.instance.project = project
        return super().save(commit)


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
        labels = {"desc": "Libellé", "third_party": "Tiers", "invoice": "Note de frais remboursée"}
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
