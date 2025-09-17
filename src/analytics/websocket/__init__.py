"""
WebSocket Package for Real-time Analytics

Real-time monitoring and notification system using WebSockets.
Provides live updates for device status, alerts, and system metrics.
"""

from .consumers import (
    AnalyticsConsumer, DeviceMonitoringConsumer, AlertConsumer,
    DashboardConsumer, SystemMetricsConsumer
)
from .routing import websocket_urlpatterns
from .middleware import WebSocketAuthMiddleware
from .utils import broadcast_message, send_to_tenant, send_to_user

__all__ = [
    'AnalyticsConsumer', 'DeviceMonitoringConsumer', 'AlertConsumer',
    'DashboardConsumer', 'SystemMetricsConsumer',
    'websocket_urlpatterns', 'WebSocketAuthMiddleware',
    'broadcast_message', 'send_to_tenant', 'send_to_user'
]