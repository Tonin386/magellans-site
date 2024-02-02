from django.db import models
from members.models import *

class Project(models.Model):
    name = models.CharField("Nom", max_length=255)
    genre = models.CharField("Genre", max_length=255)
    duration = models.IntegerField("Durée en minutes")
    desc = models.TextField("Résumé")
    poster = models.ImageField(upload_to='img/')
    shoot_date = models.DateField("Date du tournage", blank=True, null=True)
    released_date = models.DateField("Date de sortie", blank=True, null=True)
    
    def __str__(self):
        return "Projet" + self.name
    
    class Meta:
        verbose_name = "Projet"
    
class RoleMap(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="Membre", related_name="roles")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Projet", related_name="team")
    role_name = models.CharField("Rôle", max_length=255)
    
    def __str__(self):
        return self.member + "|" + self.project + " : " + self.role_name
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['member', 'project'], name='unique_user_project_role')
        ]
        verbose_name = "Rôle"