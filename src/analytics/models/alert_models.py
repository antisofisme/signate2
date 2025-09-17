"""
Alert and Notification Models

Models for managing alerting rules, notifications, and escalation policies
for the analytics and monitoring system.
"""

import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class NotificationChannel(models.Model):
    """
    Notification delivery channels for alerts and system notifications.
    Supports multiple delivery methods with configuration options.
    """

    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('push', 'Push Notification'),
        ('dashboard', 'Dashboard Notification'),
        ('mobile', 'Mobile App'),
    ]

    CHANNEL_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('rate_limited', 'Rate Limited'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Channel Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='notification_channels')
    name = models.CharField(max_length=255)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    status = models.CharField(max_length=20, choices=CHANNEL_STATUS, default='active')

    # Configuration
    configuration = models.JSONField(default=dict, blank=True)
    endpoint_url = models.URLField(blank=True)
    api_key = models.CharField(max_length=255, blank=True)

    # Email Configuration
    email_recipients = models.JSONField(default=list, blank=True)
    email_template = models.TextField(blank=True)

    # SMS Configuration
    phone_numbers = models.JSONField(default=list, blank=True)
    sms_template = models.TextField(blank=True)

    # Rate Limiting
    rate_limit_per_hour = models.IntegerField(default=100)
    rate_limit_per_day = models.IntegerField(default=1000)
    current_hour_count = models.IntegerField(default=0)
    current_day_count = models.IntegerField(default=0)
    last_reset_hour = models.DateTimeField(default=timezone.now)
    last_reset_day = models.DateTimeField(default=timezone.now)

    # Retry Configuration
    max_retries = models.IntegerField(default=3)
    retry_delay_seconds = models.IntegerField(default=300)  # 5 minutes
    backoff_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=2.0)

    # Health Metrics
    total_sent = models.BigIntegerField(default=0)
    total_failed = models.BigIntegerField(default=0)
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    average_delivery_time = models.IntegerField(null=True, blank=True)  # milliseconds

    # Metadata
    is_default = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'analytics_notification_channels'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'channel_type']),
            models.Index(fields=['status', 'channel_type']),
            models.Index(fields=['is_default', 'tenant']),
        ]

    def __str__(self):
        return f"{self.name} ({self.channel_type}) - {self.tenant.name}"

    def can_send_notification(self):
        """Check if channel can send notification based on rate limits."""
        now = timezone.now()

        # Reset hourly counter
        if (now - self.last_reset_hour).total_seconds() >= 3600:
            self.current_hour_count = 0
            self.last_reset_hour = now

        # Reset daily counter
        if (now - self.last_reset_day).total_seconds() >= 86400:
            self.current_day_count = 0
            self.last_reset_day = now

        return (
            self.status == 'active' and
            self.current_hour_count < self.rate_limit_per_hour and
            self.current_day_count < self.rate_limit_per_day
        )

    def record_notification_sent(self, success=True):
        """Record a notification attempt and update metrics."""
        self.current_hour_count += 1
        self.current_day_count += 1
        self.total_sent += 1
        self.last_used_at = timezone.now()

        if not success:
            self.total_failed += 1

        # Update success rate
        if self.total_sent > 0:
            self.success_rate = ((self.total_sent - self.total_failed) / self.total_sent) * 100

        self.save()


