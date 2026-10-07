"""Historique : notifications de l'ancienne API (conservées, plus alimentées).

Les actions sont désormais tracées dans le journal d'activité (``core.ActivityLog``).
"""

from django.db import models

from members.models import Member

NOTIFICATION_STATUS = [
    (0, "success"),
    (1, "info"),
    (2, "warning"),
    (3, "danger"),
]

APPLICATION_CHOICES = [
    (0, "API"),
    (1, "Trésorerie"),
    (2, "Dashboard"),
    (3, "Magellans"),
    (4, "Membres"),
    (5, "Vitrine"),
    (6, "Magasin"),
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

    class Meta:
        verbose_name = "Notification (ancien site)"
        verbose_name_plural = "Notifications (ancien site)"

    def __str__(self):
        return self.time.strftime("%Y-%m-%d %H:%M:%S") + f" {self.title} - {self.application} ({self.status})"
