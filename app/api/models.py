from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from members.models import Member
from django.db import models

NOTIFICATION_STATUS = [
    (0, 'success'),
    (1, 'info'),
    (2, 'warning'),
    (3, 'danger')
]

APPLICATION_CHOICES = [
    (0, "API"),
    (1, "Trésorerie"),
    (2, "Gestionnaire"),
    (3, "Magellans"),
    (4, "Membres"),
    (5, "Vitrine"),
    (6, "Magasin")
]

class Notification(models.Model):
    title = models.CharField("Titre", max_length=255)
    subtitle = models.CharField("Sous-titre", max_length=255)
    application = models.PositiveSmallIntegerField("Application d'origine", choices=APPLICATION_CHOICES)
    status = models.PositiveSmallIntegerField("Statut", choices=NOTIFICATION_STATUS)
    message = models.TextField("Message")
    time = models.DateTimeField("Date et heure", auto_now_add=True)
    user = models.ForeignKey(Member, verbose_name="Auteur de l'action", blank=True, null=True, on_delete=models.SET_NULL)
    extra_field = models.TextField("Informations supplémentaires", blank=True, null=True)
    
    def show(self):
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            'notifications',
            {
                'type': 'emit_notification',
                'notification': dict(
                    id=self.pk,
                    title=self.title, 
                    subtitle=self.subtitle, 
                    application=self.application,
                    status=self.status,
                    message=self.message,
                    time=str(self.time)
                )
            }
        )