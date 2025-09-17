"""
System Analytics Models

Models for tracking system-wide metrics, API usage, resource consumption,
and operational health across the digital signage platform.
"""

import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class SystemMetrics(models.Model):
    """
    System-wide performance and health metrics.
    Tracks overall platform performance, resource usage, and operational health.
    """

    METRIC_CATEGORIES = [
        ('performance', 'Performance'),
        ('capacity', 'Capacity'),
        ('reliability', 'Reliability'),
        ('security', 'Security'),
        ('usage', 'Usage'),
        ('quality', 'Quality'),
    ]

    AGGREGATION_LEVELS = [
        ('instance', 'Instance Level'),
        ('tenant', 'Tenant Level'),
        ('global', 'Global Level'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Metric Information
    metric_name = models.CharField(max_length=100)
    metric_category = models.CharField(max_length=20, choices=METRIC_CATEGORIES)
    aggregation_level = models.CharField(max_length=20, choices=AGGREGATION_LEVELS, default='global')

    # Tenant (for tenant-level metrics)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='system_metrics'
    )

    # Metric Values
    value = models.DecimalField(max_digits=20, decimal_places=6)
    unit = models.CharField(max_length=50, blank=True)
    threshold_warning = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    threshold_critical = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)

    # Contextual Information
    component = models.CharField(max_length=100, blank=True)
    environment = models.CharField(max_length=50, default='production')
    region = models.CharField(max_length=50, blank=True)

    # Statistical Data
    min_value = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    max_value = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    avg_value = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    std_deviation = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)

    # Metadata
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    recorded_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_system_metrics'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_name', '-recorded_at']),
            models.Index(fields=['metric_category', '-recorded_at']),
            models.Index(fields=['aggregation_level', '-recorded_at']),
            models.Index(fields=['tenant', '-recorded_at']),
            models.Index(fields=['component', '-recorded_at']),
        ]

    def __str__(self):
        tenant_info = f" ({self.tenant.name})" if self.tenant else ""
        return f"{self.metric_name}: {self.value} {self.unit}{tenant_info}"

    def is_warning(self):
        """Check if metric value exceeds warning threshold."""
        return self.threshold_warning and self.value >= self.threshold_warning

    def is_critical(self):
        """Check if metric value exceeds critical threshold."""
        return self.threshold_critical and self.value >= self.threshold_critical


class ResourceUsage(models.Model):
    """
    Resource consumption tracking for infrastructure components.
    Monitors CPU, memory, storage, and network usage across the platform.
    """

    RESOURCE_TYPES = [
        ('cpu', 'CPU'),
        ('memory', 'Memory'),
        ('storage', 'Storage'),
        ('network', 'Network'),
        ('database', 'Database'),
        ('cache', 'Cache'),
        ('queue', 'Message Queue'),
    ]

    MEASUREMENT_UNITS = [
        ('percentage', 'Percentage'),
        ('bytes', 'Bytes'),
        ('operations', 'Operations'),
        ('requests', 'Requests'),
        ('connections', 'Connections'),
        ('count', 'Count'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Resource Information
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    resource_name = models.CharField(max_length=100)
    component = models.CharField(max_length=100)
    instance_id = models.CharField(max_length=100, blank=True)

    # Tenant (for tenant-specific resource usage)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='resource_usage'
    )

    # Usage Metrics
    current_usage = models.DecimalField(max_digits=20, decimal_places=6)
    peak_usage = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    average_usage = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    unit = models.CharField(max_length=20, choices=MEASUREMENT_UNITS)

    # Capacity Information
    total_capacity = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    available_capacity = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    utilization_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Thresholds
    warning_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=75)
    critical_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=90)

    # Growth Metrics
    growth_rate_daily = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    growth_rate_weekly = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    growth_rate_monthly = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Cost Information
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Metadata
    environment = models.CharField(max_length=50, default='production')
    region = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    measurement_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_resource_usage'
        ordering = ['-measurement_time']
        indexes = [
            models.Index(fields=['resource_type', '-measurement_time']),
            models.Index(fields=['component', '-measurement_time']),
            models.Index(fields=['tenant', '-measurement_time']),
            models.Index(fields=['utilization_percentage', '-measurement_time']),
        ]

    def __str__(self):
        tenant_info = f" ({self.tenant.name})" if self.tenant else ""
        return f"{self.resource_name}: {self.current_usage} {self.unit}{tenant_info}"

    def is_at_warning_level(self):
        """Check if resource usage is at warning level."""
        return self.utilization_percentage and self.utilization_percentage >= self.warning_threshold

    def is_at_critical_level(self):
        """Check if resource usage is at critical level."""
        return self.utilization_percentage and self.utilization_percentage >= self.critical_threshold


