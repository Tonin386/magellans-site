"""Protection anti-robots sans service tiers (pas de reCAPTCHA, pas de cookie).

- un champ « pot de miel » invisible que seuls les robots remplissent ;
- un jeton horodaté et signé : le formulaire doit avoir été affiché il y a plus
  de quelques secondes (les robots soumettent instantanément) ;
- une limite de débit par adresse IP, stockée dans le cache.
"""

from django import forms
from django.core import signing
from django.core.cache import cache

from .utils import client_ip

MIN_SECONDS = 3
MAX_SECONDS = 60 * 60 * 6
SALT = "magellans.antispam"


class AntiSpamFormMixin(forms.Form):
    website = forms.CharField(required=False, label="Ne pas remplir", widget=forms.TextInput(
        attrs={"autocomplete": "off", "tabindex": "-1"}
    ))
    form_token = forms.CharField(required=False, widget=forms.HiddenInput)

    antispam_error = "Le formulaire n'a pas pu être validé. Merci de réessayer dans quelques secondes."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["form_token"].initial = signing.TimestampSigner(salt=SALT).sign("ok")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError(self.antispam_error, code="honeypot")
        token = cleaned.get("form_token") or ""
        signer = signing.TimestampSigner(salt=SALT)
        try:
            signer.unsign(token, max_age=MAX_SECONDS)
        except signing.BadSignature:
            raise forms.ValidationError(self.antispam_error, code="token")
        try:
            signer.unsign(token, max_age=MIN_SECONDS)
        except signing.SignatureExpired:
            pass  # assez de temps s'est écoulé : tout va bien
        else:
            raise forms.ValidationError(self.antispam_error, code="too-fast")
        return cleaned


def rate_limited(request, scope, limit, period):
    """Retourne ``True`` si l'IP a dépassé ``limit`` actions ``scope`` sur ``period`` secondes."""
    key = f"ratelimit:{scope}:{client_ip(request) or 'unknown'}"
    added = cache.add(key, 1, period)
    if added:
        return False
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, period)
        return False
    return count > limit
