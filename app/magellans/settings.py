"""Configuration Django du site de l'association Magellans.

Toute la configuration sensible ou dépendante de l'environnement est lue depuis
les variables d'environnement (fichier ``app/.env`` en local et en production).
Voir ``app/.env.example`` pour la liste complète.
"""

import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().strip('"').strip("'")


def env_bool(name, default=False):
    value = env(name)
    if value is None or value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on", "oui"}


def env_list(name, default=""):
    value = env(name, default) or ""
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Sécurité de base
# ---------------------------------------------------------------------------
DEBUG = env_bool("DEBUG")
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "dev-insecure-secret-key-ne-pas-utiliser-en-production"
    else:
        raise ImproperlyConfigured("La variable d'environnement SECRET_KEY est obligatoire en production.")

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    # localhost : contrôles de santé internes (nginx rejette déjà tout nom d'hôte inconnu).
    "localhost,127.0.0.1,django" if DEBUG else "magellans.fr,www.magellans.fr,django,localhost,127.0.0.1",
)
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost,http://localhost:8000,http://127.0.0.1:8000"
    if DEBUG
    else "https://magellans.fr,https://www.magellans.fr",
)

# URL publique du site, utilisée pour construire les liens absolus des e-mails.
SITE_URL = env("SITE_URL", "http://localhost:8000" if DEBUG else "https://magellans.fr").rstrip("/")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Outils frontend
    "django_cotton",
    "django_vite",
    "django_htmx",
    # Applications Magellans
    "core",
    "members",
    "memberships",
    "showcase",
    "warehouse",
    "bank",
    "dashboard",
    "backoffice",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "core.middleware.MaintenanceModeMiddleware",
    "core.middleware.HtmxMessagesMiddleware",
]

ROOT_URLCONF = "magellans.urls"
WSGI_APPLICATION = "magellans.wsgi.application"
ASGI_APPLICATION = "magellans.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.csp",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site",
            ],
            "builtins": ["core.templatetags.ui"],
        },
    },
]

# ---------------------------------------------------------------------------
# Base de données
# ---------------------------------------------------------------------------
# En production (Docker) : PostgreSQL. En local sans Docker, si DB_HOST est vide,
# on bascule sur SQLite pour simplifier la prise en main.
if env("DB_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_DJANGO_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT", "5432"),
            "CONN_MAX_AGE": int(env("DB_CONN_MAX_AGE", "60")),
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Cache : table en base en production (partagée entre les workers gunicorn,
# sans service supplémentaire), mémoire locale en développement.
if env("CACHE_BACKEND", "locmem" if (DEBUG or TESTING) else "db") == "db":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "django_cache",
            # 300 entrées par défaut : une vague de robots effacerait les compteurs
            # anti-abus et les défis déjà utilisés (core/antispam.py).
            "OPTIONS": {"MAX_ENTRIES": 50_000},
        }
    }
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "members.Member"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "members:home"
LOGOUT_REDIRECT_URL = "home"
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 7  # 7 jours : utilisé aussi pour les invitations

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Fichiers statiques et médias
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    ("vite", BASE_DIR / "frontend" / "dist"),
]

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", str(BASE_DIR / "media")))

# Fichiers privés (justificatifs, dossiers d'aide, contrats, ressources membres) :
# jamais servis directement, uniquement via une vue Django qui contrôle les droits.
PRIVATE_MEDIA_ROOT = Path(env("PRIVATE_MEDIA_ROOT", str(BASE_DIR / "private")))
# "django" : la vue renvoie le fichier elle-même (développement).
# "nginx"  : la vue délègue l'envoi à nginx via X-Accel-Redirect (production).
PRIVATE_MEDIA_SERVER = env("PRIVATE_MEDIA_SERVER", "django" if DEBUG else "nginx")
PRIVATE_MEDIA_INTERNAL_URL = "/_protected/"

