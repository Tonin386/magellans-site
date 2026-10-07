"""Balises de l'espace CA."""

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.templatetags.ui import icon

register = template.Library()


@register.simple_tag(takes_context=True)
def sort_header(context, key, label, css=""):
    """En-tête de colonne triable : {% sort_header "nom" "Nom" %}."""
    request = context["request"]
    current = context.get("sort", "")
    params = request.GET.copy()
    params.pop("page", None)
    if current == key:
        params["tri"] = f"-{key}"
        arrow = icon("arrow-up", css="text-accent")
    elif current == f"-{key}":
        params["tri"] = key
        arrow = icon("arrow-down", css="text-accent")
    else:
        params["tri"] = key
        arrow = ""
    active = mark_safe(' aria-current="true"') if current.lstrip("-") == key else ""
    return format_html(
        '<a class="sort-link {}" href="?{}" hx-get="?{}" hx-target="#table" hx-push-url="true"{}>{}{}</a>',
        css,
        params.urlencode(),
        params.urlencode(),
        active,
        label,
        arrow,
    )


@register.simple_tag(takes_context=True)
def page_url(context, number):
    params = context["request"].GET.copy()
    params["page"] = number
    return f"?{params.urlencode()}"
