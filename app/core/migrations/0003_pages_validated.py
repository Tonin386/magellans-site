"""Les textes proposés par défaut (mentions légales, confidentialité, conditions du magasin)
ont été validés par le CA : retrait de l'avertissement « à relire et valider par le CA ».

Seul ce paragraphe d'avertissement est retiré ; le reste du texte n'est pas modifié.
"""

import re

from django.db import migrations, models

REVIEW_NOTE = re.compile(r"\A\s*>[^\n]*valider par le CA[^\n]*(\r?\n>[^\n]*)*\s*")


def forwards(apps, schema_editor):
    Page = apps.get_model("core", "Page")
    for page in Page.objects.all():
        body = REVIEW_NOTE.sub("", page.body, count=1)
        if body != page.body or page.needs_review:
            page.body = body
            page.needs_review = False
            page.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_seed_content"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="page",
            name="needs_review",
            field=models.BooleanField(
                default=False,
                help_text="Tant que la case est cochée, un rappel s'affiche sur le tableau de bord du CA.",
                verbose_name="À relire",
            ),
        ),
    ]
