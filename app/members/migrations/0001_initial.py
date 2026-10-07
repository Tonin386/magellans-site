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
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnregisteredMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Externe site',
                'verbose_name_plural': 'Externes site',
            },
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Courriel')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('is_staff', models.BooleanField(default=False, verbose_name='CA')),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")),
                ('donation', models.FloatField(default=0, verbose_name='Montant donation')),
                ('account', models.FloatField(default=0, verbose_name='Statut compte')),
                ('api_token', models.CharField(blank=True, editable=False, max_length=128, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Membre',
                'verbose_name_plural': 'Membres',
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Courriel')),
                ('first_name', models.CharField(blank=True, max_length=30, null=True, verbose_name='Prénom')),
                ('last_name', models.CharField(blank=True, max_length=30, null=True, verbose_name='Nom')),
                ('phone', models.CharField(blank=True, max_length=15, verbose_name='N° téléphone')),
                ('gender', models.CharField(blank=True, choices=[('M', 'Homme'), ('F', 'Femme'), ('B', 'Non-binaire'), ('O', 'Autre')], max_length=1, null=True, verbose_name='Sexe')),
                ('role', models.CharField(choices=[('P', 'Président.e'), ('C', 'Communication'), ('G', 'Gestionnaire magasin'), ('T', 'Trésorier.ère'), ('S', 'Secrétaire'), ('M', 'Membre Magellans & site'), ('Mx', 'Membre Magellans & pas site'), ('E', 'Inscrit site'), ('O', 'Organisation'), ('X', 'Externe site'), ('W', 'Webmaster')], default='X', max_length=2, verbose_name='Role')),
                ('additional_notes', models.TextField(blank=True, null=True, verbose_name='Notes supplémentaires')),
                ('site_profile', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='site_person', to=settings.AUTH_USER_MODEL, verbose_name='Profil site lié')),
                ('ext_profile', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ext_person', to='members.unregisteredmember', verbose_name='Profil externe lié')),
            ],
            options={
                'verbose_name': 'Personne',
            },
        ),
    ]
