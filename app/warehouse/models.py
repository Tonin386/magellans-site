from members.models import Member
from django.db import models
import json

ITEM_STATUS_CHOICES = [
    (5, "Neuf"),
    (4, "Très bon état"),
    (3, "Bon état"),
    (2, "Etat moyen"),
    (1, "Mauvais état"),
    (0, "Maintenance"),
    (-1, "Ne fonctionne pas")
]

AVAILABILITY_CHOICES = [
    (1, "Disponible"),
    (2, "Loué"),
    (0, "Indisponible")
]

ORDER_STATUS_CHOICES = [
    (0, 'Commande non-effectuée'), #Order wasn't validated by the user
    (1, 'Commande effectuée & en attente de réponse'), #Order was validated and sent to the staff
    (2, 'Commande refusée'), #Order was declined by a staff member
    (3, 'Commande acceptée'), #Order was accepted by a staff member
    (4, 'Commande acceptée avec modifications') #Order was accepted by staff, but under modified conditions
]

class Tag(models.Model):
    name = models.CharField("Tag", max_length=20)
    color = models.CharField("Couleur", default="#000", max_length=10)
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Catégorie"
    
class Item(models.Model):
    name = models.CharField("Nom", max_length=255)
    tags = models.ManyToManyField(Tag, verbose_name="Tags")
    image = models.ImageField("Image", upload_to="img/items/", default="/img/items/default.png")
    max_stock = models.PositiveSmallIntegerField("Maximum disponible", default=1)
    now_available = models.PositiveIntegerField("Disponible(s)", default=0)
    state = models.IntegerField("Etat", choices=ITEM_STATUS_CHOICES)
    buy_price = models.FloatField("Prix d'achat", blank=True, null=True)
    owner = models.CharField("Propriétaire", blank=True, null=True) #A changer...
    availability = models.IntegerField("Disponibilité", choices=AVAILABILITY_CHOICES)
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Objet"
        
class Order(models.Model):
    date_start = models.DateTimeField("Début de la réservation", null=True, blank=True)
    date_end = models.DateTimeField("Fin de la réservation", null=True, blank=True)
    quantities = models.TextField(verbose_name="Quantité demandée pour chaque objet", null=False, blank=False, default="{}")
    message = models.TextField(verbose_name="Message personnalisé du demandeur", null=True, blank=True)
    answer_message = models.TextField(verbose_name="Messages de réponse", default="", blank=True)
    user = models.ForeignKey(Member, verbose_name="Demandeur", blank=True, null=True, on_delete=models.SET_NULL)
    pickup_first_name = models.TextField("Prénom de la personne chargée de récupérer la commande", max_length=255, blank=True, default="Non-renseigné")
    pickup_last_name = models.TextField("Nom de la personne chargée de récupérer la commande", max_length=255, blank=True, default="Non-renseigné")
    pickup_phone = models.TextField("Téléphone de la personne chargée de récupérer la commande", max_length=12, blank=True, default="Non-renseigné")
    status = models.IntegerField("Statut", choices=ORDER_STATUS_CHOICES, default=0)
    date_created = models.DateTimeField("Date commande effectuée", auto_now_add=True)
    date_validated = models.DateTimeField("Date commande validée", blank=True, null=True)
    tos = models.BooleanField("CGU acceptées", default=True)
    project_name = models.CharField("Projet", null=True, default="Non-renseigné", blank=True, max_length=255)
    sent_by_mail = models.BooleanField("Commande reçue par mail", default=False)
    notes = models.TextField("Notes concernant la commande", null=True, blank=True)
    
    def pickup_phone_formatted(self):
        if self.pickup_phone != "Non-renseigné" and self.pickup_phone:
            return ' '.join(self.pickup_phone[i:i+2] for i in range(0, len(self.pickup_phone), 2))
        return self.pickup_phone
    
    def load_quantities(self):
        return json.loads(self.quantities)  
     
    def __str__(self):
        if self.status == 0:
            return f"Réservation TEMPORAIRE de {self.user}"
        return f"Réservation de {self.user} : {self.date_start.strftime('%d/%m/%Y')} -> {self.date_end.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Réservation"