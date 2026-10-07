"""Fils de discussion attachés à un objet (réservation, note de frais, demande d'aide)."""

from django import forms
from django.contrib.contenttypes.models import ContentType

from .forms import StyledFormMixin
from .models import Message


class MessageForm(StyledFormMixin, forms.Form):
    body = forms.CharField(
        label="Message",
        max_length=4000,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Écris ton message…"}),
    )
    is_internal = forms.BooleanField(
        label="Note interne (invisible pour la personne concernée)", required=False
    )

    def __init__(self, *args, allow_internal=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not allow_internal:
            del self.fields["is_internal"]


def thread_for(obj, *, include_internal=False):
    content_type = ContentType.objects.get_for_model(obj)
    messages = Message.objects.filter(content_type=content_type, object_id=str(obj.pk)).select_related(
        "author", "author__site_person"
    )
    if not include_internal:
        messages = messages.filter(is_internal=False)
    return messages


def post_message(obj, *, author, body, is_internal=False, is_from_board=False):
    return Message.objects.create(
        content_type=ContentType.objects.get_for_model(obj),
        object_id=str(obj.pk),
        author=author,
        body=body.strip(),
        is_internal=is_internal,
        is_from_board=is_from_board,
    )
