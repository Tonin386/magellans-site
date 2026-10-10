"""Protection anti-robots sans service tiers (pas de reCAPTCHA, pas de cookie).

- un champ « pot de miel » invisible que seuls les robots remplissent ;
- un défi signé, horodaté et à usage unique : le navigateur doit retrouver par
  calcul (preuve de travail SHA-256, une fraction de seconde en arrière-plan) le
  nombre qui produit l'empreinte demandée. Les robots qui postent sans exécuter
  JavaScript échouent, ceux qui rejouent un défi déjà servi aussi ;
- un délai minimal entre l'affichage et l'envoi (les robots soumettent instantanément) ;
- une limite de débit par adresse IP (ou par clé), stockée dans le cache ;
- pour les messages libres, un filtre de contenu (liens, balises, vocabulaire du spam…).
"""

import hashlib
import re
import secrets
import time
import unicodedata

from django import forms
from django.core import signing
from django.core.cache import cache

from .utils import client_ip

MIN_SECONDS = 3
MAX_SECONDS = 60 * 60 * 6
SALT = "magellans.antispam"
# Le navigateur essaie en moyenne POW_MAX_NUMBER / 2 empreintes : ~0,5 s sur un
# ordinateur, quelques secondes sur un vieux téléphone (calcul lancé dès qu'on
# touche au formulaire, donc pendant la saisie).
POW_MAX_NUMBER = 100_000


def new_challenge(issued_at=None):
    """Défi de preuve de travail ; ``issued_at`` conserve l'heure du premier affichage."""
    salt = secrets.token_hex(12)
    number = secrets.randbelow(POW_MAX_NUMBER + 1)
    digest = hashlib.sha256(f"{salt}{number}".encode()).hexdigest()
    payload = {"salt": salt, "hash": digest, "t0": int(issued_at or time.time())}
    return {
        "token": signing.TimestampSigner(salt=SALT).sign_object(payload),
        "salt": salt,
        "hash": digest,
        "max": POW_MAX_NUMBER,
    }


