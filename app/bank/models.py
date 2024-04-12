from members.models import Member, Person
from dashboard.models import Project
from datetime import datetime
from django.db import models

OPE_TYPES= [
    ('C', 'Crédit'),
    ('D', 'Débit'),
    ('R', 'Remboursement')
]

STATUS = [
    ('R', "Remboursement effectué et confirmé"),
    ('F', "A faire"),
    ('J', "Justificatif(s) manquant(s)"),
    ('V', "En attente de validation par le CA"),
    ('D', "Demande d'informations bancaires"),
    ('C', "Virement en cours")
]

class Operation(models.Model):
    id = models.CharField(primary_key=True, max_length=100, unique=True, verbose_name="ID Opération", editable=False)
    desc = models.TextField(verbose_name="Description")
    type = models.CharField(max_length=1, choices=OPE_TYPES, default="D", verbose_name="Type d'opération")
    src = models.ForeignKey(Person, on_delete=models.DO_NOTHING, verbose_name="Emetteur de l'opération", related_name="source_operations")
    dest = models.ForeignKey(Person, on_delete=models.DO_NOTHING, verbose_name="Receveur de l'opération", related_name="destination_operations")
    amount = models.FloatField(verbose_name="Montant")
    date_created = models.DateTimeField(verbose_name="Date d'ajout", editable=False, default=datetime.now)
    date = models.DateField(verbose_name="Date")

    def save(self, *args, **kwargs):
        # Check if it's a new object (not updating an existing one)
        if not self.pk:
            # Get the latest object to determine the next number
            last_object = Operation.objects.order_by('date_created').last()
            if last_object:
                last_pk = last_object.id
                last_number = int(last_pk.split('-')[1])
                print(last_number)
                new_number = last_number + 1
                self.id = f'OPE-{new_number}'
            else:
                self.id = 'OPE-1'
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.type} {self.date.strftime('%Y-%m-%d')} - {self.id} ({self.amount})"
        
    class Meta:
        verbose_name="Opération"

class Invoice(models.Model):
    title = models.CharField(verbose_name="Titre de la note de frais", max_length=255)
    date_created = models.DateTimeField(verbose_name="Date de création", auto_now_add=True, editable=False)
    project = models.ForeignKey(Project, verbose_name="Projet", on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=1, choices=STATUS, default="V", verbose_name="Statut")
    author = models.ForeignKey(Member, verbose_name="Auteur de la note de frais", on_delete=models.DO_NOTHING, null=True)
    role = models.CharField("Rôle sur le projet", max_length=255, null=True)
    comm = models.TextField(verbose_name="Commentaire", null=True, blank=True)
    total = models.CharField("Montant total", null=True, blank=True, editable=False, max_length=255)

    def __str__(self):
        return f"Note de frais #{self.pk} - {self.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        total_amount = 0
        for expense in self.expense_set.all():
            total_amount += expense.amount

        self.total = "%.2f" % total_amount
        super().save(*args, **kwargs)

    
    class Meta:
        verbose_name = "Note de frais"
        verbose_name_plural = "Notes de frais"

class Expense(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titre de la dépense")
    date = models.DateField(verbose_name="Date de la dépense")
    comm = models.TextField(verbose_name="Description de la dépense...", null=True, blank=True)
    amount = models.FloatField(verbose_name="Montant")
    author = models.ForeignKey(Member, verbose_name="Auteur de la dépense", on_delete=models.DO_NOTHING)
    proof = models.ImageField(verbose_name="Justificatif de paiement", null=True, blank=True, upload_to="img/proofs/")
    linked_invoice = models.ForeignKey(Invoice, verbose_name="Note de frais liée", null=True, blank=True, on_delete=models.DO_NOTHING)
    date_created = models.DateField(verbose_name="Date d'ajout", auto_now_add=True, editable=False)

    def __str__(self):
        return f"{self.title} ({self.amount}€) par {self.author.first_name()} {self.author.last_name()}"
    
    class Meta:
        verbose_name = "Dépense"