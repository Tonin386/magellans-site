# Migration de référence (« baseline ») : schéma de la base tel qu'il existait
# au commit ebc7d7f, avant la refonte 2026. Sur une base de production existante,
# elle est marquée comme appliquée par `manage.py baseline_migrations` (sans rien
# exécuter) ; sur une base neuve elle est appliquée normalement.

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Titre')),
                ('subtitle', models.CharField(max_length=255, verbose_name='Sous-titre')),
                ('application', models.PositiveSmallIntegerField(choices=[(0, 'API'), (1, 'Trésorerie'), (2, 'Dashboard'), (3, 'Magellans'), (4, 'Membres'), (5, 'Vitrine'), (6, 'Magasin')], verbose_name="Application d'origine")),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'success'), (1, 'info'), (2, 'warning'), (3, 'danger')], verbose_name='Statut')),
                ('message', models.TextField(verbose_name='Message')),
                ('time', models.DateTimeField(auto_now_add=True, verbose_name='Date et heure')),
                ('extra_field', models.TextField(blank=True, null=True, verbose_name='Informations supplémentaires')),
            ],
        ),
    ]
