"""
Device Analytics Models

Models for tracking device health, performance metrics, and operational status.
Includes real-time monitoring capabilities and multi-tenant device management.
"""

import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Device(models.Model):
    """
    Enhanced device model with analytics capabilities.
    Extends base device information with monitoring and health tracking.
    """

    DEVICE_TYPES = [
        ('display', 'Digital Display'),
        ('kiosk', 'Interactive Kiosk'),
        ('tablet', 'Tablet Display'),
        ('tv', 'Smart TV'),
        ('led', 'LED Board'),
        ('projector', 'Projector'),
        ('other', 'Other Device'),
    ]

    DEVICE_STATUS = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('maintenance', 'Maintenance'),
        ('error', 'Error'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='devices')

    # Basic Information
    name = models.CharField(max_length=255)
    device_id = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='display')
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Hardware Information
    hardware_info = models.JSONField(default=dict, blank=True)
    resolution = models.CharField(max_length=20, blank=True)
    orientation = models.CharField(max_length=20, default='landscape')

    # Network Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)

    # Status and Health
    status = models.CharField(max_length=20, choices=DEVICE_STATUS, default='unknown')
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)

    # Analytics Flags
    analytics_enabled = models.BooleanField(default=True)
    monitoring_enabled = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_devices'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['device_id']),
            models.Index(fields=['status', 'last_seen']),
            models.Index(fields=['device_type', 'tenant']),
        ]

    def __str__(self):
        return f"{self.name} ({self.device_id})"

    def is_online(self):
        """Check if device is considered online based on last heartbeat."""
        if not self.last_heartbeat:
            return False

        # Device is considered online if last heartbeat was within 5 minutes
        threshold = timezone.now() - timezone.timedelta(minutes=5)
        return self.last_heartbeat > threshold

    def get_health_score(self):
        """Calculate overall device health score (0-100)."""
        if not self.analytics_enabled:
            return None

        try:
            latest_health = self.health_records.latest('timestamp')
            return latest_health.health_score
        except DeviceHealth.DoesNotExist:
            return None


class DeviceHealth(models.Model):
    """
    Device health monitoring with comprehensive metrics.
    Tracks system performance, connectivity, and operational status.
    """

    HEALTH_STATUS = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='health_records')

    # Health Metrics
    health_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    status = models.CharField(max_length=20, choices=HEALTH_STATUS, default='unknown')

    # System Metrics
    cpu_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    memory_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    disk_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Network Metrics
    network_latency = models.IntegerField(null=True, blank=True)  # milliseconds
    network_quality = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bandwidth_usage = models.BigIntegerField(null=True, blank=True)  # bytes

    # Display Metrics
    display_errors = models.IntegerField(default=0)
    content_load_time = models.IntegerField(null=True, blank=True)  # milliseconds
    uptime = models.BigIntegerField(null=True, blank=True)  # seconds

    # Diagnostic Information
    error_count = models.IntegerField(default=0)
    warning_count = models.IntegerField(default=0)
    diagnostic_data = models.JSONField(default=dict, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_device_health'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['status', 'timestamp']),
            models.Index(fields=['health_score', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.device.name} Health: {self.health_score}% ({self.status})"


class DeviceMetrics(models.Model):
    """
    Detailed device performance metrics collected over time.
    Supports historical analysis and trend identification.
    """

    METRIC_TYPES = [
        ('performance', 'Performance'),
        ('usage', 'Usage'),
        ('error', 'Error'),
        ('network', 'Network'),
        ('display', 'Display'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='metrics')

    # Metric Information
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=15, decimal_places=4)
    metric_unit = models.CharField(max_length=50, blank=True)

    # Context and Metadata
    context = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Aggregation Support
    aggregation_period = models.CharField(
        max_length=20,
        choices=[
            ('raw', 'Raw Data'),
            ('minute', '1 Minute'),
            ('hour', '1 Hour'),
            ('day', '1 Day'),
        ],
        default='raw'
    )

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'analytics_device_metrics'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['device', 'metric_type', '-recorded_at']),
            models.Index(fields=['metric_name', '-recorded_at']),
            models.Index(fields=['aggregation_period', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.device.name}: {self.metric_name} = {self.metric_value} {self.metric_unit}"


class DeviceEvent(models.Model):
    """
    Device events and operational logs.
    Tracks important device state changes and operational events.
    """

    EVENT_TYPES = [
        ('startup', 'Device Startup'),
        ('shutdown', 'Device Shutdown'),
        ('connect', 'Network Connect'),
        ('disconnect', 'Network Disconnect'),
        ('content_change', 'Content Change'),
        ('error', 'Error Event'),
        ('warning', 'Warning Event'),
        ('maintenance', 'Maintenance Event'),
        ('update', 'Software Update'),
        ('configuration', 'Configuration Change'),
    ]

    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='events')

    # Event Information
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Event Data
    event_data = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=50, blank=True)

    # Source Information
    source_component = models.CharField(max_length=100, blank=True)
    source_version = models.CharField(max_length=50, blank=True)

    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    event_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'analytics_device_events'
        ordering = ['-event_time']
        indexes = [
            models.Index(fields=['device', '-event_time']),
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['severity', '-event_time']),
            models.Index(fields=['is_resolved', '-event_time']),
        ]

    def __str__(self):
        return f"{self.device.name}: {self.title} ({self.severity})"


class DeviceAlert(models.Model):
    """
    Device alerts and notifications.
    Manages automated alerts based on device health and performance thresholds.
    """

    ALERT_TYPES = [
        ('health', 'Health Alert'),
        ('performance', 'Performance Alert'),
        ('connectivity', 'Connectivity Alert'),
        ('error', 'Error Alert'),
        ('maintenance', 'Maintenance Alert'),
        ('threshold', 'Threshold Alert'),
    ]

    ALERT_STATES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('suppressed', 'Suppressed'),
    ]

    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alerts')

    # Alert Information
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    state = models.CharField(max_length=20, choices=ALERT_STATES, default='active')

    # Alert Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)

    # Threshold Information
    threshold_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    current_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    metric_name = models.CharField(max_length=100, blank=True)

    # Alert Management
    acknowledged_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_device_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    resolved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_device_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Notification Status
    notifications_sent = models.IntegerField(default=0)
    last_notification_at = models.DateTimeField(null=True, blank=True)
    escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_device_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['device', 'state', '-created_at']),
            models.Index(fields=['alert_type', 'priority']),
            models.Index(fields=['state', 'priority', '-created_at']),
            models.Index(fields=['escalated', '-created_at']),
        ]

    def __str__(self):
        return f"{self.device.name}: {self.title} ({self.priority})"

    def acknowledge(self, user):
        """Acknowledge the alert."""
        self.state = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()

    def resolve(self, user):
        """Resolve the alert."""
        self.state = 'resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()