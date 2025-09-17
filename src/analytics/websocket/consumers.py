"""
WebSocket Consumers for Real-time Analytics

Handles WebSocket connections and real-time data streaming
for device monitoring, alerts, and system metrics.
"""

import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class BaseAnalyticsConsumer(AsyncWebsocketConsumer):
    """
    Base WebSocket consumer for analytics with common functionality.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant_id = None
        self.user_id = None
        self.subscriptions = set()

    async def connect(self):
        """Handle WebSocket connection."""
        # Check authentication
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return

        self.user_id = self.scope["user"].id
        self.tenant_id = await self.get_user_tenant_id()

        if not self.tenant_id:
            await self.close()
            return

        # Join tenant group
        await self.channel_layer.group_add(
            f"analytics_tenant_{self.tenant_id}",
            self.channel_name
        )

        await self.accept()

        # Send initial connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'tenant_id': self.tenant_id,
            'timestamp': timezone.now().isoformat()
        }))

        logger.info(f"WebSocket connected: user {self.user_id}, tenant {self.tenant_id}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.tenant_id:
            await self.channel_layer.group_discard(
                f"analytics_tenant_{self.tenant_id}",
                self.channel_name
            )

            # Leave all subscribed groups
            for subscription in self.subscriptions:
                await self.channel_layer.group_discard(
                    subscription,
                    self.channel_name
                )

        logger.info(f"WebSocket disconnected: user {self.user_id}, code {close_code}")

    async def receive(self, text_data):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'subscribe':
                await self.handle_subscription(data)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscription(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal error'
            }))

    async def handle_subscription(self, data):
        """Handle subscription to specific data streams."""
        subscription_type = data.get('subscription')
        if not subscription_type:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Missing subscription type'
            }))
            return

        group_name = f"{subscription_type}_tenant_{self.tenant_id}"

        # Add device-specific subscriptions
        if subscription_type.startswith('device_') and 'device_id' in data:
            group_name = f"{subscription_type}_{data['device_id']}_tenant_{self.tenant_id}"

        await self.channel_layer.group_add(group_name, self.channel_name)
        self.subscriptions.add(group_name)

        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'subscription': subscription_type,
            'group': group_name
        }))

    async def handle_unsubscription(self, data):
        """Handle unsubscription from data streams."""
        subscription_type = data.get('subscription')
        if not subscription_type:
            return

        group_name = f"{subscription_type}_tenant_{self.tenant_id}"

        if subscription_type.startswith('device_') and 'device_id' in data:
            group_name = f"{subscription_type}_{data['device_id']}_tenant_{self.tenant_id}"

        await self.channel_layer.group_discard(group_name, self.channel_name)
        self.subscriptions.discard(group_name)

        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'subscription': subscription_type
        }))

    @database_sync_to_async
    def get_user_tenant_id(self):
        """Get the tenant ID for the authenticated user."""
        try:
            if hasattr(self.scope["user"], 'tenant'):
                return str(self.scope["user"].tenant.id)
        except:
            pass
        return None

    # Channel layer message handlers
    async def analytics_message(self, event):
        """Handle analytics message from channel layer."""
        await self.send(text_data=json.dumps(event['data']))

    async def device_update(self, event):
        """Handle device update message."""
        await self.send(text_data=json.dumps({
            'type': 'device_update',
            'data': event['data']
        }))

    async def alert_notification(self, event):
        """Handle alert notification."""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'data': event['data']
        }))

    async def metric_update(self, event):
        """Handle metric update."""
        await self.send(text_data=json.dumps({
            'type': 'metric_update',
            'data': event['data']
        }))


class DeviceMonitoringConsumer(BaseAnalyticsConsumer):
    """
    WebSocket consumer for real-time device monitoring.
    Streams device health, status, and performance metrics.
    """

    async def connect(self):
        """Connect and set up device monitoring."""
        await super().connect()

        if self.tenant_id:
            # Subscribe to device monitoring group
            await self.channel_layer.group_add(
                f"device_monitoring_tenant_{self.tenant_id}",
                self.channel_name
            )

            # Send initial device status
            await self.send_initial_device_status()

    async def send_initial_device_status(self):
        """Send current status of all tenant devices."""
        devices = await self.get_tenant_devices()
        await self.send(text_data=json.dumps({
            'type': 'initial_device_status',
            'devices': devices,
            'timestamp': timezone.now().isoformat()
        }))

    @database_sync_to_async
    def get_tenant_devices(self):
        """Get current status of all tenant devices."""
        from ..models import Device
        try:
            devices = Device.objects.filter(tenant_id=self.tenant_id).values(
                'id', 'name', 'device_id', 'status', 'last_heartbeat',
                'device_type', 'location'
            )
            return list(devices)
        except:
            return []

    async def device_heartbeat(self, event):
        """Handle device heartbeat updates."""
        await self.send(text_data=json.dumps({
            'type': 'device_heartbeat',
            'device_id': event['device_id'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))

    async def device_health_update(self, event):
        """Handle device health updates."""
        await self.send(text_data=json.dumps({
            'type': 'device_health',
            'data': event['data']
        }))

    async def device_metrics_update(self, event):
        """Handle device metrics updates."""
        await self.send(text_data=json.dumps({
            'type': 'device_metrics',
            'data': event['data']
        }))


class AlertConsumer(BaseAnalyticsConsumer):
    """
    WebSocket consumer for real-time alert notifications.
    Handles alert delivery and acknowledgment.
    """

    async def connect(self):
        """Connect and set up alert monitoring."""
        await super().connect()

        if self.tenant_id:
            # Subscribe to alert notifications
            await self.channel_layer.group_add(
                f"alerts_tenant_{self.tenant_id}",
                self.channel_name
            )

            # Send active alerts
            await self.send_active_alerts()

    async def send_active_alerts(self):
        """Send currently active alerts."""
        alerts = await self.get_active_alerts()
        await self.send(text_data=json.dumps({
            'type': 'active_alerts',
            'alerts': alerts,
            'timestamp': timezone.now().isoformat()
        }))

    @database_sync_to_async
    def get_active_alerts(self):
        """Get active alerts for the tenant."""
        from ..models import Alert
        try:
            alerts = Alert.objects.filter(
                tenant_id=self.tenant_id,
                state='active'
            ).values(
                'id', 'title', 'message', 'severity', 'triggered_at',
                'device_id', 'alert_rule_id'
            )
            return list(alerts)
        except:
            return []

    async def new_alert(self, event):
        """Handle new alert notifications."""
        await self.send(text_data=json.dumps({
            'type': 'new_alert',
            'alert': event['alert'],
            'timestamp': timezone.now().isoformat()
        }))

    async def alert_acknowledged(self, event):
        """Handle alert acknowledgment notifications."""
        await self.send(text_data=json.dumps({
            'type': 'alert_acknowledged',
            'alert_id': event['alert_id'],
            'acknowledged_by': event['acknowledged_by'],
            'timestamp': event['timestamp']
        }))

    async def alert_resolved(self, event):
        """Handle alert resolution notifications."""
        await self.send(text_data=json.dumps({
            'type': 'alert_resolved',
            'alert_id': event['alert_id'],
            'resolved_by': event.get('resolved_by'),
            'auto_resolved': event.get('auto_resolved', False),
            'timestamp': event['timestamp']
        }))


class SystemMetricsConsumer(BaseAnalyticsConsumer):
    """
    WebSocket consumer for real-time system metrics.
    Streams system performance and health metrics.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics_task = None

    async def connect(self):
        """Connect and set up system metrics streaming."""
        await super().connect()

        if self.tenant_id:
            # Subscribe to system metrics
            await self.channel_layer.group_add(
                f"system_metrics_tenant_{self.tenant_id}",
                self.channel_name
            )

            # Start periodic metrics updates
            self.metrics_task = asyncio.create_task(
                self.periodic_metrics_update()
            )

    async def disconnect(self, close_code):
        """Disconnect and cleanup."""
        if self.metrics_task:
            self.metrics_task.cancel()
        await super().disconnect(close_code)

    async def periodic_metrics_update(self):
        """Send periodic system metrics updates."""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                metrics = await self.get_current_metrics()
                await self.send(text_data=json.dumps({
                    'type': 'system_metrics',
                    'metrics': metrics,
                    'timestamp': timezone.now().isoformat()
                }))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic metrics update: {e}")

    @database_sync_to_async
    def get_current_metrics(self):
        """Get current system metrics for the tenant."""
        from ..models import SystemMetrics, ResourceUsage
        try:
            # Get latest system metrics
            recent_time = timezone.now() - timedelta(minutes=5)

            system_metrics = SystemMetrics.objects.filter(
                tenant_id=self.tenant_id,
                recorded_at__gte=recent_time
            ).values(
                'metric_name', 'value', 'unit', 'recorded_at'
            )

            resource_usage = ResourceUsage.objects.filter(
                tenant_id=self.tenant_id,
                measurement_time__gte=recent_time
            ).values(
                'resource_type', 'current_usage', 'utilization_percentage',
                'measurement_time'
            )

            return {
                'system_metrics': list(system_metrics),
                'resource_usage': list(resource_usage)
            }
        except:
            return {'system_metrics': [], 'resource_usage': []}

    async def resource_alert(self, event):
        """Handle resource threshold alerts."""
        await self.send(text_data=json.dumps({
            'type': 'resource_alert',
            'resource': event['resource'],
            'current_usage': event['current_usage'],
            'threshold': event['threshold'],
            'timestamp': event['timestamp']
        }))


