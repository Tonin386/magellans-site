"""Saisons passées (2021-2022 → 2024-2025), chacune liée à sa campagne d'adhésion HelloAsso.

Les adhésions elles-mêmes sont ensuite récupérées auprès de HelloAsso par
``manage.py helloasso_sync --all`` : pour une saison terminée, elles sont
enregistrées sans créer de compte ni envoyer d'e-mail.

La saison 2023-2024 a connu deux campagnes : « adhesion-2023-2024 » (premières
adhésions, puis désactivée) et « adhesion-magellans-2023-2024 ».

Aucune donnée existante n'est modifiée : une saison déjà présente est laissée telle quelle.
"""

import datetime
from decimal import Decimal

from django.db import migrations

BASE_URL = "https://www.helloasso.com/associations/magellans/adhesions/"

# (saison, campagne, campagnes secondaires, cotisation : None = prix libre)
PAST_SEASONS = [
    ("2021-2022", "adhesion-2021", [], Decimal("8.00")),
    ("2022-2023", "adhesion-2022-2023", [], None),
    ("2023-2024", "adhesion-magellans-2023-2024", ["adhesion-2023-2024"], None),
    ("2024-2025", "adhesions-2024-2025", [], Decimal("5.00")),
]


def forwards(apps, schema_editor):
    Season = apps.get_model("memberships", "Season")
    for label, slug, other_slugs, price in PAST_SEASONS:
        first = int(label[:4])
        Season.objects.get_or_create(
            label=label,
            defaults=dict(
                start_date=datetime.date(first, 9, 1),
                end_date=datetime.date(first + 1, 8, 31),
                is_current=False,
                registrations_open=False,
                helloasso_url=BASE_URL + slug,
                helloasso_org_slug="magellans",
                helloasso_form_type="Membership",
                helloasso_form_slug=slug,
                helloasso_other_urls="\n".join(BASE_URL + other for other in other_slugs),
                price=price,
            ),
        )


def backwards(apps, schema_editor):
    Season = apps.get_model("memberships", "Season")
    Season.objects.filter(label__in=[season[0] for season in PAST_SEASONS], memberships__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("memberships", "0003_season_other_campaigns"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
