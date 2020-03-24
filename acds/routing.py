from django.conf.urls import url

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from chat.consumers import ChatConsumer
from devicelist.consumers import TopologyConsumer
from activator.consumers import VPNConsumer

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            url(r'^ws/chat/(?P<room_name>[^/]+)/$', ChatConsumer),
            url(r'^ws/topology/(?P<user_name>[^/]+)/$', TopologyConsumer),
            url(r'^ws/vpn/(?P<user_name>[^/]+)/$', VPNConsumer),
        ])
    ),
})





# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# import chat.routing
# import devicelist.routing

# application = ProtocolTypeRouter({
#     # (http->django views is added by default)
#     'websocket': AuthMiddlewareStack(
#         URLRouter(
#             chat.routing.websocket_urlpatterns
#         )
#     ),
# })