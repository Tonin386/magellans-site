# Migration de référence (« baseline ») : schéma de la base tel qu'il existait
# au commit ebc7d7f, avant la refonte 2026. Sur une base de production existante,
# elle est marquée comme appliquée par `manage.py baseline_migrations` (sans rien
# exécuter) ; sur une base neuve elle est appliquée normalement.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='Tag')),
                ('color', models.CharField(default='#000', max_length=10, verbose_name='Couleur')),
            ],
            options={
                'verbose_name': 'Catégorie',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_start', models.DateTimeField(blank=True, null=True, verbose_name='Début de la réservation')),
                ('date_end', models.DateTimeField(blank=True, null=True, verbose_name='Fin de la réservation')),
                ('quantities', models.TextField(default='{}', verbose_name='Quantité demandée pour chaque objet')),
                ('message', models.TextField(blank=True, null=True, verbose_name='Message personnalisé du demandeur')),
                ('answer_message', models.TextField(blank=True, default='', verbose_name='Messages de réponse')),
                ('pickup_first_name', models.TextField(blank=True, default='Non-renseigné', max_length=255, verbose_name='Prénom de la personne chargée de récupérer la commande')),
                ('pickup_last_name', models.TextField(blank=True, default='Non-renseigné', max_length=255, verbose_name='Nom de la personne chargée de récupérer la commande')),
                ('pickup_phone', models.TextField(blank=True, default='Non-renseigné', max_length=12, verbose_name='Téléphone de la personne chargée de récupérer la commande')),
                ('status', models.IntegerField(choices=[(0, 'Commande non-effectuée'), (1, 'Commande effectuée & en attente de réponse'), (2, 'Commande refusée'), (3, 'Commande acceptée'), (4, 'Commande acceptée avec modifications'), (5, 'Commande avec contrat signé')], default=0, verbose_name='Statut')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date commande effectuée')),
                ('date_validated', models.DateTimeField(blank=True, null=True, verbose_name='Date commande validée')),
                ('tos', models.BooleanField(default=True, verbose_name='CGU acceptées')),
                ('project_name', models.CharField(blank=True, default='Non-renseigné', max_length=255, null=True, verbose_name='Projet')),
                ('sent_by_mail', models.BooleanField(default=False, verbose_name='Commande reçue par mail')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes concernant la commande')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Demandeur')),
            ],
            options={
                'verbose_name': 'Réservation',
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nom')),
                ('image', models.ImageField(default='/img/items/default.png', upload_to='img/items/', verbose_name='Image')),
                ('max_stock', models.PositiveSmallIntegerField(default=1, verbose_name='Maximum disponible')),
                ('now_available', models.PositiveIntegerField(default=0, verbose_name='Disponible(s)')),
                ('state', models.IntegerField(choices=[(5, 'Neuf'), (4, 'Très bon état'), (3, 'Bon état'), (2, 'Etat moyen'), (1, 'Mauvais état'), (0, 'Maintenance'), (-1, 'Ne fonctionne pas')], verbose_name='Etat')),
                ('buy_price', models.FloatField(blank=True, null=True, verbose_name="Prix d'achat")),
                ('owner', models.CharField(blank=True, null=True, verbose_name='Propriétaire')),
                ('availability', models.IntegerField(choices=[(1, 'Disponible'), (2, 'Loué'), (0, 'Indisponible')], verbose_name='Disponibilité')),
                ('tags', models.ManyToManyField(to='warehouse.tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'Objet',
            },
        ),
    ]
