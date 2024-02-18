from django.db import models
from members.models import *
from django.utils.text import slugify

class Project(models.Model):
    name = models.CharField("Nom", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True, blank=True)
    genre = models.CharField("Genre", max_length=255)
    duration = models.IntegerField("Durée en minutes", null=True, blank=True)
    desc = models.TextField("Résumé explicatif de l'oeuvre ou du projet")
    short_desc = models.TextField("Courte phrase d'accroche pour le projet", null=True, blank=True)
    poster = models.ImageField(upload_to='img/projets/', default="img/projets/default.png")
    shoot_date = models.DateField("Date du tournage", blank=True, null=True)
    released_date = models.DateField("Date de sortie", blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug or self.slug != slugify(self.name):
            self.slug = slugify(self.name)
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return "Projet " + self.name
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