class AlertRule(models.Model):
    """
    Alert rules for automated monitoring and notification.
    Defines conditions and thresholds for triggering alerts.
    """

    RULE_TYPES = [
        ('threshold', 'Threshold Alert'),
        ('anomaly', 'Anomaly Detection'),
        ('trend', 'Trend Analysis'),
        ('composite', 'Composite Rule'),
        ('heartbeat', 'Heartbeat Monitoring'),
        ('error_rate', 'Error Rate'),
        ('performance', 'Performance Alert'),
    ]

    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    COMPARISON_OPERATORS = [
        ('gt', 'Greater Than'),
        ('gte', 'Greater Than or Equal'),
        ('lt', 'Less Than'),
        ('lte', 'Less Than or Equal'),
        ('eq', 'Equal To'),
        ('ne', 'Not Equal To'),
        ('between', 'Between'),
        ('outside', 'Outside Range'),
    ]

    AGGREGATION_FUNCTIONS = [
        ('avg', 'Average'),
        ('sum', 'Sum'),
        ('min', 'Minimum'),
        ('max', 'Maximum'),
        ('count', 'Count'),
        ('rate', 'Rate'),
        ('percentile', 'Percentile'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Rule Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='alert_rules')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='warning')

    # Rule Configuration
    metric_name = models.CharField(max_length=100)
    aggregation_function = models.CharField(max_length=20, choices=AGGREGATION_FUNCTIONS, default='avg')
    comparison_operator = models.CharField(max_length=20, choices=COMPARISON_OPERATORS, default='gt')
    threshold_value = models.DecimalField(max_digits=20, decimal_places=6)
    threshold_value_max = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)

    # Time Configuration
    evaluation_window = models.IntegerField(default=300)  # seconds
    evaluation_frequency = models.IntegerField(default=60)  # seconds
    minimum_duration = models.IntegerField(default=300)  # seconds

    # Filtering
    filters = models.JSONField(default=dict, blank=True)
    device_filters = models.JSONField(default=list, blank=True)
    content_filters = models.JSONField(default=list, blank=True)

    # Notification Configuration
    notification_channels = models.ManyToManyField(
        NotificationChannel,
        through='AlertRuleNotification',
        related_name='alert_rules'
    )

    # Escalation
    escalation_policy = models.ForeignKey(
        'EscalationPolicy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alert_rules'
    )

    # State Management
    is_active = models.BooleanField(default=True)
    is_paused = models.BooleanField(default=False)
    pause_until = models.DateTimeField(null=True, blank=True)

    # Alert Management
    auto_resolve = models.BooleanField(default=True)
    auto_resolve_timeout = models.IntegerField(default=3600)  # seconds
    suppress_duplicates = models.BooleanField(default=True)
    suppress_duration = models.IntegerField(default=1800)  # seconds

    # Performance Metrics
    evaluation_count = models.BigIntegerField(default=0)
    triggered_count = models.BigIntegerField(default=0)
    false_positive_count = models.BigIntegerField(default=0)
    last_evaluation = models.DateTimeField(null=True, blank=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    # Custom Logic
    custom_query = models.TextField(blank=True)
    custom_logic = models.JSONField(default=dict, blank=True)

    # Metadata
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_alert_rules'
    )
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_alert_rules'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['rule_type', 'severity']),
            models.Index(fields=['metric_name', 'is_active']),
            models.Index(fields=['last_evaluation']),
        ]

    def __str__(self):
        return f"{self.name} ({self.severity}) - {self.tenant.name}"

    def should_evaluate(self):
        """Check if rule should be evaluated based on frequency."""
        if not self.is_active or self.is_paused:
            return False

        if self.pause_until and self.pause_until > timezone.now():
            return False

        if not self.last_evaluation:
            return True

        time_since_last = (timezone.now() - self.last_evaluation).total_seconds()
        return time_since_last >= self.evaluation_frequency

    def calculate_accuracy(self):
        """Calculate rule accuracy based on false positive rate."""
        if self.triggered_count == 0:
            return 100

        true_positives = self.triggered_count - self.false_positive_count
        return (true_positives / self.triggered_count) * 100


