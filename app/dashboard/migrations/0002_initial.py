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
        ('dashboard', '0001_initial'),
        ('members', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='director',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='directed_projects', to='members.person', verbose_name='Réalisateur.ice'),
        ),
        migrations.AddField(
            model_name='project',
            name='money_handler',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='handled_projects', to='members.person', verbose_name='Responsable financier'),
        ),
        migrations.AddField(
            model_name='projectfundingrequest',
            name='asker',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Demandeur'),
        ),
        migrations.AddField(
            model_name='rolemap',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='members.person', verbose_name='Coéquipier'),
        ),
        migrations.AddField(
            model_name='rolemap',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team', to='dashboard.project', verbose_name='Projet'),
        ),
        migrations.AddConstraint(
            model_name='rolemap',
            constraint=models.UniqueConstraint(fields=('person', 'project', 'role_name'), name='unique_user_project_role'),
        ),
    ]
