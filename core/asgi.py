"""
ASGI config for VivaCRM v2 project.

It exposes the ASGI callable as a module-level variable named ``application``.
This configuration includes both HTTP and WebSocket protocol support.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import core.routing

application = ProtocolTypeRouter({
    # HTTP protokolü için Django ASGI uygulaması
    "http": django_asgi_app,
    
    # WebSocket protokolü için Channels yapılandırması
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                core.routing.websocket_urlpatterns
            )
        )
    ),
})