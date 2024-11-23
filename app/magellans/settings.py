from dotenv import load_dotenv
from pathlib import Path
import logging
import os

load_dotenv()
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Static files (CSS, JavaScript, images)
STATIC_URL = '/static/'

DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400

# Additional directories where Django will look for static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / "assets",
]

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / "assets/media"

AUTH_USER_MODEL = 'members.Member'

LOGIN_REDIRECT_URL = '/membres/mon-profil'

LOGIN_URL = '/connexion/'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7cxr-qg^cmmmpun1x-q9136c3-w8a$@#$%yagj&s5sjob%t0^+'
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG") == str(1)
ALLOWED_HOSTS = ["django"]
CSRF_TRUSTED_ORIGINS = ['http://localhost', 'http://192.168.137.128', 'http://dev.magellans.fr']

if not DEBUG:
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALLOWED_HOSTS += ["*"]
    CSRF_TRUSTED_ORIGINS = ['https://*.magellans.fr', "https://magellans.fr"]
    STATICFILES_DIRS = []
    STATIC_ROOT = BASE_DIR / 'assets'

# Application definition

INSTALLED_APPS = [
    'daphne',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_registration',
    'members',
    'magellans',
    'showcase',
    'warehouse',
    'bank',
    'dashboard',
    'api',
    'channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware'
]

ROOT_URLCONF = 'magellans.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'members.context_processors.get_treasurer',
            ],
        },
    },
]
AUTH_USER_MODEL = 'members.Member'

WSGI_APPLICATION = 'magellans.wsgi.application'
ASGI_APPLICATION = 'magellans.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_DJANGO_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT')
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'asyncio': {
            'level': 'WARNING',
        },
    },
}

#Email configuration

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
DEFAULT_FROM_EMAIL = f'"Contact Magellans" <{EMAIL_RECEIVER}>'

TREASURER_PK = 1