class APIUsage(models.Model):
    """
    API usage tracking and analytics.
    Monitors API endpoint usage, performance, and errors.
    """

    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS'),
    ]

    RESPONSE_CATEGORIES = [
        ('2xx', 'Success (2xx)'),
        ('3xx', 'Redirection (3xx)'),
        ('4xx', 'Client Error (4xx)'),
        ('5xx', 'Server Error (5xx)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # API Endpoint Information
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10, choices=HTTP_METHODS)
    api_version = models.CharField(max_length=10, blank=True)

    # Request Information
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='api_usage'
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_usage'
    )

    # Response Information
    response_status = models.IntegerField()
    response_category = models.CharField(max_length=3, choices=RESPONSE_CATEGORIES)
    response_time_ms = models.IntegerField()
    response_size_bytes = models.BigIntegerField(null=True, blank=True)

    # Request Details
    request_size_bytes = models.BigIntegerField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referer = models.URLField(blank=True)

    # Performance Metrics
    db_query_count = models.IntegerField(null=True, blank=True)
    db_query_time_ms = models.IntegerField(null=True, blank=True)
    cache_hits = models.IntegerField(default=0)
    cache_misses = models.IntegerField(default=0)

    # Error Information
    error_code = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    error_type = models.CharField(max_length=100, blank=True)

    # Rate Limiting
    rate_limit_remaining = models.IntegerField(null=True, blank=True)
    rate_limit_reset = models.DateTimeField(null=True, blank=True)
    was_rate_limited = models.BooleanField(default=False)

    # Authentication Information
    auth_method = models.CharField(max_length=50, blank=True)
    auth_success = models.BooleanField(default=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    request_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_api_usage'
        ordering = ['-request_time']
        indexes = [
            models.Index(fields=['endpoint', '-request_time']),
            models.Index(fields=['method', '-request_time']),
            models.Index(fields=['tenant', '-request_time']),
            models.Index(fields=['user', '-request_time']),
            models.Index(fields=['response_status', '-request_time']),
            models.Index(fields=['response_category', '-request_time']),
            models.Index(fields=['response_time_ms', '-request_time']),
        ]

    def __str__(self):
        tenant_info = f" ({self.tenant.name})" if self.tenant else ""
        return f"{self.method} {self.endpoint} - {self.response_status}{tenant_info}"

    def is_successful(self):
        """Check if the API request was successful."""
        return 200 <= self.response_status < 300

    def is_slow_request(self, threshold_ms=1000):
        """Check if the request was slower than the threshold."""
        return self.response_time_ms > threshold_ms


class ErrorLog(models.Model):
    """
    Comprehensive error logging and tracking.
    Captures application errors, exceptions, and system failures.
    """

    ERROR_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    ERROR_CATEGORIES = [
        ('application', 'Application Error'),
        ('system', 'System Error'),
        ('network', 'Network Error'),
        ('database', 'Database Error'),
        ('authentication', 'Authentication Error'),
        ('authorization', 'Authorization Error'),
        ('validation', 'Validation Error'),
        ('external', 'External Service Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Error Information
    error_level = models.CharField(max_length=20, choices=ERROR_LEVELS)
    error_category = models.CharField(max_length=20, choices=ERROR_CATEGORIES)
    error_code = models.CharField(max_length=100, blank=True)
    error_message = models.TextField()
    error_details = models.TextField(blank=True)

    # Exception Information
    exception_type = models.CharField(max_length=255, blank=True)
    exception_message = models.TextField(blank=True)
    stack_trace = models.TextField(blank=True)

    # Context Information
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs'
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs'
    )

    # Request Context
    request_url = models.URLField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_headers = models.JSONField(default=dict, blank=True)
    request_params = models.JSONField(default=dict, blank=True)

    # System Context
    component = models.CharField(max_length=100, blank=True)
    module = models.CharField(max_length=100, blank=True)
    function_name = models.CharField(max_length=100, blank=True)
    line_number = models.IntegerField(null=True, blank=True)

    # Environment Information
    environment = models.CharField(max_length=50, default='production')
    server_name = models.CharField(max_length=100, blank=True)
    process_id = models.IntegerField(null=True, blank=True)
    thread_id = models.CharField(max_length=50, blank=True)

    # Client Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)

    # Resolution Information
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_errors'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    # Occurrence Information
    occurrence_count = models.IntegerField(default=1)
    first_occurrence = models.DateTimeField(default=timezone.now)
    last_occurrence = models.DateTimeField(default=timezone.now)

    # Impact Assessment
    affected_users = models.IntegerField(default=0)
    affected_devices = models.IntegerField(default=0)
    downtime_minutes = models.IntegerField(default=0)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_error_logs'
        ordering = ['-last_occurrence']
        indexes = [
            models.Index(fields=['error_level', '-last_occurrence']),
            models.Index(fields=['error_category', '-last_occurrence']),
            models.Index(fields=['tenant', '-last_occurrence']),
            models.Index(fields=['component', '-last_occurrence']),
            models.Index(fields=['is_resolved', '-last_occurrence']),
            models.Index(fields=['occurrence_count', '-last_occurrence']),
        ]

    def __str__(self):
        return f"{self.error_level.upper()}: {self.error_message[:100]}"

    def resolve(self, user, notes=""):
        """Mark the error as resolved."""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()

    def increment_occurrence(self):
        """Increment the occurrence count and update last occurrence."""
        self.occurrence_count += 1
        self.last_occurrence = timezone.now()
        self.save()