STORAGES = {
    "default": {"BACKEND": "core.storage.MediaStorage"},
    "private": {
        "BACKEND": "core.storage.MediaStorage",
        "OPTIONS": {"location": PRIVATE_MEDIA_ROOT, "base_url": None},
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if (DEBUG or TESTING)
        else "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 26 * 1024 * 1024
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # par fichier, contrôlé dans les formulaires

WHITENOISE_MAX_AGE = 60 * 60 * 24 * 30

# ---------------------------------------------------------------------------
# Frontend (Vite)
# ---------------------------------------------------------------------------
DJANGO_VITE = {
    "default": {
        "dev_mode": env_bool("VITE_DEV_MODE", False),
        "dev_server_port": int(env("VITE_DEV_PORT", "5173")),
        "manifest_path": BASE_DIR / "frontend" / "dist" / ".vite" / "manifest.json",
        "static_url_prefix": "vite",
    }
}

COTTON_DIR = "cotton"

# ---------------------------------------------------------------------------
# E-mails (réglage MAILERS introduit par Django 6.1)
# ---------------------------------------------------------------------------
if env("EMAIL_HOST"):
    _email_port = int(env("EMAIL_PORT", "587"))
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": env("EMAIL_HOST"),
                "port": _email_port,
                "username": env("EMAIL_HOST_USER"),
                "password": env("EMAIL_HOST_PASSWORD"),
                "use_tls": _email_port != 465,
                "use_ssl": _email_port == 465,
                "timeout": 20,
            },
        }
    }
else:
    MAILERS = {"default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}}

# Adresse d'expédition : on réutilise EMAIL_RECEIVER (ancienne configuration) si présent.
_sender = env("DEFAULT_FROM_EMAIL") or env("EMAIL_RECEIVER") or "contact@magellans.fr"
DEFAULT_FROM_EMAIL = _sender if "<" in _sender else f'"Magellans" <{_sender}>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_SUBJECT_PREFIX = "[Magellans] "

# ---------------------------------------------------------------------------
# Sécurité HTTP
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", str(60 * 60 * 24 * 365)))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False

_vite_dev = DJANGO_VITE["default"]["dev_mode"]
_vite_origin = f"http://localhost:{DJANGO_VITE['default']['dev_server_port']}"

# Content Security Policy (Django 6) : seuls nos scripts (ou ceux portant le nonce
# de la requête) peuvent s'exécuter. Les iframes autorisées sont HelloAsso et les
# lecteurs vidéo. Google Analytics n'est chargé qu'après consentement.
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE, "https://www.googletagmanager.com"]
    + ([_vite_origin] if _vite_dev else []),
    "style-src": [CSP.SELF] + ([_vite_origin, CSP.UNSAFE_INLINE] if _vite_dev else [CSP.NONCE]),
    # Attributs style="" (couleurs des tags, barres de progression…)
    "style-src-attr": [CSP.UNSAFE_INLINE],
    "img-src": [
        CSP.SELF,
        "data:",
        "blob:",
        "https://cdn.helloasso.com",
        "https://i.ytimg.com",
        "https://i.vimeocdn.com",
        "https://www.googletagmanager.com",
        "https://*.google-analytics.com",
    ],
    "font-src": [CSP.SELF] + ([_vite_origin] if _vite_dev else []),
    "media-src": [CSP.SELF, "blob:"],
    "connect-src": [
        CSP.SELF,
        "https://*.google-analytics.com",
        "https://*.analytics.google.com",
        "https://www.googletagmanager.com",
    ]
    + ([_vite_origin, _vite_origin.replace("http", "ws")] if _vite_dev else []),
    "frame-src": [
        "https://www.helloasso.com",
        "https://www.youtube-nocookie.com",
        "https://player.vimeo.com",
    ],
    "worker-src": [CSP.SELF, "blob:"],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
}

# ---------------------------------------------------------------------------
# HelloAsso
# ---------------------------------------------------------------------------
HELLOASSO = {
    "API_URL": env("HELLOASSO_API_URL", "https://api.helloasso.com").rstrip("/"),
    "CLIENT_ID": env("HELLOASSO_CLIENTID", ""),
    "CLIENT_SECRET": env("HELLOASSO_CLIENTSECRET", ""),
    "ORGANIZATION_SLUG": env("HELLOASSO_ORGANIZATION_SLUG", "magellans"),
    # Secret ajouté à l'URL du webhook (https://magellans.fr/api/helloasso/<secret>/).
    "WEBHOOK_SECRET": env("HELLOASSO_WEBHOOK_SECRET", ""),
    # IP d'émission des notifications HelloAsso (documentation officielle).
    "WEBHOOK_IPS": env_list("HELLOASSO_WEBHOOK_IPS", "51.138.206.200"),
}

# ---------------------------------------------------------------------------
# Journalisation
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "{asctime} {levelname} {name} — {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

if TESTING:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    PRIVATE_MEDIA_SERVER = "django"
