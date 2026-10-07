"""Magasin de matériel : objets, réservations et contrats de prêt."""

import json

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.storage import private_storage, upload_to
from members.models import Member

ITEM_STATUS_CHOICES = [
    (5, "Neuf"),
    (4, "Très bon état"),
    (3, "Bon état"),
    (2, "État moyen"),
    (1, "Mauvais état"),
    (0, "En maintenance"),
    (-1, "Hors service"),
]

AVAILABILITY_CHOICES = [
    (1, "Réservable"),
    (2, "Réservable (actuellement sorti)"),
    (0, "Non réservable"),
]


class OrderStatus(models.IntegerChoices):
    DRAFT = 0, "Brouillon"
    PENDING = 1, "En attente de réponse"
    REFUSED = 2, "Refusée"
    ACCEPTED = 3, "Acceptée — contrat à signer"
    ACCEPTED_MODIFIED = 4, "Acceptée avec modifications — contrat à signer"
    SIGNED = 5, "Contrat signé"
    RETURNED = 6, "Terminée (matériel rendu)"
    CANCELLED = 7, "Annulée"


ORDER_STATUS_CHOICES = OrderStatus.choices
# Réservations qui bloquent effectivement le matériel sur leur période.
BLOCKING_STATUSES = (OrderStatus.ACCEPTED, OrderStatus.ACCEPTED_MODIFIED, OrderStatus.SIGNED)
OPEN_STATUSES = (OrderStatus.PENDING, *BLOCKING_STATUSES)


