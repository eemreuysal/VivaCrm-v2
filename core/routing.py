"""
WebSocket URL routing configuration for VivaCRM v2.
"""
from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # Excel import progress tracking
    re_path(r'ws/imports/(?P<import_job_id>[^/]+)/$', consumers.ImportProgressConsumer.as_asgi()),
    
    # General notifications (future)
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]