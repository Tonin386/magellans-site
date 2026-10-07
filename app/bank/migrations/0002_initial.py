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
        ('bank', '0001_initial'),
        ('dashboard', '0001_initial'),
        ('members', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, verbose_name='Auteur de la dépense'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, verbose_name='Auteur de la note de frais'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='dashboard.project', verbose_name='Projet'),
        ),
        migrations.AddField(
            model_name='expense',
            name='linked_invoice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='bank.invoice', verbose_name='Note de frais liée'),
        ),
        migrations.AddField(
            model_name='operation',
            name='third_party',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='operations', to='members.person', verbose_name='Tiers'),
        ),
    ]
