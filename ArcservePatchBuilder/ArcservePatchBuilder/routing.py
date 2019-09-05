from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import ASBU.routing
import UDP.routing

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            ASBU.routing.websocket_urlpatterns+UDP.routing.websocket_urlpatterns,
            
        ),
    ),
})