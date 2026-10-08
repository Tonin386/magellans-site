"""Formulaires de l'espace CA."""

from django import forms
from django.forms import modelform_factory

from bank.models import STATUS as INVOICE_STATUS
from core.forms import IMAGE_EXTENSIONS, StyledFormMixin, validate_upload
from core.models import FAQEntry, Page, Service, SiteSettings, TeamMember, TimelineEntry
from core.permissions import BOARD_ROLES
from core.utils import normalize_phone, optimize_image
from dashboard.models import Project, ProjectFundingRequest, ResourceFile, RoleMap
from members.models import Member, Person
from memberships.models import Membership, Season, parse_helloasso_url
from warehouse.models import Order, OrderStatus


class OptimizedImagesMixin:
    """Convertit les images envoyées en WebP optimisé (taille maximale par champ)."""

    image_sizes = {}

    def save(self, commit=True):
        instance = super().save(commit=False)
        for field, size in self.image_sizes.items():
            upload = self.cleaned_data.get(field)
            if upload and hasattr(upload, "content_type"):
                image = optimize_image(upload, max_size=size)
                if image:
                    # Remplace le fichier brut par sa version optimisée avant l'enregistrement.
                    getattr(instance, field).save(image.name, image, save=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    def clean(self):
        cleaned = super().clean()
        for field in self.image_sizes:
            upload = cleaned.get(field)
            if upload and hasattr(upload, "content_type"):
                try:
                    validate_upload(upload, max_size=15 * 1024 * 1024, extensions=IMAGE_EXTENSIONS)
                except forms.ValidationError as error:
                    self.add_error(field, error)
        return cleaned


# ---------------------------------------------------------------- Contenus du site
class TeamMemberForm(OptimizedImagesMixin, StyledFormMixin, forms.ModelForm):
    image_sizes = {"photo": 720}

    class Meta:
        model = TeamMember
        fields = ["season", "name", "role_title", "photo", "email", "bio", "instagram_url", "linkedin_url", "person", "is_visible"]
        widgets = {"person": forms.Select(attrs={"data-searchable": ""}), "bio": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["person"].queryset = Person.objects.exclude(kind="organisation").order_by("first_name", "last_name")
        self.fields["person"].help_text = "Facultatif : relie cette présentation à une fiche personne."
        if not self.instance.pk and not self.initial.get("season"):
            self.initial["season"] = Season.current()


class TimelineEntryForm(OptimizedImagesMixin, StyledFormMixin, forms.ModelForm):
    image_sizes = {"image": 960}

    class Meta:
        model = TimelineEntry
        fields = ["date_label", "title", "body", "image", "is_visible"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}


class ServiceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = ["icon", "title", "body", "is_visible"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}


class PageForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Page
        fields = ["title", "slug", "body", "is_published", "show_in_footer", "needs_review"]
        widgets = {"body": forms.Textarea(attrs={"rows": 22, "class": "font-mono text-sm"})}
        help_texts = {"slug": "Adresse de la page : magellans.fr/p/<adresse>/"}


class FAQEntryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = FAQEntry
        fields = ["topic", "question", "answer", "is_visible"]
        widgets = {"answer": forms.Textarea(attrs={"rows": 4})}


class ResourceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ResourceFile
        fields = ["name", "category", "desc", "associated_file", "external_url"]
        widgets = {"desc": forms.Textarea(attrs={"rows": 2}), "category": forms.TextInput(attrs={"list": "resource-categories"})}

    def clean(self):
        cleaned = super().clean()
        upload = cleaned.get("associated_file")
        if upload and hasattr(upload, "size"):
            try:
                validate_upload(upload, max_size=25 * 1024 * 1024)
            except forms.ValidationError as error:
                self.add_error("associated_file", error)
        if not cleaned.get("associated_file") and not cleaned.get("external_url") and not self.instance.associated_file:
            raise forms.ValidationError("Ajoute un fichier ou un lien externe.")
        return cleaned


SETTINGS_SECTIONS = [
    {
        "key": "identite",
        "label": "Identité & accueil",
        "icon": "house",
        "fields": [
            "site_name", "tagline", "meta_description", "founded_year", "rna_number", "address", "postal_code", "city",
            "hero_kicker", "hero_title", "hero_text", "hero_video", "hero_image", "about_title", "about_text", "photo_credits",
        ],
    },
    {
        "key": "contact",
        "label": "Contact & réseaux",
        "icon": "mail",
        "fields": ["contact_email", "contact_phone", "instagram_url", "tiktok_url", "youtube_url", "twitch_url", "discord_url", "linkedin_url", "donation_url"],
    },
    {
        "key": "annonce",
        "label": "Annonce & mise en avant",
        "icon": "megaphone",
        "fields": [
            "announcement_enabled", "announcement_text", "announcement_link_label", "announcement_link_url", "announcement_tone",
            "spotlight_enabled", "spotlight_title", "spotlight_text", "spotlight_video_url", "seasonal_theme",
        ],
    },
    {
        "key": "magasin",
        "label": "Magasin",
        "icon": "package",
        "fields": [
            "warehouse_enabled", "warehouse_members_only", "warehouse_notice", "order_cooldown_minutes",
            "order_min_notice_hours", "order_max_days", "pickup_address", "pickup_instructions",
        ],
    },
    {
        "key": "contrat",
        "label": "Contrat de prêt",
        "icon": "signature",
        "fields": ["contract_signatory_name", "contract_signatory_title", "contract_signature", "contract_intro", "contract_commitments", "contract_counterparts"],
    },
    {
        "key": "aides",
        "label": "Aides & notes de frais",
        "icon": "hand-coins",
        "fields": ["funding_max_amount", "funding_intro", "expense_intro"],
    },
    {
        "key": "notifications",
        "label": "Notifications e-mail",
        "icon": "bell",
        "fields": ["notify_contact", "notify_orders", "notify_memberships", "notify_finance", "notify_funding"],
    },
    {
        "key": "adhesions",
        "label": "Adhésions",
        "icon": "id-card",
        "fields": ["membership_auto_accounts"],
    },
    {
        "key": "avance",
        "label": "Avancé",
        "icon": "settings",
        "fields": ["maintenance_mode", "maintenance_message", "ga_measurement_id"],
        "capability": "settings_advanced",
    },
]

TEXTAREA_ROWS = {
    "meta_description": 2, "hero_text": 3, "about_text": 8, "photo_credits": 3, "warehouse_notice": 3,
    "pickup_instructions": 3, "contract_intro": 3, "contract_commitments": 10, "contract_counterparts": 10,
    "funding_intro": 5, "expense_intro": 6, "notify_contact": 3, "notify_orders": 3, "notify_memberships": 3,
    "notify_finance": 3, "notify_funding": 3, "maintenance_message": 3, "spotlight_text": 3,
}


class SettingsFormBase(OptimizedImagesMixin, StyledFormMixin, forms.ModelForm):
    image_sizes = {"hero_image": 1920}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, rows in TEXTAREA_ROWS.items():
            if name in self.fields:
                self.fields[name].widget.attrs["rows"] = rows

    def clean_hero_video(self):
        video = self.cleaned_data.get("hero_video")
        if video and hasattr(video, "size"):
            validate_upload(video, max_size=40 * 1024 * 1024, extensions=["mp4", "webm"])
        return video

    def clean_contract_signature(self):
        signature = self.cleaned_data.get("contract_signature")
        if signature and hasattr(signature, "size"):
            validate_upload(signature, max_size=3 * 1024 * 1024, extensions=["png", "jpg", "jpeg", "webp"])
        return signature


def settings_form_class(section):
    return modelform_factory(SiteSettings, form=SettingsFormBase, fields=section["fields"])


# ----------------------------------------------------------------------- Saisons
class SeasonForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Season
        fields = ["label", "start_date", "end_date", "helloasso_url", "price", "registrations_open", "is_current", "pitch", "helloasso_other_urls"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "end_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "pitch": forms.Textarea(attrs={"rows": 7}),
            "helloasso_other_urls": forms.Textarea(attrs={"rows": 2}),
        }

    URL_ERROR = "Lien HelloAsso non reconnu. Exemple attendu : https://www.helloasso.com/associations/magellans/adhesions/adhesions-2026-2027"

    def clean_helloasso_url(self):
        url = self.cleaned_data.get("helloasso_url")
        if url and not parse_helloasso_url(url):
            raise forms.ValidationError(self.URL_ERROR)
        return url

    def clean_helloasso_other_urls(self):
        lines = [line.strip() for line in self.cleaned_data.get("helloasso_other_urls", "").splitlines() if line.strip()]
        for line in lines:
            if not parse_helloasso_url(line):
                raise forms.ValidationError(f"{self.URL_ERROR} (ligne « {line} »)")
        return "\n".join(lines)

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end and end <= start:
            self.add_error("end_date", "La fin de saison doit être après son début.")
        return cleaned


class ManualMembershipForm(StyledFormMixin, forms.Form):
    person = forms.ModelChoiceField(
        label="Personne", queryset=Person.objects.order_by("first_name", "last_name"), required=False,
        widget=forms.Select(attrs={"data-searchable": ""}),
    )
    new_first_name = forms.CharField(label="Prénom", max_length=30, required=False)
    new_last_name = forms.CharField(label="Nom", max_length=30, required=False)
    new_email = forms.EmailField(label="E-mail", required=False)
    new_phone = forms.CharField(label="Téléphone", max_length=20, required=False)
    season = forms.ModelChoiceField(label="Saison", queryset=Season.objects.all())
    amount = forms.DecimalField(label="Montant (€)", min_value=0, max_digits=8, decimal_places=2, initial=0)
    payment_method = forms.ChoiceField(label="Paiement", choices=[c for c in Membership.PAYMENT_METHODS if c[0] != "card"])
    joined_at = forms.DateField(label="Date", widget=forms.DateInput(attrs={"type": "date"}), required=False)
    notes = forms.CharField(label="Notes", required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["season"].initial = Season.current()

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("person") and not (cleaned.get("new_first_name") and cleaned.get("new_last_name")):
            raise forms.ValidationError("Choisis une personne existante ou indique au moins le prénom et le nom d'une nouvelle personne.")
        person, season = cleaned.get("person"), cleaned.get("season")
        if person and season and person.memberships.active().filter(season=season).exists():
            raise forms.ValidationError(f"{person.display_name} a déjà une adhésion valide pour {season.label}.")
        cleaned["new_phone"] = normalize_phone(cleaned.get("new_phone"))
        return cleaned


class MembershipEditForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["status", "amount", "donation", "payment_method", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


# ----------------------------------------------------------------------- Personnes
class PersonForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Person
        fields = ["kind", "first_name", "last_name", "organisation_name", "email", "phone", "gender", "additional_notes"]
        widgets = {"additional_notes": forms.Textarea(attrs={"rows": 4})}
        labels = {"additional_notes": "Notes internes (visibles du CA uniquement)"}

    def clean_phone(self):
        return normalize_phone(self.cleaned_data.get("phone"))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("kind") == Person.Kind.ORGANISATION:
            if not cleaned.get("organisation_name"):
                self.add_error("organisation_name", "Indique le nom de l'organisation.")
        elif not (cleaned.get("first_name") or cleaned.get("last_name")):
            raise forms.ValidationError("Indique au moins un nom ou un prénom.")
        return cleaned


class BoardRolesForm(StyledFormMixin, forms.Form):
    roles = forms.MultipleChoiceField(
        label="Rôles au CA", choices=BOARD_ROLES, required=False, widget=forms.CheckboxSelectMultiple
    )


class LinkAccountForm(StyledFormMixin, forms.Form):
    account = forms.ModelChoiceField(
        label="Compte du site",
        queryset=Member.objects.select_related("site_person").order_by("email"),
        widget=forms.Select(attrs={"data-searchable": ""}),
        help_text="La fiche actuelle sera fusionnée avec la fiche de ce compte (adhésions, opérations, projets…).",
    )


# ------------------------------------------------------------------------- Magasin
class OrderDecisionForm(StyledFormMixin, forms.Form):
    STATUS_CHOICES = [
        (OrderStatus.ACCEPTED, "Accepter"),
        (OrderStatus.ACCEPTED_MODIFIED, "Accepter avec modifications"),
        (OrderStatus.REFUSED, "Refuser"),
        (OrderStatus.PENDING, "Remettre en attente"),
        (OrderStatus.SIGNED, "Contrat signé (hors ligne)"),
        (OrderStatus.RETURNED, "Matériel rendu — terminer"),
        (OrderStatus.CANCELLED, "Annuler"),
    ]
    status = forms.TypedChoiceField(label="Nouveau statut", choices=STATUS_CHOICES, coerce=int)
    note = forms.CharField(
        label="Message pour le demandeur", required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    notify = forms.BooleanField(label="Prévenir le demandeur par e-mail", required=False, initial=True)


class OrderNotesForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ["notes"]
        labels = {"notes": "Notes internes du magasin"}
        widgets = {"notes": forms.Textarea(attrs={"rows": 4, "placeholder": "État du matériel au retour, remarques…"})}


# ---------------------------------------------------------------------- Projets
class ProjectForm(OptimizedImagesMixin, StyledFormMixin, forms.ModelForm):
    image_sizes = {"poster": 1200}

    class Meta:
        model = Project
        fields = [
            "name", "genre", "status", "short_desc", "desc", "poster", "video_url", "duration_minutes",
            "shoot_date", "release_date", "director", "money_handler", "festivals", "public", "featured",
        ]
        widgets = {
            "short_desc": forms.TextInput(),
            "desc": forms.Textarea(attrs={"rows": 6}),
            "festivals": forms.Textarea(attrs={"rows": 3}),
            "shoot_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "release_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "director": forms.Select(attrs={"data-searchable": ""}),
            "money_handler": forms.Select(attrs={"data-searchable": ""}),
        }


class CreditForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = RoleMap
        fields = ["person", "role_name", "label"]
        widgets = {"person": forms.Select(attrs={"data-searchable": ""})}


class FundingDecisionForm(StyledFormMixin, forms.ModelForm):
    notify = forms.BooleanField(label="Prévenir le / la demandeur·se par e-mail", required=False, initial=True)

    class Meta:
        model = ProjectFundingRequest
        fields = ["status", "granted_amount", "decision_note"]
        widgets = {"decision_note": forms.Textarea(attrs={"rows": 4})}
        labels = {"decision_note": "Message / motivation de la décision"}


class InvoiceStatusForm(StyledFormMixin, forms.Form):
    status = forms.ChoiceField(label="Nouveau statut", choices=INVOICE_STATUS)
    note = forms.CharField(label="Message pour l'auteur·ice", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    notify = forms.BooleanField(label="Prévenir par e-mail", required=False, initial=True)


__all__ = [name for name in dir() if name.endswith("Form") or name in {"SETTINGS_SECTIONS", "settings_form_class"}]
