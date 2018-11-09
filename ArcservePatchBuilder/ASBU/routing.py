from django.conf.urls import url
from . import consumers


websocket_urlpatterns = [
    url(r'^(?i)ws/asbu/[tp]\d{8}/$', consumers.ASBUStatusConsumer),
]