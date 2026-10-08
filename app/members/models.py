"""Comptes du site (Member) et fiches personnes (Person).

- ``Member`` : compte de connexion au site (e-mail + mot de passe).
- ``Person`` : fiche d'une personne ou d'une organisation, avec ou sans compte
  (tiers d'une opération bancaire, réalisateur·ice d'un projet, adhérent·e…).

Champs historiques conservés tels quels pour préserver la base existante :
``Person.role``, ``Person.ext_profile`` / ``UnregisteredMember``,
``Member.donation``, ``Member.account`` et ``Member.api_token``. Ils ne sont plus
utilisés par le site et pourront être supprimés lors d'une future version.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from core.permissions import BOARD_ROLE_LABELS
from core.utils import format_phone

ROLE_CHOICES = [
    ("P", "Président.e"),
    ("C", "Communication"),
    ("G", "Gestionnaire magasin"),
    ("T", "Trésorier.ère"),
    ("S", "Secrétaire"),
    ("M", "Membre Magellans & site"),
    ("Mx", "Membre Magellans & pas site"),
    ("E", "Inscrit site"),
    ("O", "Organisation"),
    ("X", "Externe site"),
    ("W", "Webmaster"),
]

GENDER_CHOICES = [
    ("M", "Homme"),
    ("F", "Femme"),
    ("B", "Non-binaire"),
    ("O", "Autre"),
]

PLACEHOLDER_NAMES = {"", "inconnu", "indéfini", "non-renseigné"}


class MemberManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email).lower()
        person = extra_fields.pop("person", None)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user._pending_person = person
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Un super-utilisateur doit avoir is_staff=True et is_superuser=True.")
        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, username):
        # Recherche exacte d'abord (comptes historiques), puis insensible à la casse.
        try:
            return self.get(email=username)
        except self.model.DoesNotExist:
            matches = list(self.filter(email__iexact=username)[:2])
            if len(matches) == 1:
                return matches[0]
            raise


class Member(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Courriel")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_staff = models.BooleanField(default=False, verbose_name="CA")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    # Champs historiques (non utilisés, conservés pour préserver les données).
    donation = models.FloatField(default=0, verbose_name="Montant donation (ancien site)")
    account = models.FloatField(default=0, verbose_name="Statut compte (ancien site)")
    api_token = models.CharField(max_length=128, null=True, blank=True, editable=False)

    objects = MemberManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Compte"
        verbose_name_plural = "Comptes"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating:
            person = getattr(self, "_pending_person", None)
            if person is None:
                person = Person(email=self.email, role="E")
            person.site_profile = self
            person.email = person.email or self.email
            person.save()
            self._pending_person = None

    def __str__(self):
        name = self.get_full_name()
        return f"{name} ({self.email})" if name else self.email

    @property
    def person(self):
        try:
            return self.site_person
        except Person.DoesNotExist:
            return None

    @property
    def first_name(self):
        person = self.person
        return person.clean_first_name if person else ""

    @property
    def last_name(self):
        person = self.person
        return person.clean_last_name if person else ""

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self):
        return self.get_full_name() or self.email

    def get_short_name(self):
        return self.first_name or self.email.split("@")[0]

    @property
    def profile_complete(self):
        person = self.person
        return bool(person and person.clean_first_name and person.clean_last_name and person.phone_display)


class UnregisteredMember(models.Model):
    """Historique : marqueur des personnes externes (n'est plus utilisé)."""

    class Meta:
        verbose_name = "Externe site (ancien)"
        verbose_name_plural = "Externes site (ancien)"

    def __str__(self):
        person = getattr(self, "ext_person", None)
        return str(person) if person else f"Externe #{self.pk}"


class PersonQuerySet(models.QuerySet):
    def board(self):
        return self.exclude(board_roles=[]).exclude(board_roles__isnull=True)

    def current_members(self):
        from memberships.models import Season

        season = Season.current()
        if season is None:
            return self.none()
        return self.filter(memberships__season=season, memberships__status="active").distinct()

    def in_directory(self):
        """Fiches visibles dans l'annuaire : volontaires ayant adhéré pour la saison en cours."""
        return self.current_members().filter(show_in_directory=True)


class Person(models.Model):
    class Kind(models.TextChoices):
        INDIVIDUAL = "individual", "Personne"
        ORGANISATION = "organisation", "Organisation"

    email = models.EmailField(verbose_name="Courriel", null=True, blank=True)
    first_name = models.CharField(max_length=30, null=True, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=30, null=True, blank=True, verbose_name="Nom")
    phone = models.CharField(max_length=15, blank=True, verbose_name="Téléphone")
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="Genre"
    )
    site_profile = models.OneToOneField(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Compte du site",
        related_name="site_person",
    )
    ext_profile = models.OneToOneField(
        UnregisteredMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Profil externe lié (ancien)",
        related_name="ext_person",
        editable=False,
    )
    role = models.CharField(
        max_length=2,
        choices=ROLE_CHOICES,
        default="X",
        verbose_name="Rôle (ancien site)",
        help_text="Champ historique, remplacé par les rôles CA et les adhésions.",
    )
    additional_notes = models.TextField(verbose_name="Notes internes", null=True, blank=True)

    # --- Ajouts de la refonte 2026 ---------------------------------------------
    kind = models.CharField(
        "Type", max_length=12, choices=Kind.choices, default=Kind.INDIVIDUAL
    )
    board_roles = models.JSONField(
        "Rôles au conseil d'administration",
        default=list,
        blank=True,
        help_text="Codes des rôles CA (une personne peut en cumuler plusieurs).",
    )
    organisation_name = models.CharField("Nom de l'organisation", max_length=200, blank=True)
    bio = models.TextField("Présentation", blank=True, max_length=800)
    skills = models.JSONField("Compétences", default=list, blank=True)
    portfolio_url = models.URLField("Portfolio / site", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    show_in_directory = models.BooleanField(
        "Apparaître dans l'annuaire des membres",
        default=False,
        help_text="Visible uniquement par les adhérent·es connecté·es.",
    )
    avatar = models.ImageField("Photo de profil", upload_to="avatars/", blank=True)
    created_at = models.DateTimeField("Créée le", null=True, blank=True, editable=False)
    updated_at = models.DateTimeField("Modifiée le", null=True, blank=True, editable=False)

    objects = PersonQuerySet.as_manager()

    class Meta:
        verbose_name = "Personne"
        ordering = ["last_name", "first_name", "pk"]

    def __str__(self):
        name = self.display_name
        return f"{name} ({self.email})" if self.email and name != self.email else name

    def save(self, *args, **kwargs):
        now = timezone.now()
        if self.created_at is None:
            self.created_at = now
        self.updated_at = now
        self.board_roles = sorted({role for role in (self.board_roles or []) if role in BOARD_ROLE_LABELS})
        super().save(*args, **kwargs)
        if self.site_profile_id:
            Member.objects.filter(pk=self.site_profile_id, is_superuser=False).update(
                is_staff=bool(self.board_roles)
            )

    # --- Affichage -------------------------------------------------------------
    @property
    def clean_first_name(self):
        value = (self.first_name or "").strip()
        return "" if value.lower() in PLACEHOLDER_NAMES else value

    @property
    def clean_last_name(self):
        value = (self.last_name or "").strip()
        return "" if value.lower() in PLACEHOLDER_NAMES else value

    @property
    def full_name(self):
        return f"{self.clean_first_name} {self.clean_last_name}".strip()

    @property
    def display_name(self):
        if self.kind == self.Kind.ORGANISATION and self.organisation_name:
            return self.organisation_name
        return self.full_name or self.organisation_name or (self.email or f"Personne #{self.pk}")

    @property
    def contact_email(self):
        """Adresse de la fiche, sinon celle du compte associé."""
        if self.email:
            return self.email
        return self.site_profile.email if self.site_profile_id else ""

    @property
    def phone_display(self):
        return format_phone(self.phone)

    def phone_formatted(self):  # compatibilité avec les anciens gabarits
        return self.phone_display or "Non renseigné"

    # --- Statuts ---------------------------------------------------------------
    @property
    def is_board(self):
        return bool(self.board_roles)

    @property
    def board_role_labels(self):
        return [BOARD_ROLE_LABELS[code] for code in self.board_roles or [] if code in BOARD_ROLE_LABELS]

    @property
    def is_organisation(self):
        return self.kind == self.Kind.ORGANISATION

    def membership_for(self, season):
        if season is None:
            return None
        return self.memberships.active().filter(season=season).first()

    @property
    def current_membership(self):
        from memberships.models import Season

        if not hasattr(self, "_current_membership_cache"):
            self._current_membership_cache = self.membership_for(Season.current())
        return self._current_membership_cache

    @property
    def is_current_member(self):
        return self.current_membership is not None

    @property
    def is_in_directory(self):
        """Même règle que ``PersonQuerySet.in_directory``."""
        return self.show_in_directory and self.is_current_member

    @property
    def status_label(self):
        if self.is_organisation:
            return "Organisation"
        if self.is_board:
            return "Membre du CA"
        if self.is_current_member:
            return "Adhérent·e à jour"
        if self.site_profile_id:
            return "Inscrit·e sur le site"
        return "Externe"
