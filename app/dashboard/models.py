from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import EmailMessage
from django.utils.text import slugify
from django.conf import settings
from django.db import models
from members.models import *

def dynamic_upload_path(instance, filename):
    return "funding_requests/" + slugify(instance.name) + "/" + filename

class ProjectFundingRequest(models.Model):
    name = models.CharField("Nom du projet", max_length=255)
    asker = models.ForeignKey(Member, verbose_name="Demandeur", blank=True, editable=False, null=True, on_delete=models.SET_NULL)
    role = models.CharField("Poste occupé sur le projet", max_length=255)
    directors = models.CharField("Réalisateur.ices", max_length=255)
    genre = models.CharField("Genre", max_length=255)
    duration = models.PositiveIntegerField("Durée en minutes estimée")
    production = models.CharField("Production", max_length=255)
    previsional_shoot_start_date = models.DateField("Date prévisionnelle du début du tournage")
    previsional_shoot_end_date = models.DateField("Date prévisionnelle de fin du tournage")
    explanation = models.TextField("Justification de la demande")
    funding_value = models.PositiveIntegerField("Montant demandé")
    deposit_date = models.DateTimeField("Date de dépôt du dossier", auto_now_add=True)
    script = models.FileField("Scénario", upload_to=dynamic_upload_path)
    intention_note = models.FileField("Note d'intention", upload_to=dynamic_upload_path)
    previsional_budget_plan = models.FileField("Plan de financement prévisionnel", upload_to=dynamic_upload_path)
    contact_list = models.FileField("Fiche contact", upload_to=dynamic_upload_path)

    def __str__(self):
        return f"Demande de financement {self.name} ({self.funding_value})"
    
    def send_by_email(self):
        subject = f"Nouvelle demande d'aide financière pour {self.name}"
        email_render = mark_safe(render_to_string("funding_request_email.html", {'instance': self}))

        email = EmailMessage(
            subject=subject,
            body=email_render,
            to=[settings.DEFAULT_FROM_EMAIL]
        )

        attached_files = []

        # Attach all FileField files to the email
        file_fields = [self.script, self.intention_note, self.previsional_budget_plan, self.contact_list]
        for file_field in file_fields:
            if file_field:
                email.attach_file(file_field.path)
                attached_files.append(file_field.name)

        email.send()
    
    class Meta:
        verbose_name = "Demande d'aide financière"
        verbose_name_plural = "Demandes d'aide financière"

class Project(models.Model):
    name = models.CharField("Nom", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True, blank=True, editable=False)
    genre = models.CharField("Genre", max_length=255, blank=True, default="Non-spécifié")
    desc = models.TextField("Résumé explicatif de l'oeuvre ou du projet")
    short_desc = models.TextField("Courte phrase d'accroche pour le projet", null=True, blank=True)
    poster = models.ImageField(upload_to='img/projects/', default="img/projects/default.png")
    shoot_date = models.DateField("Date du tournage", blank=True, null=True)
    release_date = models.DateField("Date de sortie", blank=True, null=True)
    director = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, verbose_name="Réalisateur.ice", related_name="directed_projects")
    money_handler = models.ForeignKey(Person, on_delete=models.SET_DEFAULT, default=settings.TREASURER_PK, verbose_name="Responsable financier", related_name="handled_projects")
    public = models.BooleanField("Projet public", default=False)
    
    def save(self, *args, **kwargs):
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