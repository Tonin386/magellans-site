from members.models import Member
from django.db import models

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
    (0, 'Invalidée'), #Order wasn't validated by the user
    (1, 'Validée'), #Order was validated and sent to the staff
    (2, 'Refusée'), #Order was declined by a staff member
    (3, 'Acceptée') #Order was accepted by a staff member
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
    date_start = models.DateField("Début de la réservation")
    date_end = models.DateField("Fin de la réservation")
    items = models.ManyToManyField(Item, verbose_name="Objets réservés")
    user = models.ForeignKey(Member, verbose_name="Demandeur", blank=True, null=True, on_delete=models.SET_NULL)
    status = models.IntegerField("Statut", choices=ORDER_STATUS_CHOICES)
    
    def __str__(self):
        return f"Réservation de {self.user} : {self.date_start.strftime('%d/%m/%Y')} -> {self.date_end.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Réservation"