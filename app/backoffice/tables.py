"""Tableaux de l'espace CA : recherche, filtres, tri et pagination côté serveur."""

import csv
from functools import reduce
from operator import or_

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse


def apply_search(queryset, query, fields):
    query = (query or "").strip()
    if not query:
        return queryset
    for word in query.split():
        queryset = queryset.filter(reduce(or_, (Q(**{f"{field}__icontains": word}) for field in fields)))
    return queryset


def table(request, queryset, *, search_fields=(), sorts=None, default_sort="", per_page=25):
    """Applique recherche + tri + pagination ; retourne le contexte du tableau.

    ``sorts`` : {"clé d'URL": "champ ORM"} (le préfixe « - » dans l'URL inverse l'ordre).
    """
    sorts = sorts or {}
    query = request.GET.get("q", "")
    queryset = apply_search(queryset, query, search_fields)
    sort = request.GET.get("tri") or default_sort
    key = sort.lstrip("-")
    if key in sorts:
        fields = sorts[key] if isinstance(sorts[key], (list, tuple)) else [sorts[key]]
        if sort.startswith("-"):
            fields = [f[1:] if f.startswith("-") else f"-{f}" for f in fields]
        queryset = queryset.order_by(*fields)
    paginator = Paginator(queryset, per_page)
    page = paginator.get_page(request.GET.get("page"))
    return {"page": page, "rows": page.object_list, "q": query, "sort": sort, "total": paginator.count}


def csv_response(filename, header, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("﻿")  # BOM : ouverture correcte des accents dans Excel
    writer = csv.writer(response, delimiter=";")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return response
