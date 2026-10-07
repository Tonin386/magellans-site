from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.urls import reverse

from core.antispam import AntiSpamFormMixin
from core.emails import send_templated_email
from core.forms import IMAGE_EXTENSIONS, StyledFormMixin, validate_upload
from core.utils import normalize_phone, optimize_image

from .models import GENDER_CHOICES, Member, Person

SKILL_SUGGESTIONS = [
    "Réalisation", "Scénario", "Production", "Image / cadrage", "Lumière", "Son", "Montage", "Étalonnage",
    "Effets visuels", "Musique", "Jeu / comédie", "Décors", "Costumes", "Maquillage", "Régie", "Photo",
    "Graphisme", "Communication", "Animation", "Motion design",
]


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.EmailField(
        label="Adresse e-mail", widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"})
    )
    password = forms.CharField(
        label="Mot de passe", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )

    error_messages = {
        "invalid_login": "E-mail ou mot de passe incorrect.",
        "inactive": (
            "Ce compte n'est pas encore activé : clique sur le lien reçu par e-mail "
            "(pense à vérifier tes courriers indésirables)."
        ),
    }

    def clean_username(self):
        return self.cleaned_data["username"].strip()


class RegisterForm(StyledFormMixin, AntiSpamFormMixin, forms.Form):
    first_name = forms.CharField(label="Prénom", max_length=30, widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    last_name = forms.CharField(label="Nom", max_length=30, widget=forms.TextInput(attrs={"autocomplete": "family-name"}))
    email = forms.EmailField(label="Adresse e-mail", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    phone = forms.CharField(
        label="Téléphone",
        max_length=20,
        required=False,
        help_text="Utile pour réserver du matériel au magasin.",
        widget=forms.TextInput(attrs={"autocomplete": "tel", "type": "tel"}),
    )
    password1 = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Au moins 10 caractères, pas trop simple.",
    )
    password2 = forms.CharField(
        label="Confirme ton mot de passe", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )
    tos = forms.BooleanField(label="J'accepte les conditions d'utilisation et la politique de confidentialité.")

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_phone(self):
        return normalize_phone(self.cleaned_data.get("phone"))

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get("password1"), cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Les deux mots de passe ne correspondent pas.")
        if password1 and not self.errors.get("password1"):
            candidate = Member(email=cleaned.get("email") or "")
            try:
                password_validation.validate_password(password1, candidate)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned


class StyledPasswordResetForm(StyledFormMixin, PasswordResetForm):
    email = forms.EmailField(label="Adresse e-mail", widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    def get_users(self, email):
        # Inclut les comptes non activés : un nouvel·le adhérent·e peut ainsi choisir son mot de passe.
        return Member.objects.filter(email__iexact=email)

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        user = context["user"]
        path = reverse("password_reset_confirm", kwargs={"uidb64": context["uid"], "token": context["token"]})
        send_templated_email("password_reset", {"user": user, "reset_path": path}, [to_email])


class StyledSetPasswordForm(StyledFormMixin, SetPasswordForm):
    pass


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    pass


class ProfileForm(StyledFormMixin, forms.ModelForm):
    skills = forms.MultipleChoiceField(
        label="Compétences",
        required=False,
        choices=[(skill, skill) for skill in SKILL_SUGGESTIONS],
        widget=forms.SelectMultiple(attrs={"data-searchable": "", "data-create": ""}),
        help_text="Pour l'annuaire des membres : tu peux aussi saisir tes propres compétences.",
    )
    avatar_upload = forms.ImageField(label="Photo de profil", required=False)
    remove_avatar = forms.BooleanField(label="Retirer ma photo", required=False)

    class Meta:
        model = Person
        fields = ["first_name", "last_name", "phone", "gender", "bio", "skills", "portfolio_url", "instagram_url", "show_in_directory"]
        widgets = {
            "gender": forms.Select(choices=[("", "Je préfère ne pas le dire")] + GENDER_CHOICES),
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "Ce que tu fais, ce que tu aimerais faire…"}),
        }
        labels = {"phone": "Téléphone", "gender": "Genre"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["phone"].required = True
        self.fields["phone"].help_text = "Indispensable pour réserver du matériel."
        current = list(self.instance.skills or [])
        extra = [(skill, skill) for skill in current if skill not in SKILL_SUGGESTIONS]
        self.fields["skills"].choices = self.fields["skills"].choices + extra
        self.initial.setdefault("skills", current)
        if self.instance and not self.instance.clean_first_name:
            self.initial["first_name"] = ""
        if self.instance and not self.instance.clean_last_name:
            self.initial["last_name"] = ""
        if self.instance and not self.instance.phone_display:
            self.initial["phone"] = ""

    def clean_skills(self):
        return [skill.strip()[:40] for skill in self.cleaned_data.get("skills", []) if skill.strip()][:15]

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if len(phone.lstrip("+")) < 8:
            raise forms.ValidationError("Numéro de téléphone invalide.")
        return phone

    def clean_avatar_upload(self):
        return validate_upload(self.cleaned_data.get("avatar_upload"), max_size=8 * 1024 * 1024, extensions=IMAGE_EXTENSIONS)

    def save(self, commit=True):
        person = super().save(commit=False)
        if self.cleaned_data.get("remove_avatar") and person.avatar:
            person.avatar.delete(save=False)
            person.avatar = ""
        upload = self.cleaned_data.get("avatar_upload")
        if upload:
            image = optimize_image(upload, max_size=512)
            if image:
                person.avatar.save(f"avatar-{person.pk}.webp", image, save=False)
        if commit:
            person.save()
        return person


class AccountDeletionForm(StyledFormMixin, forms.Form):
    reason = forms.CharField(
        label="Un mot pour nous ?",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    confirm = forms.BooleanField(label="Je confirme vouloir supprimer mon compte et mes données personnelles.")
