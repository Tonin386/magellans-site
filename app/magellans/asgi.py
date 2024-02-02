from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from . import consumers_routing
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'magellans.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            consumers_routing.websocket_urlpatterns
        ),
    )
})