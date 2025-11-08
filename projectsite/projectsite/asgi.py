import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import realsproj.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectsite.settings')

# This is the standard Django ASGI application for HTTP requests
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            realsproj.routing.websocket_urlpatterns
        )
    ),
})