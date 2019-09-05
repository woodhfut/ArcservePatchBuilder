from django.conf.urls import url
from . import consumers


websocket_urlpatterns = [
    url(r'^(?i)ws/udp/[tp]\d{8}/$', consumers.UDPStatusConsumer),
]