"""
Report and Reporting Models

Models for managing automated reports, report templates, scheduling,
and report execution tracking for the analytics dashboard.
"""

import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class ReportTemplate(models.Model):
    """
    Report templates for standardized reporting.
    Defines reusable report structures and configurations.
    """

    TEMPLATE_TYPES = [
        ('dashboard', 'Dashboard Report'),
        ('performance', 'Performance Report'),
        ('usage', 'Usage Analytics'),
        ('financial', 'Financial Report'),
        ('device', 'Device Health Report'),
        ('content', 'Content Analytics'),
        ('user', 'User Activity Report'),
        ('compliance', 'Compliance Report'),
        ('custom', 'Custom Report'),
    ]

    TEMPLATE_CATEGORIES = [
        ('operational', 'Operational'),
        ('strategic', 'Strategic'),
        ('compliance', 'Compliance'),
        ('financial', 'Financial'),
        ('technical', 'Technical'),
    ]

    OUTPUT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('html', 'HTML'),
        ('dashboard', 'Interactive Dashboard'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Template Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='report_templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORIES, default='operational')

    # Template Configuration
    data_sources = models.JSONField(default=list, blank=True)
    metrics = models.JSONField(default=list, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    grouping = models.JSONField(default=list, blank=True)
    sorting = models.JSONField(default=list, blank=True)

    # Visualization Configuration
    charts = models.JSONField(default=list, blank=True)
    tables = models.JSONField(default=list, blank=True)
    layout = models.JSONField(default=dict, blank=True)

    # Output Configuration
    supported_formats = models.JSONField(default=list, blank=True)
    default_format = models.CharField(max_length=20, choices=OUTPUT_FORMATS, default='pdf')

    # Template Content
    template_content = models.TextField(blank=True)  # HTML/template content
    css_styles = models.TextField(blank=True)
    javascript = models.TextField(blank=True)

    # Query Configuration
    sql_queries = models.JSONField(default=dict, blank=True)
    api_endpoints = models.JSONField(default=list, blank=True)
    aggregation_rules = models.JSONField(default=dict, blank=True)

    # Access Control
    is_public = models.BooleanField(default=False)
    allowed_roles = models.JSONField(default=list, blank=True)
    allowed_users = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='accessible_report_templates'
    )

    # Versioning
    version = models.CharField(max_length=20, default='1.0')
    parent_template = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_templates'
    )

    # Usage Metrics
    usage_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    average_generation_time = models.IntegerField(null=True, blank=True)  # seconds

    # Metadata
    is_active = models.BooleanField(default=True)
    is_system_template = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_templates'
    )
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_report_templates'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'template_type']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_public', 'is_active']),
            models.Index(fields=['usage_count', '-last_used_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.template_type}) - {self.tenant.name}"

    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])


