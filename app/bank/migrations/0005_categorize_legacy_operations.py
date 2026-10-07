"""Catégorie des opérations de l'ancien site, devinée d'après leur libellé.

Seule la nouvelle colonne ``category`` est renseignée, et uniquement pour les
opérations restées en « Autre ». Le CA peut corriger chaque opération ensuite.
"""

import re
import unicodedata

from django.db import migrations

# (catégorie, type d'opération concerné ou None pour tous, motif) — la première règle qui correspond l'emporte.
RULES = [
    ("projects", None, r"cagnotte|proarti|pro arti|levee de fonds"),
    ("memberships", None, r"adhesion|helloasso"),
    ("fees", None, r"banque|frais bancaire|assurance|maif|ovh|hebergement|nom de domaine|abonnement"),
    ("grants", "C", r"ddfip|drfip|sgc|subvention|fsdie|crous|ville|region|departement"),
    ("projects", "D", r"transfert|trans fonds|aide|projet"),
    ("equipment", None, r"magasin|lightyshare|location materiel|achat materiel"),
    ("services", "C", r"prestation|decibulles|lysias|asls|tvh|rvte|production|cours"),
    ("events", None, r"\bago\b|pique.nique|narathon|hfp|festival"),
    ("reimbursements", "D", r"\bremb|note de frais"),
]


def normalize(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text.lower())


def guess(description, kind):
    text = normalize(description)
    for category, only_kind, pattern in RULES:
        if (only_kind is None or only_kind == kind) and re.search(pattern, text):
            return category
    return None


def forwards(apps, schema_editor):
    Operation = apps.get_model("bank", "Operation")
    for operation in Operation.objects.filter(category="other"):
        category = guess(operation.desc, operation.type)
        if category:
            Operation.objects.filter(pk=operation.pk).update(category=category)


def backwards(apps, schema_editor):
    pass  # les catégories devinées restent valables


class Migration(migrations.Migration):
    dependencies = [("bank", "0004_operation_categories")]

    operations = [migrations.RunPython(forwards, backwards)]
