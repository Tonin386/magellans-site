# Generated by Django 4.2.5 on 2023-10-08 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('showcase', '0004_alter_section_content'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='section',
            name='content',
        ),
        migrations.AddField(
            model_name='category',
            name='content',
            field=models.TextField(blank=True),
        ),
    ]
