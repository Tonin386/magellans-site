# Migration de référence (« baseline ») : schéma de la base tel qu'il existait
# au commit ebc7d7f, avant la refonte 2026. Sur une base de production existante,
# elle est marquée comme appliquée par `manage.py baseline_migrations` (sans rien
# exécuter) ; sur une base neuve elle est appliquée normalement.

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Titre de la dépense')),
                ('date', models.DateField(verbose_name='Date de la dépense')),
                ('comm', models.TextField(blank=True, null=True, verbose_name='Description de la dépense...')),
                ('amount', models.FloatField(verbose_name='Montant')),
                ('proof', models.FileField(blank=True, null=True, upload_to='img/proofs/', verbose_name='Justificatif de paiement')),
                ('date_created', models.DateField(auto_now_add=True, verbose_name="Date d'ajout")),
            ],
            options={
                'verbose_name': 'Dépense',
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Titre de la note de frais')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('status', models.CharField(choices=[('R', 'Remboursement effectué et confirmé'), ('X', 'Remboursement refusé'), ('F', 'A faire'), ('J', 'Justificatif(s) manquant(s)'), ('V', 'En attente de validation par le CA'), ('D', "Demande d'informations bancaires"), ('C', 'Virement en cours')], default='V', max_length=1, verbose_name='Statut')),
                ('role', models.CharField(max_length=255, null=True, verbose_name='Rôle sur le projet')),
                ('comm', models.TextField(blank=True, null=True, verbose_name='Commentaire')),
                ('total', models.CharField(blank=True, editable=False, max_length=255, null=True, verbose_name='Montant total')),
            ],
            options={
                'verbose_name': 'Note de frais',
                'verbose_name_plural': 'Notes de frais',
            },
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.CharField(editable=False, max_length=100, primary_key=True, serialize=False, unique=True, verbose_name='ID Opération')),
                ('desc', models.TextField(verbose_name='Description')),
                ('type', models.CharField(choices=[('C', 'Crédit'), ('D', 'Débit'), ('R', 'Remboursement')], default='D', max_length=1, verbose_name="Type d'opération")),
                ('amount', models.FloatField(verbose_name='Montant')),
                ('date_created', models.DateTimeField(default=datetime.datetime.now, editable=False, verbose_name="Date d'ajout")),
                ('date', models.DateField(verbose_name='Date')),
            ],
            options={
                'verbose_name': 'Opération',
            },
        ),
    ]
