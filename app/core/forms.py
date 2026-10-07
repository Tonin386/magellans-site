"""Outils communs aux formulaires : style homogène des champs."""

from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat

WIDGET_CLASSES = {
    forms.CheckboxInput: "checkbox",
    forms.RadioSelect: "radio",
    forms.CheckboxSelectMultiple: "checkbox",
    forms.Select: "select",
    forms.SelectMultiple: "select",
    forms.Textarea: "textarea",
    forms.ClearableFileInput: "input",
    forms.FileInput: "input",
}


class StyledFormMixin:
    """Ajoute les classes CSS du site aux widgets (input, select, textarea…)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css = "input"
            for widget_class, value in WIDGET_CLASSES.items():
                if isinstance(widget, widget_class):
                    css = value
                    break
            existing = widget.attrs.get("class", "")
            if css not in existing.split():
                widget.attrs["class"] = f"{css} {existing}".strip()
            if isinstance(widget, (forms.Select, forms.SelectMultiple)) and not isinstance(
                widget, (forms.RadioSelect, forms.CheckboxSelectMultiple)
            ):
                choices = getattr(field, "choices", None)
                try:
                    many = len(list(choices)) > 12 if choices is not None else False
                except TypeError:
                    many = False
                if many or isinstance(widget, forms.SelectMultiple):
                    widget.attrs.setdefault("data-searchable", "")


def validate_upload(uploaded, *, max_size=None, extensions=None):
    """Contrôle la taille et l'extension d'un fichier envoyé."""
    if not uploaded:
        return uploaded
    max_size = max_size or settings.MAX_UPLOAD_SIZE
    if uploaded.size > max_size:
        raise forms.ValidationError(f"Fichier trop volumineux ({filesizeformat(uploaded.size)}, maximum {filesizeformat(max_size)}).")
    if extensions:
        name = uploaded.name.lower()
        if not any(name.endswith(f".{ext}") for ext in extensions):
            raise forms.ValidationError(f"Format non accepté. Formats possibles : {', '.join(extensions)}.")
    return uploaded


DOCUMENT_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "webp", "heic"]
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif", "heic"]
