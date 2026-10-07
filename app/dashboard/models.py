"""Projets (films), demandes d'aide à projet et ressources pour les membres."""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from core.storage import private_storage, upload_to
from members.models import Member, Person

# Affiche par défaut de l'ancien site, et ses copies (« default_Ab12Cd3.png »).
LEGACY_DEFAULT_POSTER = "img/projects/default"


def dynamic_upload_path(instance, filename):
    """Conservée car référencée par les migrations historiques."""
    return "funding_requests/" + slugify(instance.name) + "/" + filename


class FundingStatus(models.TextChoices):
    SUBMITTED = "submitted", "Déposée"
    REVIEWING = "reviewing", "En cours d'examen"
    ACCEPTED = "accepted", "Acceptée"
    PARTIAL = "partial", "Acceptée partiellement"
    REFUSED = "refused", "Refusée"
    WITHDRAWN = "withdrawn", "Retirée"


FUNDING_TONES = {
    "submitted": "info",
    "reviewing": "warning",
    "accepted": "success",
    "partial": "success",
    "refused": "danger",
    "withdrawn": "neutral",
}


class ProjectFundingRequest(models.Model):
    name = models.CharField("Nom du projet", max_length=255)
    asker = models.ForeignKey(
        Member,
        verbose_name="Demandeur·se",
        blank=True,
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
        related_name="funding_requests",
    )
    role = models.CharField("Ton poste sur le projet", max_length=255)
    directors = models.CharField("Réalisateur·ices", max_length=255)
    genre = models.CharField("Genre", max_length=255)
    duration = models.PositiveIntegerField("Durée estimée (minutes)")
    production = models.CharField("Production", max_length=255)
    previsional_shoot_start_date = models.DateField("Début prévisionnel du tournage")
    previsional_shoot_end_date = models.DateField("Fin prévisionnelle du tournage")
    explanation = models.TextField("Pourquoi cette demande ?")
    funding_value = models.PositiveIntegerField("Montant demandé (€)")
    deposit_date = models.DateTimeField("Déposée le", auto_now_add=True)
    script = models.FileField("Scénario", upload_to=upload_to("funding_requests"), storage=private_storage)
    intention_note = models.FileField(
        "Note d'intention", upload_to=upload_to("funding_requests"), storage=private_storage
    )
    previsional_budget_plan = models.FileField(
        "Plan de financement prévisionnel", upload_to=upload_to("funding_requests"), storage=private_storage
    )
    contact_list = models.FileField("Fiche contact", upload_to=upload_to("funding_requests"), storage=private_storage)
    sent_by_mail = models.BooleanField("Dossier envoyé par e-mail", default=False)
    # Ajouts de la refonte 2026
    status = models.CharField("Statut", max_length=12, choices=FundingStatus.choices, default=FundingStatus.SUBMITTED)
    granted_amount = models.DecimalField("Montant accordé (€)", max_digits=8, decimal_places=2, null=True, blank=True)
    decision_note = models.TextField("Réponse du CA", blank=True)
    decided_at = models.DateTimeField("Décision prise le", null=True, blank=True)
    decided_by = models.ForeignKey(
        Member, verbose_name="Décision saisie par", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        verbose_name = "Demande d'aide à projet"
        verbose_name_plural = "Demandes d'aide à projet"
        ordering = ["-deposit_date"]

    def __str__(self):
        return f"Demande d'aide « {self.name} » ({self.funding_value} €)"

    def get_absolute_url(self):
        return reverse("funding:detail", kwargs={"pk": self.pk})

    @property
    def status_tone(self):
        return FUNDING_TONES.get(self.status, "neutral")

    @property
    def files(self):
        return [
            (field, getattr(self, field), self._meta.get_field(field).verbose_name)
            for field in ("script", "intention_note", "previsional_budget_plan", "contact_list")
            if getattr(self, field)
        ]


class ProjectStatus(models.TextChoices):
    DEVELOPMENT = "development", "En développement"
    PREPRODUCTION = "preproduction", "En préparation"
    SHOOTING = "shooting", "En tournage"
    POSTPRODUCTION = "postproduction", "En post-production"
    RELEASED = "released", "Sorti"


class Project(models.Model):
    name = models.CharField("Titre", max_length=255)
    slug = models.SlugField("Adresse", max_length=255, unique=True, blank=True, editable=False)
    genre = models.CharField("Genre", max_length=255, blank=True, default="Non-spécifié")
    desc = models.TextField("Synopsis / présentation")
    short_desc = models.TextField("Accroche", null=True, blank=True)
    poster = models.ImageField("Affiche", upload_to="img/projects/", default="", blank=True)
    shoot_date = models.DateField("Date du tournage", blank=True, null=True)
    release_date = models.DateField("Date de sortie", blank=True, null=True)
    director = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Réalisateur·ice",
        related_name="directed_projects",
    )
    money_handler = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        verbose_name="Responsable financier·ère",
        related_name="handled_projects",
    )
    public = models.BooleanField("Visible dans le catalogue public", default=False)
    # Ajouts de la refonte 2026
    status = models.CharField("Avancement", max_length=20, choices=ProjectStatus.choices, blank=True)
    video_url = models.URLField("Film ou bande-annonce (YouTube / Vimeo)", blank=True)
    duration_minutes = models.PositiveSmallIntegerField("Durée (minutes)", null=True, blank=True)
    festivals = models.TextField("Festivals & distinctions", blank=True, help_text="Un par ligne.")
    featured = models.BooleanField("Mis en avant sur l'accueil", default=False)
    created_at = models.DateTimeField("Créé le", null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Projet"
        ordering = ["-release_date", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:240] or "projet"
            slug, counter = base, 2
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, counter = f"{base}-{counter}", counter + 1
            self.slug = slug
        if self.created_at is None:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("film-detail", kwargs={"slug": self.slug})

    @property
    def has_poster(self):
        return bool(self.poster) and not self.poster.name.lstrip("/").startswith(LEGACY_DEFAULT_POSTER)

    @property
    def festival_list(self):
        return [line.strip() for line in (self.festivals or "").splitlines() if line.strip()]

    @property
    def effective_status(self):
        if self.status:
            return self.status
        if self.release_date and self.release_date <= timezone.localdate():
            return ProjectStatus.RELEASED
        return ""

    @property
    def year(self):
        day = self.release_date or self.shoot_date
        return day.year if day else None


class RoleMap(models.Model):
    """Générique d'un projet : qui a fait quoi."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name="Personne", related_name="roles")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Projet", related_name="team")
    ROLE_CHOICES = [
        (1, "Réalisation"),
        (2, "Production"),
        (3, "Scénario"),
        (4, "Direction de la photographie"),
        (5, "Montage"),
        (6, "Son / design sonore"),
        (7, "Décors"),
        (8, "Costumes"),
        (9, "Maquillage"),
        (10, "Interprétation"),
        (11, "Assistanat réalisation"),
        (12, "Assistanat production"),
        (13, "Lumière"),
        (14, "Machinerie"),
        (15, "Perche"),
        (16, "Musique"),
        (17, "Effets visuels"),
        (18, "Cascades"),
        (19, "Casting"),
        (99, "Autre"),
    ]
    role_name = models.IntegerField("Poste", choices=ROLE_CHOICES)
    # Ajouts de la refonte 2026
    label = models.CharField("Intitulé personnalisé", max_length=120, blank=True, help_text="Ex. « Rôle de Mia ».")
    order = models.PositiveSmallIntegerField("Ordre", default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["person", "project", "role_name"], name="unique_user_project_role")
        ]
        verbose_name = "Poste au générique"
        verbose_name_plural = "Générique"
        ordering = ["order", "role_name", "pk"]

    def __str__(self):
        return f"{self.person} — {self.display_role} ({self.project})"

    @property
    def display_role(self):
        return self.label or self.get_role_name_display()


class ResourceFile(models.Model):
    name = models.CharField("Nom", max_length=255)
    associated_file = models.FileField(
        "Fichier", upload_to=upload_to("resources"), storage=private_storage, blank=True
    )
    desc = models.TextField("Description", null=True, blank=True)
    category = models.CharField("Catégorie", max_length=255, null=True, blank=True)
    # Ajouts de la refonte 2026
    external_url = models.URLField("Lien externe", blank=True, help_text="À la place d'un fichier (Drive, Notion…).")
    created_at = models.DateTimeField("Ajoutée le", null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Ressource"
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.created_at is None:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

    def extension(self):
        name = str(self.associated_file or "")
        if "." not in name:
            return "lien" if self.external_url else ""
        return name.rsplit(".", 1)[-1].lower()
