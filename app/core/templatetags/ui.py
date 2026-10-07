"""Balises et filtres de gabarit disponibles partout (chargés en « builtins »)."""

from django import template
from django.templatetags.static import static
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.permissions import has_capability
from core.private_files import private_url as _private_url
from core.text import render_markdown
from core.utils import format_money, format_phone

register = template.Library()


@register.simple_tag
def icon(name, size="", css="", label=""):
    """Icône Lucide issue du sprite SVG : ``{% icon "calendar" css="size-5" %}``."""
    classes = " ".join(part for part in ["icon", size, css] if part)
    aria = format_html(' role="img" aria-label="{}"', label) if label else mark_safe(' aria-hidden="true"')
    return format_html(
        '<svg class="{}"{} focusable="false"><use href="{}#{}"></use></svg>',
        classes,
        aria,
        static("icons.svg"),
        name,
    )


@register.filter
def money(value, signed=False):
    return format_money(value, signed=bool(signed))


@register.filter
def phone(value):
    return format_phone(value) or "—"


@register.filter(name="markdown")
def markdown_filter(value):
    return render_markdown(value)


@register.simple_tag
def past_season_banners(limit=4):
    """Saisons passées ayant une bannière HelloAsso, de la plus récente à la plus ancienne."""
    from memberships.models import Season

    return list(Season.objects.exclude(banner="").filter(end_date__lt=timezone.localdate()).order_by("-start_date")[:limit])


@register.filter
def markdown_inline(value):
    return render_markdown(value, inline=True)


@register.filter
def can(user, capability):
    """``{% if request.user|can:"warehouse" %}``"""
    return has_capability(user, capability)


@register.filter
def private_url(obj, field_name):
    return _private_url(obj, field_name)


@register.filter
def initials(value):
    parts = [p for p in str(value or "").replace("-", " ").split() if p and p[0].isalpha()]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.simple_tag(takes_context=True)
def nav_active(context, *prefixes, exact=False):
    """Retourne ``aria-current="page"`` si l'URL courante correspond."""
    request = context.get("request")
    if request is None:
        return ""
    path = request.path
    for prefix in prefixes:
        if (exact and path == prefix) or (not exact and path.startswith(prefix)):
            return mark_safe('aria-current="page"')
    return ""


@register.filter
def youtube_id(url):
    """Identifiant d'une vidéo YouTube à partir de son URL (ou chaîne vide)."""
    from core.video import parse_video

    video = parse_video(url)
    return video["id"] if video and video["provider"] == "youtube" else ""


@register.filter
def video_embed(url):
    from core.video import parse_video

    return parse_video(url)


@register.simple_tag(takes_context=True)
def messages_json(context):
    """Messages Django (succès, erreurs…) transmis aux notifications « toast » de la page."""
    from django.contrib.messages import get_messages
    from django.utils.html import json_script

    request = context.get("request")
    if request is None:
        return ""
    tones = {"debug": "info", "info": "info", "success": "success", "warning": "warning", "error": "error"}
    items = [
        {"message": str(message), "tone": tones.get(message.level_tag, "info")}
        for message in get_messages(request)
    ]
    if not items:
        return ""
    return json_script(items, "initial-toasts")


@register.simple_tag
def first_words(text, count=1):
    """Sépare un titre : les ``count`` derniers mots servent à la mise en valeur."""
    words = str(text or "").split()
    return " ".join(words[:-count]) if len(words) > count else ""


@register.simple_tag
def last_words(text, count=1):
    words = str(text or "").split()
    return " ".join(words[-count:])


@register.filter
def blockquote(text):
    """Citation Markdown (chaque ligne préfixée par « > »), pour les e-mails."""
    return "\n".join(f"> {line}" if line.strip() else ">" for line in str(text or "").splitlines())
