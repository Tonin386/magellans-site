"""Reprise des anciennes réservations.

- Le contenu des réservations était stocké en JSON dans ``Order.quantities``
  (``{"<id objet>": {"count": 2, "available": true}}``) : il est recopié dans la
  nouvelle table ``OrderLine``.
- Les réponses du magasin étaient concaténées en HTML dans ``Order.answer_message`` :
  chaque réponse devient un message du nouveau fil de discussion.

Les colonnes d'origine sont conservées telles quelles.
"""

import datetime
import html
import json
import re

from django.db import migrations
from django.utils import timezone

ANSWER_DATE = re.compile(r"Réponse reçue le (\d{2})/(\d{2})/(\d{4}) à (\d{2}):(\d{2})")


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value):
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "", "non"}
    return bool(value)


def _html_to_text(fragment):
    text = re.sub(r"(?i)<br\s*/?>", "\n", fragment)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def forwards(apps, schema_editor):
    Order = apps.get_model("warehouse", "Order")
    OrderLine = apps.get_model("warehouse", "OrderLine")
    Item = apps.get_model("warehouse", "Item")
    Message = apps.get_model("core", "Message")
    ContentType = apps.get_model("contenttypes", "ContentType")

    item_ids = set(Item.objects.values_list("pk", flat=True))
    order_type, _ = ContentType.objects.get_or_create(app_label="warehouse", model="order")
    skipped = 0

    for order in Order.objects.all().iterator():
        # --- Lignes de réservation -------------------------------------------
        if not OrderLine.objects.filter(order_id=order.pk).exists():
            try:
                quantities = json.loads(order.quantities or "{}")
            except ValueError:
                quantities = {}
            if isinstance(quantities, dict):
                lines = []
                for key, value in quantities.items():
                    item_id = _to_int(key)
                    count = _to_int(value.get("count") if isinstance(value, dict) else value)
                    if count <= 0:
                        continue
                    if item_id not in item_ids:
                        skipped += 1
                        continue
                    available = _to_bool(value.get("available", True)) if isinstance(value, dict) else True
                    lines.append(
                        OrderLine(order_id=order.pk, item_id=item_id, quantity=min(count, 32767), available=available)
                    )
                OrderLine.objects.bulk_create(lines, ignore_conflicts=True)

        # --- Réponses du magasin ---------------------------------------------
        if order.answer_message and not Message.objects.filter(
            content_type=order_type, object_id=str(order.pk)
        ).exists():
            blocks = [block for block in re.split(r"(?i)<hr\s*/?>", order.answer_message) if block.strip()]
            for block in reversed(blocks):  # les réponses les plus récentes étaient en tête
                match = ANSWER_DATE.search(block)
                created_at = order.date_validated or order.date_created or timezone.now()
                if match:
                    day, month, year, hour, minute = (int(part) for part in match.groups())
                    try:
                        created_at = timezone.make_aware(datetime.datetime(year, month, day, hour, minute))
                    except ValueError:
                        pass
                    block = ANSWER_DATE.sub("", block, count=1)
                body = _html_to_text(block)
                if body:
                    Message.objects.create(
                        content_type=order_type,
                        object_id=str(order.pk),
                        body=body,
                        is_from_board=True,
                        created_at=created_at,
                    )
    if skipped:
        print(f"\n  ↳ {skipped} ligne(s) de réservation ignorée(s) : objet supprimé depuis.")


def backwards(apps, schema_editor):
    OrderLine = apps.get_model("warehouse", "OrderLine")
    OrderLine.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("warehouse", "0002_refonte_2026"),
        ("core", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
