"""Point d'entrée ASGI (conservé pour compatibilité ; la production utilise WSGI)."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "magellans.settings")

application = get_asgi_application()
