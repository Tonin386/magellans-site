"""Mentions légales : ajout de la conception du site (Antonin MATHUBERT), avant « Hébergement ».

Seule la section est ajoutée, le reste du texte validé par le CA n'est pas modifié.
Sans effet si la page n'existe pas ou mentionne déjà l'auteur.
"""

from django.db import migrations

SECTION = "## Conception et réalisation\n\nLe site a été créé par **Antonin MATHUBERT**.\n\n"


def forwards(apps, schema_editor):
    Page = apps.get_model("core", "Page")
    page = Page.objects.filter(slug="mentions-legales").first()
    if page is None or "mathubert" in page.body.lower():
        return
    marker = "## Hébergement"
    if marker in page.body:
        page.body = page.body.replace(marker, SECTION + marker, 1)
    else:
        page.body = page.body.rstrip() + "\n\n" + SECTION.rstrip() + "\n"
    page.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_pages_validated"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
