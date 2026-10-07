"""Rendu Markdown sécurisé (contenus saisis par le CA ou les membres)."""

import markdown as md
import nh3
from django.utils.safestring import mark_safe

ALLOWED_TAGS = {
    "p", "br", "strong", "em", "b", "i", "u", "s", "a", "ul", "ol", "li", "blockquote",
    "code", "pre", "h2", "h3", "h4", "hr", "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}, "th": {"align"}, "td": {"align"}}


def render_markdown(text, *, inline=False):
    """Convertit du Markdown en HTML nettoyé (aucun script ni attribut dangereux)."""
    if not text:
        return mark_safe("")
    html = md.markdown(str(text), extensions=["extra", "sane_lists", "nl2br"], output_format="html")
    cleaned = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto", "tel"},
        link_rel="noopener noreferrer",
    )
    if inline and cleaned.startswith("<p>") and cleaned.endswith("</p>") and cleaned.count("<p>") == 1:
        cleaned = cleaned[3:-4]
    return mark_safe(cleaned)
