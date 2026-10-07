"""Création des saisons 2025-2026 et 2026-2027, et reprise des adhérent·es de l'ancien site.

Sur l'ancien site, être adhérent·e se traduisait par le rôle « M » (ou « Mx »),
remis à zéro manuellement chaque année. Ces personnes (ainsi que les membres du
CA) reçoivent une adhésion « reprise de l'ancien site » pour la saison 2025-2026.
Les adhésions HelloAsso exactes sont ensuite récupérées par la synchronisation
(``manage.py helloasso_sync``), qui complète ces fiches sans créer de doublon.

Aucune donnée existante n'est modifiée ni supprimée.
"""

import datetime
from decimal import Decimal

from django.db import migrations
from django.utils import timezone

LEGACY_MEMBER_ROLES = {"M", "Mx", "P", "C", "G", "T", "S", "W"}

DEFAULT_PITCH = (
    "Adhérer à Magellans, c'est :\n\n"
    "- **emprunter gratuitement le matériel** du magasin (caméras, son, lumière…) ;\n"
    "- **participer aux tournages** et rencontrer d'autres passionné·es ;\n"
    "- **demander une aide** humaine et financière pour tes projets ;\n"
    "- accéder aux **ressources** et aux évènements réservés aux membres."
)


def forwards(apps, schema_editor):
    Season = apps.get_model("memberships", "Season")
    Membership = apps.get_model("memberships", "Membership")
    Person = apps.get_model("members", "Person")

    previous, _ = Season.objects.get_or_create(
        label="2025-2026",
        defaults=dict(
            start_date=datetime.date(2025, 9, 1),
            end_date=datetime.date(2026, 8, 31),
            is_current=False,
            registrations_open=False,
            helloasso_url="https://www.helloasso.com/associations/magellans/adhesions/adhesions-2025-2026",
            helloasso_org_slug="magellans",
            helloasso_form_type="Membership",
            helloasso_form_slug="adhesions-2025-2026",
            price=Decimal("5.00"),
            pitch=DEFAULT_PITCH,
        ),
    )
    if not Season.objects.filter(is_current=True).exists():
        Season.objects.get_or_create(
            label="2026-2027",
            defaults=dict(
                start_date=datetime.date(2026, 9, 1),
                end_date=datetime.date(2027, 8, 31),
                is_current=True,
                registrations_open=True,
                helloasso_url="https://www.helloasso.com/beta/associations/magellans/adhesions/adhesions-2026-2027",
                helloasso_org_slug="magellans",
                helloasso_form_type="Membership",
                helloasso_form_slug="adhesions-2026-2027",
                price=Decimal("5.00"),
                pitch=DEFAULT_PITCH,
            ),
        )

    now = timezone.now()
    for person in Person.objects.filter(role__in=LEGACY_MEMBER_ROLES).select_related("site_profile"):
        if Membership.objects.filter(person=person, season=previous).exists():
            continue
        account = person.site_profile
        amount = Decimal(str(round(account.donation or 0, 2))) if account else Decimal("0")
        Membership.objects.create(
            person=person,
            season=previous,
            status="active",
            source="legacy",
            amount=amount,
            joined_at=getattr(account, "date_joined", None) or now,
            notes=f"Reprise automatique de l'ancien site (rôle « {person.role} »).",
        )


def backwards(apps, schema_editor):
    Membership = apps.get_model("memberships", "Membership")
    Season = apps.get_model("memberships", "Season")
    Membership.objects.filter(source="legacy").delete()
    Season.objects.filter(label__in=["2025-2026", "2026-2027"], memberships__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("memberships", "0001_initial"),
        ("members", "0003_board_roles_from_legacy_role"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
