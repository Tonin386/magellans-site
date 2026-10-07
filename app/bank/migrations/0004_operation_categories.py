"""Catégorie par défaut des opérations existantes (nouvelle colonne uniquement)."""

from django.db import migrations


def forwards(apps, schema_editor):
    Operation = apps.get_model("bank", "Operation")
    Operation.objects.filter(type="R", category="other").update(category="reimbursements")


def backwards(apps, schema_editor):
    Operation = apps.get_model("bank", "Operation")
    Operation.objects.filter(category="reimbursements").update(category="other")


class Migration(migrations.Migration):
    dependencies = [("bank", "0003_refonte_2026")]

    operations = [migrations.RunPython(forwards, backwards)]
