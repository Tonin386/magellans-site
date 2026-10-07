"""Trésorerie : opérations du compte, notes de frais et dépenses."""

import re
from decimal import Decimal

from django.db import IntegrityError, models, transaction
from django.urls import reverse
from django.utils import timezone

from core.storage import private_storage, upload_to
from core.utils import to_decimal
from dashboard.models import Project
from members.models import Member, Person

OPE_TYPES = [
    ("C", "Crédit"),
    ("D", "Débit"),
    ("R", "Remboursement"),
]

STATUS = [
    ("V", "En attente de validation par le CA"),
    ("F", "Validée — remboursement à faire"),
    ("D", "Informations bancaires demandées"),
    ("J", "Justificatif(s) manquant(s)"),
    ("C", "Virement en cours"),
    ("R", "Remboursement effectué"),
    ("X", "Remboursement refusé"),
]
STATUS_TONES = {"V": "info", "F": "warning", "D": "warning", "J": "danger", "C": "success", "R": "success", "X": "neutral"}
# Statuts pour lesquels une action est attendue de la personne qui a déposé la note.
STATUS_NEEDS_AUTHOR = {"D", "J"}

OPERATION_CATEGORIES = [
    ("memberships", "Adhésions & dons"),
    ("projects", "Projets & aides"),
    ("equipment", "Matériel"),
    ("events", "Évènements"),
    ("services", "Prestations"),
    ("reimbursements", "Remboursements de frais"),
    ("fees", "Frais bancaires & abonnements"),
    ("grants", "Subventions"),
    ("other", "Autre"),
]


class Operation(models.Model):
    id = models.CharField(primary_key=True, max_length=100, unique=True, verbose_name="N° d'opération", editable=False)
    desc = models.TextField(verbose_name="Libellé")
    type = models.CharField(max_length=1, choices=OPE_TYPES, default="D", verbose_name="Type")
    third_party = models.ForeignKey(Person, on_delete=models.PROTECT, verbose_name="Tiers", related_name="operations")
    amount = models.FloatField(verbose_name="Montant (€)")
    date_created = models.DateTimeField(verbose_name="Saisie le", editable=False, default=timezone.now)
    date = models.DateField(verbose_name="Date")
    # Ajouts de la refonte 2026
    category = models.CharField("Catégorie", max_length=20, choices=OPERATION_CATEGORIES, default="other")
    invoice = models.ForeignKey(
        "Invoice",
        verbose_name="Note de frais remboursée",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="operations",
    )
    attachment = models.FileField(
        "Pièce jointe", upload_to=upload_to("bank/operations"), storage=private_storage, blank=True
    )
    created_by = models.ForeignKey(
        Member, verbose_name="Saisie par", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        verbose_name = "Opération"
        ordering = ["-date", "-date_created"]

    def __str__(self):
        return f"{self.id} — {self.desc[:60]} ({self.signed_amount:+.2f} €)"

    @staticmethod
    def next_id():
        numbers = [
            int(match.group(1))
            for value in Operation.objects.values_list("id", flat=True)
            if (match := re.fullmatch(r"OPE-(\d+)", value or ""))
        ]
        return f"OPE-{max(numbers, default=0) + 1}"

    def save(self, *args, **kwargs):
        if self.id:
            return super().save(*args, **kwargs)
        # Numérotation séquentielle « OPE-n » ; on réessaie en cas d'enregistrements simultanés.
        for _ in range(5):
            self.id = self.next_id()
            try:
                with transaction.atomic():
                    kwargs["force_insert"] = True
                    return super().save(*args, **kwargs)
            except IntegrityError:
                continue
        raise IntegrityError("Impossible d'attribuer un numéro d'opération.")

    @property
    def amount_decimal(self):
        return to_decimal(self.amount)

    @property
    def signed_amount(self):
        """Montant positif pour un crédit, négatif pour un débit ou un remboursement."""
        amount = abs(self.amount_decimal)
        return amount if self.type == "C" else -amount


def compute_balance(queryset=None):
    total = Decimal("0")
    for operation in queryset if queryset is not None else Operation.objects.all():
        total += operation.signed_amount
    return total


class Invoice(models.Model):
    title = models.CharField(verbose_name="Intitulé", max_length=255)
    date_created = models.DateTimeField(verbose_name="Déposée le", auto_now_add=True, editable=False)
    project = models.ForeignKey(Project, verbose_name="Projet", on_delete=models.PROTECT, related_name="invoices")
    status = models.CharField(max_length=1, choices=STATUS, default="V", verbose_name="Statut")
    author = models.ForeignKey(
        Member, verbose_name="Auteur·ice", on_delete=models.PROTECT, null=True, related_name="invoices"
    )
    role = models.CharField("Rôle sur le projet", max_length=255, null=True)
    comm = models.TextField(verbose_name="Commentaire", null=True, blank=True)
    total = models.CharField("Montant total (calculé)", null=True, blank=True, editable=False, max_length=255)
    # Ajouts de la refonte 2026
    updated_at = models.DateTimeField("Modifiée le", null=True, blank=True)

    class Meta:
        verbose_name = "Note de frais"
        verbose_name_plural = "Notes de frais"
        ordering = ["-date_created"]

    def __str__(self):
        return f"Note de frais #{self.pk} — {self.title}"

    def get_absolute_url(self):
        return reverse("bank:invoice-detail", kwargs={"pk": self.pk})

    @property
    def total_amount(self):
        return sum((to_decimal(expense.amount) for expense in self.expense_set.all()), Decimal("0"))

    def refresh_total(self, save=True):
        self.total = f"{self.total_amount:.2f}"
        if save and self.pk:
            Invoice.objects.filter(pk=self.pk).update(total=self.total, updated_at=timezone.now())

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def status_tone(self):
        return STATUS_TONES.get(self.status, "neutral")

    @property
    def needs_author_action(self):
        return self.status in STATUS_NEEDS_AUTHOR

    @property
    def missing_proofs(self):
        return [expense for expense in self.expense_set.all() if not expense.proof]


class Expense(models.Model):
    title = models.CharField(max_length=255, verbose_name="Dépense")
    date = models.DateField(verbose_name="Date de la dépense")
    comm = models.TextField(verbose_name="Précisions", null=True, blank=True)
    amount = models.FloatField(verbose_name="Montant (€)")
    author = models.ForeignKey(Member, verbose_name="Auteur·ice", on_delete=models.PROTECT, related_name="expenses")
    proof = models.FileField(
        verbose_name="Justificatif",
        null=True,
        blank=True,
        upload_to=upload_to("img/proofs"),
        storage=private_storage,
    )
    linked_invoice = models.ForeignKey(
        Invoice, verbose_name="Note de frais", null=True, blank=True, on_delete=models.SET_NULL
    )
    date_created = models.DateField(verbose_name="Ajoutée le", auto_now_add=True, editable=False)

    class Meta:
        verbose_name = "Dépense"
        ordering = ["date", "pk"]

    def __str__(self):
        return f"{self.title} ({self.amount_decimal} €)"

    @property
    def amount_decimal(self):
        return to_decimal(self.amount)