class ReportSchedule(models.Model):
    """
    Automated report scheduling configuration.
    Manages when and how reports are automatically generated and distributed.
    """

    SCHEDULE_TYPES = [
        ('once', 'One-time'),
        ('recurring', 'Recurring'),
        ('triggered', 'Event Triggered'),
        ('conditional', 'Conditional'),
    ]

    FREQUENCY_TYPES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Cron'),
    ]

    SCHEDULE_STATUS = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Schedule Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='report_schedules')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Schedule Configuration
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES, default='recurring')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_TYPES, default='daily')
    cron_expression = models.CharField(max_length=100, blank=True)

    # Timing Configuration
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    # Time Zone
    timezone = models.CharField(max_length=50, default='UTC')

    # Report Configuration
    output_format = models.CharField(max_length=20, choices=ReportTemplate.OUTPUT_FORMATS, default='pdf')
    custom_filters = models.JSONField(default=dict, blank=True)
    custom_parameters = models.JSONField(default=dict, blank=True)

    # Distribution Configuration
    recipients = models.JSONField(default=list, blank=True)
    notification_channels = models.ManyToManyField(
        'analytics.NotificationChannel',
        blank=True,
        related_name='report_schedules'
    )

    # Storage Configuration
    storage_location = models.CharField(max_length=255, blank=True)
    retain_reports = models.BooleanField(default=True)
    retention_days = models.IntegerField(default=90)
    auto_cleanup = models.BooleanField(default=True)

    # Conditional Execution
    execution_conditions = models.JSONField(default=dict, blank=True)
    data_freshness_required = models.IntegerField(default=24)  # hours

    # Error Handling
    max_retries = models.IntegerField(default=3)
    retry_delay_minutes = models.IntegerField(default=30)
    failure_notification = models.BooleanField(default=True)

    # Status and Metrics
    status = models.CharField(max_length=20, choices=SCHEDULE_STATUS, default='active')
    execution_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    last_execution_duration = models.IntegerField(null=True, blank=True)  # seconds

    # Metadata
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_schedules'
    )
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_report_schedules'
        ordering = ['-next_run_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['template', 'status']),
            models.Index(fields=['next_run_at', 'status']),
            models.Index(fields=['frequency', 'status']),
        ]

    def __str__(self):
        return f"{self.name} - {self.frequency} - {self.tenant.name}"

    def is_due(self):
        """Check if the schedule is due for execution."""
        if self.status != 'active' or not self.next_run_at:
            return False
        return timezone.now() >= self.next_run_at

    def calculate_next_run(self):
        """Calculate the next run time based on frequency."""
        if self.schedule_type == 'once':
            return None

        now = timezone.now()
        if self.frequency == 'hourly':
            return now + timezone.timedelta(hours=1)
        elif self.frequency == 'daily':
            return now + timezone.timedelta(days=1)
        elif self.frequency == 'weekly':
            return now + timezone.timedelta(weeks=1)
        elif self.frequency == 'monthly':
            return now + timezone.timedelta(days=30)
        elif self.frequency == 'quarterly':
            return now + timezone.timedelta(days=90)
        elif self.frequency == 'yearly':
            return now + timezone.timedelta(days=365)

        return None


