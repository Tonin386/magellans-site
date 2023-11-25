from django.db import models
from members.models import Member

OPE_TYPES= [
    ('C', 'Crédit'),
    ('D', 'Débit'),
    ('R', 'Remboursement')
]

STATUS = [
    ('R', "Reçue"),
    ('P', "Prévisionnelle"),
    ('F', "A faire"),
    ('J', "En attente justificatif"),
    ('V', "En attente de validation CA"),
    ('D', "Demande des identifiants"),
    ('C', "Virement en cours")
]

class Operation(models.Model):
    id = models.CharField(primary_key=True, max_length=100, unique=True, verbose_name="ID Opération", editable=False)
    desc = models.TextField(verbose_name="Description")
    direction = models.CharField(max_length=1, choices=OPE_TYPES, default="D", verbose_name="Type d'opération")
    src = models.OneToOneField(Member, on_delete=models.DO_NOTHING, verbose_name="Emetteur de l'opération", related_name="source_operation")
    dest = models.OneToOneField(Member, on_delete=models.DO_NOTHING, verbose_name="Receveur de l'opération", related_name="destination_operation")
    amout = models.FloatField(verbose_name="Montant")
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout", editable=False)
    date = models.DateTimeField(verbose_name="Date")
    status = models.CharField(max_length=1, choices=STATUS, default="J", verbose_name="Statut")

    def save(self, *args, **kwargs):
        # Check if it's a new object (not updating an existing one)
        if not self.pk:
            # Get the latest object to determine the next number
            last_object = Operation.objects.last()
            if last_object:
                last_pk = last_object.id
                last_number = int(last_pk.split('-')[1])
                new_number = last_number + 1
                self.id = f'OPE-{new_number}'
            else:
                self.id = 'OPE-1'
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name="Opération"
        
        