from django.db import models

STATUS_CHOICES = [
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

class Tag(models.Model):
    name = models.CharField("Tag", max_length=20)
    color = models.CharField("Couleur")
    
class Item(models.Model):
    name = models.CharField("Nom", max_length=255)
    tags = models.ManyToManyField(Tag)
    image = models.ImageField("Image", upload_to="img/items/", default="/img/items/default.png")
    max_stock = models.PositiveSmallIntegerField("Nombre possédés", default=1)
    state = models.IntegerField("Etat", choices=STATUS_CHOICES)
    buy_price = models.FloatField("Prix d'achat", blank=True, null=True)
    owner = models.CharField("Propriétaire", blank=True, null=True) #A changer...
    availability = models.IntegerField("Disponibilité", choices=AVAILABILITY_CHOICES)
    now_available = models.PositiveIntegerField("Nombre disponible", default=0)