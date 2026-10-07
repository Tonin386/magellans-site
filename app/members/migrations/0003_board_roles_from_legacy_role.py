"""Reprise des rôles de l'ancien site (champ ``role``, conservé intact).

- rôles CA (P, C, G, T, S, W) → ``board_roles`` ;
- « Organisation » (O) → ``kind = organisation``.

Opération uniquement additive : seules les nouvelles colonnes sont renseignées.
"""

from django.db import migrations

LEGACY_BOARD = {"P", "C", "G", "T", "S", "W"}
PLACEHOLDERS = {"", "inconnu", "indéfini", "non-renseigné"}


def forwards(apps, schema_editor):
    Person = apps.get_model("members", "Person")
    for person in Person.objects.filter(role__in=LEGACY_BOARD):
        person.board_roles = sorted(set(person.board_roles or []) | {person.role})
        person.save(update_fields=["board_roles"])
    for person in Person.objects.filter(role="O"):
        name = " ".join(
            part.strip()
            for part in [person.first_name or "", person.last_name or ""]
            if part and part.strip().lower() not in PLACEHOLDERS
        )
        person.kind = "organisation"
        person.organisation_name = person.organisation_name or name[:200]
        person.save(update_fields=["kind", "organisation_name"])


def backwards(apps, schema_editor):
    Person = apps.get_model("members", "Person")
    Person.objects.update(board_roles=[], kind="individual", organisation_name="")


class Migration(migrations.Migration):
    dependencies = [("members", "0002_refonte_2026")]

    operations = [migrations.RunPython(forwards, backwards)]
