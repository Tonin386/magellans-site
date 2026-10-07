"""Petits graphiques SVG générés côté serveur (aucune bibliothèque JavaScript).

Les coordonnées sont renvoyées sous forme de chaînes avec un point décimal :
le gabarit ne doit pas les « localiser » (« 12,5 » serait invalide en SVG).
"""

import datetime


def _n(value):
    return f"{float(value):.1f}"

from django.utils import timezone


def cumulative_series(dates, start, end, step_days=7):
    """Nombre cumulé d'événements à chaque pas de temps entre ``start`` et ``end``."""
    dates = sorted(d for d in dates if d)
    points, index, count = [], 0, 0
    day = start
    while day <= end:
        while index < len(dates) and dates[index] <= day:
            count += 1
            index += 1
        points.append((day, count))
        day += datetime.timedelta(days=step_days)
    return points


def line_chart(series, width=640, height=180, padding=24):
    """Construit les tracés SVG de plusieurs séries {label, points, tone}."""
    all_counts = [count for serie in series for _day, count in serie["points"]] or [0]
    max_count = max(max(all_counts), 1)
    longest = max((len(serie["points"]) for serie in series), default=1)
    inner_w, inner_h = width - padding * 2, height - padding * 2
    paths = []
    for serie in series:
        coords = []
        for i, (_day, count) in enumerate(serie["points"]):
            x = padding + (inner_w * i / max(longest - 1, 1))
            y = padding + inner_h - (inner_h * count / max_count)
            coords.append((float(_n(x)), float(_n(y))))
        if not coords:
            continue
        line = "M" + " L".join(f"{x},{y}" for x, y in coords)
        area = line + f" L{coords[-1][0]},{padding + inner_h} L{coords[0][0]},{padding + inner_h} Z"
        last = (_n(coords[-1][0]), _n(coords[-1][1]))
        paths.append({**serie, "line": line, "area": area, "last": last, "value": serie["points"][-1][1] if serie["points"] else 0})
    return {"width": width, "height": height, "paths": paths, "max": max_count, "baseline": _n(padding + inner_h)}


def _first_join_dates(season):
    """Date de première adhésion de chaque personne sur la saison (un double paiement compte une fois)."""
    firsts = {}
    for person_id, joined_at in season.memberships.active().values_list("person_id", "joined_at"):
        day = timezone.localtime(joined_at).date()
        firsts[person_id] = min(day, firsts.get(person_id, day))
    return list(firsts.values())


def season_progress(current, previous):
    """Courbes cumulées des adhésions : saison en cours vs précédente (même calendrier)."""
    today = timezone.localdate()
    series = []
    if current:
        end = min(today, current.end_date)
        dates = _first_join_dates(current)
        series.append({"label": current.label, "points": cumulative_series(dates, current.start_date, end), "tone": "amber"})
    if previous:
        offset = (today - current.start_date) if current else datetime.timedelta(days=365)
        end = min(previous.end_date, previous.start_date + offset)
        dates = _first_join_dates(previous)
        series.append({"label": previous.label, "points": cumulative_series(dates, previous.start_date, end), "tone": "ink"})
    return line_chart(series) if series else None


def monthly_bars(months, width=640, height=180, padding=24):
    """Barres crédits / débits par mois : months = [(label, credit, debit)]."""
    peak = max([max(c, d) for _l, c, d in months] + [1])
    inner_w, inner_h = width - padding * 2, height - padding * 2
    slot = inner_w / max(len(months), 1)
    bar = max(4, slot * 0.32)
    bars = []
    for i, (label, credit, debit) in enumerate(months):
        x = padding + slot * i + slot * 0.14
        ch = inner_h * float(credit) / float(peak)
        dh = inner_h * float(debit) / float(peak)
        bars.append(
            {
                "label": label,
                "credit": credit,
                "debit": debit,
                "cx": _n(x),
                "cy": _n(padding + inner_h - ch),
                "ch": _n(ch),
                "dx": _n(x + bar + 2),
                "dy": _n(padding + inner_h - dh),
                "dh": _n(dh),
                "w": _n(bar),
                "tx": _n(x + bar),
            }
        )
    return {"width": width, "height": height, "bars": bars, "baseline": _n(padding + inner_h)}
