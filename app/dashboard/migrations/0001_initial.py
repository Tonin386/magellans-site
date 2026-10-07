# Migration de référence (« baseline ») : schéma de la base tel qu'il existait
# au commit ebc7d7f, avant la refonte 2026. Sur une base de production existante,
# elle est marquée comme appliquée par `manage.py baseline_migrations` (sans rien
# exécuter) ; sur une base neuve elle est appliquée normalement.

import dashboard.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nom')),
                ('slug', models.SlugField(blank=True, editable=False, max_length=255, unique=True, verbose_name='Slug')),
                ('genre', models.CharField(blank=True, default='Non-spécifié', max_length=255, verbose_name='Genre')),
                ('desc', models.TextField(verbose_name="Résumé explicatif de l'oeuvre ou du projet")),
                ('short_desc', models.TextField(blank=True, null=True, verbose_name="Courte phrase d'accroche pour le projet")),
                ('poster', models.ImageField(default='img/projects/default.png', upload_to='img/projects/')),
                ('shoot_date', models.DateField(blank=True, null=True, verbose_name='Date du tournage')),
                ('release_date', models.DateField(blank=True, null=True, verbose_name='Date de sortie')),
                ('public', models.BooleanField(default=False, verbose_name='Projet public')),
            ],
            options={
                'verbose_name': 'Projet',
            },
        ),
        migrations.CreateModel(
            name='ProjectFundingRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nom du projet')),
                ('role', models.CharField(max_length=255, verbose_name='Poste occupé sur le projet')),
                ('directors', models.CharField(max_length=255, verbose_name='Réalisateur.ices')),
                ('genre', models.CharField(max_length=255, verbose_name='Genre')),
                ('duration', models.PositiveIntegerField(verbose_name='Durée en minutes estimée')),
                ('production', models.CharField(max_length=255, verbose_name='Production')),
                ('previsional_shoot_start_date', models.DateField(verbose_name='Date prévisionnelle du début du tournage')),
                ('previsional_shoot_end_date', models.DateField(verbose_name='Date prévisionnelle de fin du tournage')),
                ('explanation', models.TextField(verbose_name='Justification de la demande')),
                ('funding_value', models.PositiveIntegerField(verbose_name='Montant demandé')),
                ('deposit_date', models.DateTimeField(auto_now_add=True, verbose_name='Date de dépôt du dossier')),
                ('script', models.FileField(upload_to=dashboard.models.dynamic_upload_path, verbose_name='Scénario')),
                ('intention_note', models.FileField(upload_to=dashboard.models.dynamic_upload_path, verbose_name="Note d'intention")),
                ('previsional_budget_plan', models.FileField(upload_to=dashboard.models.dynamic_upload_path, verbose_name='Plan de financement prévisionnel')),
                ('contact_list', models.FileField(upload_to=dashboard.models.dynamic_upload_path, verbose_name='Fiche contact')),
                ('sent_by_mail', models.BooleanField(default=False, verbose_name='Dossier reçu par mail')),
            ],
            options={
                'verbose_name': "Demande d'aide financière",
                'verbose_name_plural': "Demandes d'aide financière",
            },
        ),
        migrations.CreateModel(
            name='ResourceFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nom')),
                ('associated_file', models.FileField(upload_to='resources/', verbose_name='Fichier associé')),
                ('desc', models.TextField(blank=True, null=True, verbose_name='Description du fichier')),
                ('category', models.CharField(blank=True, max_length=255, null=True, verbose_name='Catégorie')),
            ],
            options={
                'verbose_name': 'Ressource',
            },
        ),
        migrations.CreateModel(
            name='RoleMap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_name', models.IntegerField(choices=[(1, 'Réalisateur.ice'), (2, 'Producteur.ice'), (3, 'Scénariste'), (4, 'Directeur.ice de la photographie'), (5, 'Monteur.euse'), (6, 'Designer sonore'), (7, 'Chef.fe décorateur.rice'), (8, 'Costumier.ière'), (9, 'Maquilleur.euse'), (10, 'Acteur.rice'), (11, 'Assistant.e réalisateur.ice'), (12, 'Assistant.e de production'), (13, 'Éclairagiste'), (14, 'Machiniste'), (15, 'Perchman'), (16, 'Compositeur.rice'), (17, 'Superviseur.euse des effets visuels'), (18, 'Coordinateur.rice des cascades'), (19, 'Directeur.ice de casting')], verbose_name='Rôle')),
            ],
            options={
                'verbose_name': 'Rôle',
            },
        ),
    ]
