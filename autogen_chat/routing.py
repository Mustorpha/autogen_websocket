from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ag-chat/<uuid:session_uuid>', consumers.AutogenConsumer.as_asgi())
]