class AntiSpamFormMixin(forms.Form):
    website = forms.CharField(required=False, label="Ne pas remplir", widget=forms.TextInput(
        attrs={"autocomplete": "off", "tabindex": "-1"}
    ))
    form_token = forms.CharField(required=False, widget=forms.HiddenInput)
    form_proof = forms.CharField(required=False, max_length=12, widget=forms.HiddenInput)

    antispam_min_seconds = MIN_SECONDS
    antispam_error = "Le formulaire n'a pas pu être validé. Merci de réessayer dans quelques secondes."
    antispam_proof_error = (
        "La vérification anti-robot n'a pas abouti. JavaScript doit être activé ; "
        "réessaie dans quelques secondes."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Chaque affichage reçoit un défi neuf (le précédent est consommé à l'envoi).
        # Après une erreur, on garde l'heure du premier affichage pour le délai minimal.
        previous = self._read_token(self.data.get("form_token")) if self.is_bound else None
        self.antispam = new_challenge(issued_at=previous["t0"] if previous else None)

    @staticmethod
    def _read_token(token):
        try:
            payload = signing.TimestampSigner(salt=SALT).unsign_object(token or "", max_age=MAX_SECONDS)
        except (signing.BadSignature, ValueError, TypeError):
            return None
        return payload if isinstance(payload, dict) and {"salt", "hash", "t0"} <= payload.keys() else None

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError(self.antispam_error, code="honeypot")
        payload = self._read_token(cleaned.get("form_token"))
        if payload is None:
            raise forms.ValidationError(self.antispam_error, code="token")
        proof = (cleaned.get("form_proof") or "").strip()
        if not proof.isdigit() or hashlib.sha256(f"{payload['salt']}{proof}".encode()).hexdigest() != payload["hash"]:
            raise forms.ValidationError(self.antispam_proof_error, code="proof")
        if time.time() - payload["t0"] < self.antispam_min_seconds:
            raise forms.ValidationError(self.antispam_error, code="too-fast")
        # Usage unique : un défi résolu ne sert qu'une fois, même depuis une autre adresse IP.
        if not cache.add(f"antispam:used:{payload['salt']}", 1, MAX_SECONDS):
            raise forms.ValidationError(self.antispam_error, code="replay")
        return cleaned


def rate_limited(request, scope, limit, period, key=None):
    """Retourne ``True`` si ``key`` (par défaut l'IP) a dépassé ``limit`` actions ``scope`` sur ``period`` secondes."""
    key = f"ratelimit:{scope}:{key or client_ip(request) or 'unknown'}"
    added = cache.add(key, 1, period)
    if added:
        return False
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, period)
        return False
    return count > limit


# --- Filtre de contenu ------------------------------------------------------------
# Chaque indice ajoute des points ; à partir de SPAM_THRESHOLD le message est refusé.
# Un seul indice faible (un lien, un message en anglais…) ne suffit jamais.
SPAM_THRESHOLD = 3

LINK_RE = re.compile(r"https?://|\bwww\.", re.IGNORECASE)
MARKUP_RE = re.compile(r"<\s*a\s|href\s*=|\[/?(?:url|link)\b", re.IGNORECASE)
# Noms générés par les logiciels de spam (« LauraDup », « JosephTeemy ») : prénom + suffixe collé.
GENERATED_NAME_RE = re.compile(r"^[A-Z][a-z]{2,}[A-Z][a-z]{1,}$")
SPAM_TERMS = [
    r"\bseo\b", r"\bback ?links?\b", r"\blink ?building\b", r"\bguest ?posts?\b", r"\bdomain authority\b",
    r"\bsearch engine optimi[sz]ation\b", r"\b(?:google|search) rankings?\b", r"\bfirst page (?:of|on) google\b",
    r"\b(?:website|web|organic) traffic\b", r"\blead generation\b", r"\bdigital marketing (?:agency|services)\b",
    r"\bweb ?design(?:ing)? services?\b", r"\bapp development\b", r"\bvirtual assistants?\b", r"\boutsourc",
    r"\bcrypto ?(?:currenc(?:y|ies)|trading|wallet)\b", r"\bbitcoin\b", r"\bforex\b", r"\bbinance\b",
    r"\bpassive income\b", r"\binvestment opportunit", r"\bcasinos?\b", r"\bbetting\b",
    r"\b(?:porn\w*|viagra|cialis|escorts?|xxx)\b", r"\bunsubscribe\b", r"\bopt[ -]?out\b",
    r"\b(?:know|ask about|asking about) your pric(?:e|es|ing)\b", r"\bréférencement (?:naturel|google|seo)\b",
]
SPAM_TERMS_RE = [re.compile(term, re.IGNORECASE) for term in SPAM_TERMS]
EN_WORDS = {"the", "you", "your", "and", "with", "for", "this", "that", "are", "have", "we", "our", "will", "can", "hi", "hello"}
FR_WORDS = {"le", "la", "les", "et", "est", "je", "vous", "nous", "pour", "une", "des", "pas", "que", "bonjour", "merci", "salut"}


def _non_latin_ratio(text):
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0
    foreign = sum(1 for char in letters if not unicodedata.name(char, "").startswith("LATIN"))
    return foreign / len(letters)


def spam_reasons(name, message):
    """Indices de spam relevés dans un message libre : ``[]`` si le message semble légitime."""
    score, reasons = 0, []

    def flag(points, reason):
        nonlocal score
        score += points
        reasons.append(reason)

    if LINK_RE.search(name) or "@" in name:
        flag(3, "lien ou adresse dans le nom")
    if MARKUP_RE.search(message):
        flag(3, "balises de lien (HTML / BBCode)")
    links = len(LINK_RE.findall(message))
    if links:
        flag(min(links, 3), f"{links} lien(s)")
    if _non_latin_ratio(f"{name} {message}") > 0.3:
        flag(3, "alphabet non latin")
    terms = sorted({match.group(0).lower() for pattern in SPAM_TERMS_RE for match in pattern.finditer(message)})
    if terms:
        flag(2 * len(terms), "vocabulaire de spam : " + ", ".join(terms))
    if GENERATED_NAME_RE.match(name.strip()):
        flag(2, "nom généré automatiquement")
    words = set(re.findall(r"[a-zà-ÿ]+", message.lower()))
    if len(words & EN_WORDS) >= 3 and not words & FR_WORDS:
        flag(1, "message en anglais")
    return reasons if score >= SPAM_THRESHOLD else []


def message_fingerprint(text):
    """Empreinte d'un message, insensible à la casse et aux espaces (détection des doublons)."""
    return hashlib.sha256(" ".join(text.lower().split()).encode()).hexdigest()