class Alert(models.Model):
    """
    Alert instances generated by alert rules.
    Tracks the lifecycle of individual alerts from creation to resolution.
    """

    ALERT_STATES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('suppressed', 'Suppressed'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Alert Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='alerts')
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='alerts')

    # Alert Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=AlertRule.SEVERITY_LEVELS)
    state = models.CharField(max_length=20, choices=ALERT_STATES, default='active')

    # Triggering Data
    metric_value = models.DecimalField(max_digits=20, decimal_places=6)
    threshold_value = models.DecimalField(max_digits=20, decimal_places=6)
    evaluation_data = models.JSONField(default=dict, blank=True)

    # Context Information
    device = models.ForeignKey(
        'analytics.Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts'
    )
    content = models.ForeignKey(
        'anthias_app.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts'
    )

    # Alert Management
    acknowledged_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledgment_note = models.TextField(blank=True)

    resolved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)
    auto_resolved = models.BooleanField(default=False)

    # Notification Tracking
    notifications_sent = models.IntegerField(default=0)
    last_notification_at = models.DateTimeField(null=True, blank=True)
    escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)

    # Suppression
    is_suppressed = models.BooleanField(default=False)
    suppressed_until = models.DateTimeField(null=True, blank=True)
    suppression_reason = models.TextField(blank=True)

    # Impact Assessment
    affected_devices_count = models.IntegerField(default=0)
    affected_users_count = models.IntegerField(default=0)
    estimated_downtime = models.IntegerField(default=0)  # minutes
    business_impact = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low Impact'),
            ('medium', 'Medium Impact'),
            ('high', 'High Impact'),
            ('critical', 'Critical Impact'),
        ],
        default='low'
    )

    # Correlation
    correlation_id = models.CharField(max_length=100, blank=True)
    related_alerts = models.ManyToManyField('self', blank=True, symmetrical=False)
    root_cause_alert = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='caused_alerts'
    )

    # Metadata
    fingerprint = models.CharField(max_length=64, db_index=True)  # Hash for deduplication
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Timestamp
    triggered_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'analytics_alerts'
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['tenant', 'state', '-triggered_at']),
            models.Index(fields=['alert_rule', '-triggered_at']),
            models.Index(fields=['severity', 'state', '-triggered_at']),
            models.Index(fields=['device', '-triggered_at']),
            models.Index(fields=['fingerprint']),
            models.Index(fields=['correlation_id']),
        ]

    def __str__(self):
        return f"{self.title} ({self.severity}) - {self.state}"

    def acknowledge(self, user, note=""):
        """Acknowledge the alert."""
        self.state = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.acknowledgment_note = note
        self.save()

    def resolve(self, user=None, note="", auto_resolved=False):
        """Resolve the alert."""
        self.state = 'resolved'
        self.resolved_at = timezone.now()
        self.resolution_note = note
        self.auto_resolved = auto_resolved
        if user:
            self.resolved_by = user
        self.save()

    def suppress(self, duration_minutes=60, reason=""):
        """Suppress the alert for a specified duration."""
        self.is_suppressed = True
        self.suppressed_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.suppression_reason = reason
        self.save()

    def get_duration(self):
        """Get alert duration in seconds."""
        end_time = self.resolved_at or timezone.now()
        return int((end_time - self.triggered_at).total_seconds())


class EscalationPolicy(models.Model):
    """
    Escalation policies for alert management.
    Defines escalation rules and notification workflows.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Policy Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='escalation_policies')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Escalation Rules
    escalation_rules = models.JSONField(default=list, blank=True)
    default_timeout = models.IntegerField(default=1800)  # 30 minutes

    # Notification Configuration
    notification_channels = models.ManyToManyField(
        NotificationChannel,
        through='EscalationPolicyNotification',
        related_name='escalation_policies'
    )

    # Business Hours
    business_hours_only = models.BooleanField(default=False)
    business_hours_config = models.JSONField(default=dict, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')

    # Holiday Configuration
    respect_holidays = models.BooleanField(default=False)
    holiday_calendar = models.JSONField(default=list, blank=True)

    # Performance Metrics
    total_escalations = models.IntegerField(default=0)
    average_resolution_time = models.IntegerField(null=True, blank=True)  # minutes
    escalation_effectiveness = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Metadata
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_escalation_policies'
    )
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_escalation_policies'
        ordering = ['name']
        verbose_name_plural = 'Escalation policies'
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.tenant.name}"


class AlertRuleNotification(models.Model):
    """Through model for AlertRule and NotificationChannel relationship."""

    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE)
    notification_channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)

    # Notification settings for this specific rule-channel combination
    delay_seconds = models.IntegerField(default=0)
    max_notifications = models.IntegerField(default=10)
    notification_template = models.TextField(blank=True)

    class Meta:
        db_table = 'analytics_alert_rule_notifications'
        unique_together = [['alert_rule', 'notification_channel']]


class EscalationPolicyNotification(models.Model):
    """Through model for EscalationPolicy and NotificationChannel relationship."""

    escalation_policy = models.ForeignKey(EscalationPolicy, on_delete=models.CASCADE)
    notification_channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)

    # Escalation level configuration
    escalation_level = models.IntegerField(default=1)
    delay_minutes = models.IntegerField(default=30)

    class Meta:
        db_table = 'analytics_escalation_policy_notifications'
        unique_together = [['escalation_policy', 'notification_channel', 'escalation_level']]