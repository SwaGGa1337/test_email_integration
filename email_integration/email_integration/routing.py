from django.urls import re_path
from emails.consumers import EmailSyncConsumer

websocket_urlpatterns = [
    re_path(r'ws/emails/$', EmailSyncConsumer.as_asgi()),
] 