class DashboardConsumer(BaseAnalyticsConsumer):
    """
    WebSocket consumer for dashboard real-time updates.
    Aggregates and streams dashboard-specific data.
    """

    async def connect(self):
        """Connect and set up dashboard updates."""
        await super().connect()

        if self.tenant_id:
            # Subscribe to dashboard updates
            await self.channel_layer.group_add(
                f"dashboard_tenant_{self.tenant_id}",
                self.channel_name
            )

            # Send initial dashboard data
            await self.send_dashboard_summary()

    async def send_dashboard_summary(self):
        """Send dashboard summary data."""
        summary = await self.get_dashboard_summary()
        await self.send(text_data=json.dumps({
            'type': 'dashboard_summary',
            'data': summary,
            'timestamp': timezone.now().isoformat()
        }))

    @database_sync_to_async
    def get_dashboard_summary(self):
        """Get dashboard summary statistics."""
        from ..models import Device, Alert, ContentView
        try:
            # Get key dashboard metrics
            total_devices = Device.objects.filter(tenant_id=self.tenant_id).count()
            online_devices = Device.objects.filter(
                tenant_id=self.tenant_id,
                status='online'
            ).count()
            active_alerts = Alert.objects.filter(
                tenant_id=self.tenant_id,
                state='active'
            ).count()

            # Get today's content views
            today = timezone.now().date()
            content_views_today = ContentView.objects.filter(
                tenant_id=self.tenant_id,
                start_time__date=today
            ).count()

            return {
                'total_devices': total_devices,
                'online_devices': online_devices,
                'offline_devices': total_devices - online_devices,
                'active_alerts': active_alerts,
                'content_views_today': content_views_today,
                'device_uptime': round((online_devices / max(total_devices, 1)) * 100, 2)
            }
        except:
            return {
                'total_devices': 0,
                'online_devices': 0,
                'offline_devices': 0,
                'active_alerts': 0,
                'content_views_today': 0,
                'device_uptime': 0
            }

    async def dashboard_update(self, event):
        """Handle dashboard data updates."""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'widget': event.get('widget'),
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))


class AnalyticsConsumer(BaseAnalyticsConsumer):
    """
    Main analytics WebSocket consumer.
    Handles general analytics data streaming and notifications.
    """

    async def connect(self):
        """Connect and set up analytics streaming."""
        await super().connect()

        if self.tenant_id:
            # Subscribe to general analytics updates
            await self.channel_layer.group_add(
                f"analytics_general_tenant_{self.tenant_id}",
                self.channel_name
            )

    async def analytics_update(self, event):
        """Handle general analytics updates."""
        await self.send(text_data=json.dumps({
            'type': 'analytics_update',
            'category': event.get('category'),
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))

    async def performance_update(self, event):
        """Handle performance metrics updates."""
        await self.send(text_data=json.dumps({
            'type': 'performance_update',
            'data': event['data']
        }))

    async def usage_update(self, event):
        """Handle usage metrics updates."""
        await self.send(text_data=json.dumps({
            'type': 'usage_update',
            'data': event['data']
        }))