class Tag(models.Model):
    name = models.CharField("Nom", max_length=20)
    color = models.CharField("Couleur", default="#f5a524", max_length=10)

    class Meta:
        verbose_name = "Catégorie"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField("Nom", max_length=255)
    tags = models.ManyToManyField(Tag, verbose_name="Catégories", blank=True, related_name="items")
    image = models.ImageField("Photo", upload_to="img/items/", default="", blank=True)
    max_stock = models.PositiveSmallIntegerField("Quantité totale", default=1)
    now_available = models.PositiveIntegerField("Disponible(s) (ancien site)", default=0, editable=False)
    state = models.IntegerField("État", choices=ITEM_STATUS_CHOICES, default=4)
    buy_price = models.FloatField("Prix d'achat (€)", blank=True, null=True)
    owner = models.CharField("Propriétaire", blank=True, null=True)
    availability = models.IntegerField("Réservation", choices=AVAILABILITY_CHOICES, default=1)
    # Ajouts de la refonte 2026
    description = models.TextField("Description / conseils d'utilisation", blank=True)
    is_archived = models.BooleanField(
        "Archivé", default=False, help_text="Un objet archivé n'apparaît plus dans le catalogue."
    )
    created_at = models.DateTimeField("Ajouté le", null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Objet"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.created_at is None:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def has_photo(self):
        # L'ancien site copiait parfois l'image par défaut (« img/items/default_Ab12Cd3.png »).
        return bool(self.image) and not self.image.name.lstrip("/").startswith("img/items/default")

    @property
    def is_bookable(self):
        return not self.is_archived and self.availability != 0 and self.state >= 1

    @property
    def state_tone(self):
        if self.state >= 3:
            return "success"
        if self.state >= 1:
            return "warning"
        return "danger"


class OrderQuerySet(models.QuerySet):
    def submitted(self):
        return self.exclude(status=OrderStatus.DRAFT)

    def overlapping(self, start, end):
        return self.filter(date_start__lt=end, date_end__gt=start)


class Order(models.Model):
    date_start = models.DateTimeField("Début de la réservation", null=True, blank=True)
    date_end = models.DateTimeField("Fin de la réservation", null=True, blank=True)
    # Ancien stockage des quantités (JSON) : remplacé par OrderLine, conservé intact.
    quantities = models.TextField(verbose_name="Quantités (ancien site)", default="{}", editable=False)
    message = models.TextField(verbose_name="Message du demandeur", null=True, blank=True)
    # Anciennes réponses du magasin (HTML) : reprises dans le fil de messages.
    answer_message = models.TextField(verbose_name="Réponses (ancien site)", default="", blank=True, editable=False)
    user = models.ForeignKey(
        Member, verbose_name="Demandeur", blank=True, null=True, on_delete=models.SET_NULL, related_name="orders"
    )
    pickup_first_name = models.TextField("Prénom de la personne qui récupère", max_length=255, blank=True, default="")
    pickup_last_name = models.TextField("Nom de la personne qui récupère", max_length=255, blank=True, default="")
    pickup_phone = models.TextField("Téléphone de la personne qui récupère", max_length=12, blank=True, default="")
    status = models.IntegerField("Statut", choices=ORDER_STATUS_CHOICES, default=OrderStatus.DRAFT)
    date_created = models.DateTimeField("Demande envoyée le", auto_now_add=True)
    date_validated = models.DateTimeField("Réponse donnée le", blank=True, null=True)
    tos = models.BooleanField("Conditions acceptées", default=True)
    project_name = models.CharField("Projet", null=True, default="", blank=True, max_length=255)
    sent_by_mail = models.BooleanField("Notification envoyée", default=False)
    notes = models.TextField("Notes internes du magasin", null=True, blank=True)
    # Ajouts de la refonte 2026
    updated_at = models.DateTimeField("Modifiée le", null=True, blank=True)
    returned_at = models.DateTimeField("Matériel rendu le", null=True, blank=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "Réservation"
        ordering = ["-date_created"]

    def __str__(self):
        if self.status == OrderStatus.DRAFT:
            return f"Brouillon de réservation de {self.user}"
        if self.date_start and self.date_end:
            start = timezone.localtime(self.date_start)
            end = timezone.localtime(self.date_end)
            return f"Réservation #{self.pk} de {self.user} : {start:%d/%m/%Y} → {end:%d/%m/%Y}"
        return f"Réservation #{self.pk} de {self.user}"

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("warehouse:order-detail", kwargs={"pk": self.pk})

    def load_legacy_quantities(self):
        try:
            data = json.loads(self.quantities or "{}")
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}

    @property
    def is_draft(self):
        return self.status == OrderStatus.DRAFT

    @property
    def is_accepted(self):
        return self.status in (OrderStatus.ACCEPTED, OrderStatus.ACCEPTED_MODIFIED)

    @property
    def needs_contract(self):
        contract = getattr(self, "contract", None)
        return self.is_accepted and (contract is None or not contract.is_signed)

    @property
    def can_be_cancelled(self):
        return self.status in (OrderStatus.DRAFT, OrderStatus.PENDING, *BLOCKING_STATUSES)

    @property
    def owner_can_cancel(self):
        """Le demandeur peut annuler en ligne tant que le contrat n'est pas signé."""
        return self.status in (OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.ACCEPTED_MODIFIED)

    @property
    def status_tone(self):
        return {
            OrderStatus.DRAFT: "neutral",
            OrderStatus.PENDING: "warning",
            OrderStatus.REFUSED: "danger",
            OrderStatus.ACCEPTED: "info",
            OrderStatus.ACCEPTED_MODIFIED: "info",
            OrderStatus.SIGNED: "success",
            OrderStatus.RETURNED: "neutral",
            OrderStatus.CANCELLED: "neutral",
        }.get(self.status, "neutral")

    @property
    def pickup_display(self):
        name = f"{self.pickup_first_name or ''} {self.pickup_last_name or ''}".strip()
        if name.lower() in {"non-renseigné non-renseigné", "non-renseigné"}:
            name = ""
        return name or (self.user.display_name if self.user_id else "")

    @property
    def total_items(self):
        return sum(line.quantity for line in self.lines.all())

    @property
    def duration_days(self):
        if not (self.date_start and self.date_end):
            return 0
        return max(1, (self.date_end - self.date_start).days + (1 if (self.date_end - self.date_start).seconds else 0))


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines", verbose_name="Réservation")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="order_lines", verbose_name="Objet")
    quantity = models.PositiveSmallIntegerField("Quantité", default=1)
    available = models.BooleanField(
        "Accordé", default=True, help_text="Décoché si le magasin ne peut pas prêter cet objet."
    )

    class Meta:
        verbose_name = "Ligne de réservation"
        verbose_name_plural = "Lignes de réservation"
        ordering = ["item__name"]
        constraints = [models.UniqueConstraint(fields=["order", "item"], name="unique_item_per_order")]

    def __str__(self):
        return f"{self.quantity} × {self.item}"


class Contract(models.Model):
    """Contrat de prêt, généré et signé électroniquement sur le site."""

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="contract", verbose_name="Réservation")
    director_name = models.CharField("Réalisateur·ice", max_length=200)
    director_phone = models.CharField("Téléphone du / de la réalisateur·ice", max_length=30)
    director_email = models.EmailField("E-mail du / de la réalisateur·ice")
    production_name = models.CharField("Production", max_length=200)
    production_address = models.CharField("Adresse de la production", max_length=300, blank=True)
    production_phone = models.CharField("Téléphone de la production", max_length=30)
    production_email = models.EmailField("E-mail de la production")
    terms = models.JSONField("Conditions au moment de la signature", default=dict, blank=True)
    signer_name = models.CharField("Signé par", max_length=200, blank=True)
    signed_at = models.DateTimeField("Signé le", null=True, blank=True)
    signer_ip = models.GenericIPAddressField("IP du signataire", null=True, blank=True)
    signer_user_agent = models.CharField("Navigateur du signataire", max_length=400, blank=True)
    signature_image = models.ImageField(
        "Signature", upload_to=upload_to("contracts/signatures"), storage=private_storage, blank=True
    )
    pdf = models.FileField("Contrat signé (PDF)", upload_to=upload_to("contracts"), storage=private_storage, blank=True)
    sha256 = models.CharField("Empreinte SHA-256 du PDF", max_length=64, blank=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Modifié le", auto_now=True)

    class Meta:
        verbose_name = "Contrat de prêt"
        verbose_name_plural = "Contrats de prêt"

    def __str__(self):
        return f"Contrat de la réservation #{self.order_id}"

    @property
    def is_signed(self):
        return self.signed_at is not None

    @property
    def reference(self):
        return f"MAG-{self.order_id:05d}"