class Report(models.Model):
    """
    Generated report instances.
    Tracks individual report executions and their results.
    """

    REPORT_STATUS = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    GENERATION_TRIGGERS = [
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
        ('api', 'API Request'),
        ('webhook', 'Webhook'),
        ('alert', 'Alert Triggered'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Report Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='reports')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='generated_reports')
    schedule = models.ForeignKey(
        ReportSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports'
    )

    # Report Details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='pending')

    # Generation Information
    trigger = models.CharField(max_length=20, choices=GENERATION_TRIGGERS, default='manual')
    output_format = models.CharField(max_length=20, choices=ReportTemplate.OUTPUT_FORMATS)

    # Report Parameters
    parameters = models.JSONField(default=dict, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    date_range_start = models.DateTimeField(null=True, blank=True)
    date_range_end = models.DateTimeField(null=True, blank=True)

    # File Information
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)  # bytes
    file_hash = models.CharField(max_length=64, blank=True)
    download_url = models.URLField(blank=True)

    # Generation Metrics
    generation_started_at = models.DateTimeField(null=True, blank=True)
    generation_completed_at = models.DateTimeField(null=True, blank=True)
    generation_duration = models.IntegerField(null=True, blank=True)  # seconds
    data_points_processed = models.BigIntegerField(null=True, blank=True)

    # Quality Metrics
    data_freshness = models.IntegerField(null=True, blank=True)  # hours
    completeness_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Access and Security
    is_confidential = models.BooleanField(default=False)
    access_restrictions = models.JSONField(default=dict, blank=True)
    encryption_enabled = models.BooleanField(default=False)
    watermark_applied = models.BooleanField(default=False)

    # Distribution
    recipients = models.JSONField(default=list, blank=True)
    distribution_completed = models.BooleanField(default=False)
    distribution_errors = models.JSONField(default=list, blank=True)

    # Retention and Cleanup
    expires_at = models.DateTimeField(null=True, blank=True)
    auto_delete = models.BooleanField(default=True)
    retention_period_days = models.IntegerField(default=90)

    # Error Information
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    retry_count = models.IntegerField(default=0)

    # Usage Tracking
    download_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    generated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports'
    )
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status', '-created_at']),
            models.Index(fields=['template', '-created_at']),
            models.Index(fields=['schedule', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['trigger', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.status}) - {self.tenant.name}"

    def is_expired(self):
        """Check if the report has expired."""
        return self.expires_at and timezone.now() > self.expires_at

    def mark_accessed(self, user=None):
        """Mark the report as accessed and increment view count."""
        self.view_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_accessed_at'])

    def calculate_generation_efficiency(self):
        """Calculate generation efficiency score."""
        if not self.generation_duration or not self.data_points_processed:
            return None

        # Points processed per second
        processing_rate = self.data_points_processed / self.generation_duration
        # Normalize to a score (this would need benchmarking data)
        return min(100, processing_rate / 1000 * 100)


class ReportExecution(models.Model):
    """
    Detailed execution tracking for report generation.
    Provides audit trail and performance monitoring for report processes.
    """

    EXECUTION_PHASES = [
        ('initialization', 'Initialization'),
        ('data_collection', 'Data Collection'),
        ('data_processing', 'Data Processing'),
        ('rendering', 'Report Rendering'),
        ('formatting', 'Output Formatting'),
        ('distribution', 'Distribution'),
        ('cleanup', 'Cleanup'),
    ]

    EXECUTION_STATUS = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Execution Information
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='execution_logs')
    execution_id = models.CharField(max_length=100, unique=True)

    # Phase Tracking
    current_phase = models.CharField(max_length=20, choices=EXECUTION_PHASES, default='initialization')
    phase_status = models.CharField(max_length=20, choices=EXECUTION_STATUS, default='running')
    phases_completed = models.JSONField(default=list, blank=True)
    phase_timings = models.JSONField(default=dict, blank=True)

    # Resource Usage
    cpu_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    memory_usage_mb = models.IntegerField(null=True, blank=True)
    disk_io_mb = models.IntegerField(null=True, blank=True)
    network_io_mb = models.IntegerField(null=True, blank=True)

    # Data Processing Metrics
    rows_processed = models.BigIntegerField(default=0)
    queries_executed = models.IntegerField(default=0)
    api_calls_made = models.IntegerField(default=0)
    cache_hits = models.IntegerField(default=0)
    cache_misses = models.IntegerField(default=0)

    # Performance Metrics
    query_execution_time = models.IntegerField(null=True, blank=True)  # milliseconds
    rendering_time = models.IntegerField(null=True, blank=True)  # milliseconds
    total_execution_time = models.IntegerField(null=True, blank=True)  # milliseconds

    # Quality Metrics
    data_quality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    missing_data_points = models.IntegerField(default=0)
    data_anomalies = models.IntegerField(default=0)

    # Error Tracking
    warnings = models.JSONField(default=list, blank=True)
    errors = models.JSONField(default=list, blank=True)
    debug_info = models.JSONField(default=dict, blank=True)

    # Environment Information
    execution_node = models.CharField(max_length=100, blank=True)
    process_id = models.IntegerField(null=True, blank=True)
    thread_id = models.CharField(max_length=50, blank=True)
    environment = models.CharField(max_length=50, default='production')

    # Execution Context
    parameters_used = models.JSONField(default=dict, blank=True)
    data_sources_accessed = models.JSONField(default=list, blank=True)
    external_dependencies = models.JSONField(default=list, blank=True)

    # Timestamp
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_heartbeat = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_report_executions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['report', '-started_at']),
            models.Index(fields=['current_phase', 'phase_status']),
            models.Index(fields=['execution_id']),
            models.Index(fields=['last_heartbeat']),
        ]

    def __str__(self):
        return f"Execution {self.execution_id} - {self.current_phase} ({self.phase_status})"

    def start_phase(self, phase):
        """Start a new execution phase."""
        if self.current_phase not in self.phases_completed:
            self.phases_completed.append(self.current_phase)

        self.current_phase = phase
        self.phase_status = 'running'
        self.phase_timings[phase] = timezone.now().isoformat()
        self.save()

    def complete_phase(self, phase=None):
        """Mark current or specified phase as completed."""
        phase = phase or self.current_phase
        if phase not in self.phases_completed:
            self.phases_completed.append(phase)

        # Record completion time
        if phase in self.phase_timings:
            start_time = timezone.datetime.fromisoformat(self.phase_timings[phase])
            duration = (timezone.now() - start_time).total_seconds()
            self.phase_timings[f"{phase}_duration"] = duration

        self.phase_status = 'completed'
        self.save()

    def fail_execution(self, error_message, error_details=None):
        """Mark execution as failed with error information."""
        self.phase_status = 'failed'
        self.completed_at = timezone.now()
        self.errors.append({
            'phase': self.current_phase,
            'message': error_message,
            'details': error_details or {},
            'timestamp': timezone.now().isoformat()
        })
        self.save()