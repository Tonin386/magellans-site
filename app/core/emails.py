"""Envoi d'e-mails mis en forme.

Chaque e-mail est un gabarit ``templates/emails/<nom>.html`` qui définit deux
*partials* (fonctionnalité de Django 6) :

- ``subject`` : l'objet du message ;
- ``body`` : le contenu, écrit en Markdown. Une ligne ``[[Libellé|URL]]`` devient
  un bouton dans la version HTML.

Le texte brut et la version HTML (mise en page aux couleurs de Magellans) sont
générés à partir de cette source unique.
"""

import html
import logging
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from .text import render_markdown

logger = logging.getLogger("magellans.emails")

BUTTON_LINE = re.compile(r"^\[\[(?P<label>[^|\]]+)\|(?P<url>[^\]]+)\]\]\s*$", re.MULTILINE)
MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def _clean_recipients(addresses):
    seen, result = set(), []
    for address in addresses or []:
        address = (address or "").strip()
        if address and "@" in address and address.lower() not in seen:
            seen.add(address.lower())
            result.append(address)
    return result


def _to_text(body):
    text = BUTTON_LINE.sub(lambda m: f"{m['label'].strip()} : {m['url'].strip()}", body)
    text = MD_LINK.sub(lambda m: f"{m.group(1)} ({m.group(2)})", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return text.strip() + "\n"


def _to_html(body):
    parts, last = [], 0
    for match in BUTTON_LINE.finditer(body):
        parts.append(str(render_markdown(body[last : match.start()])))
        parts.append(
            '<p style="margin:28px 0;"><a class="button" href="{url}" style="display:inline-block;'
            "background:#f5a524;color:#1a120b;font-weight:700;text-decoration:none;padding:12px 22px;"
            'border-radius:999px;">{label}</a></p>'.format(
                url=html.escape(match["url"].strip(), quote=True), label=html.escape(match["label"].strip())
            )
        )
        last = match.end()
    parts.append(str(render_markdown(body[last:])))
    return mark_safe("".join(parts))


def render_email(template, context):
    from .models import SiteSettings

    ctx = {"site": SiteSettings.load(), "site_url": settings.SITE_URL, **context}
    subject = " ".join(render_to_string(f"emails/{template}.html#subject", ctx).split())
    body = render_to_string(f"emails/{template}.html#body", ctx).strip()
    html_body = render_to_string(
        "emails/_layout.html", {**ctx, "subject": subject, "content": _to_html(body)}
    )
    return subject, _to_text(body), html_body


def send_templated_email(template, context, to, *, reply_to=None, cc=None, attachments=None):
    """Envoie un e-mail ; retourne ``True`` si l'envoi a réussi (sans jamais lever)."""
    recipients = _clean_recipients(to)
    if not recipients:
        return False
    try:
        subject, text_body, html_body = render_email(template, context)
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            to=recipients,
            cc=_clean_recipients(cc),
            reply_to=_clean_recipients(reply_to),
        )
        message.attach_alternative(html_body, "text/html")
        for name, content, mimetype in attachments or []:
            message.attach(name, content, mimetype)
        message.send()
        return True
    except Exception:
        logger.exception("Échec de l'envoi de l'e-mail « %s » à %s", template, recipients)
        return False
