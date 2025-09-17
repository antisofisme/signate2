"""
User Analytics Models

Models for tracking user behavior, engagement patterns, and activity metrics
across the digital signage platform management interface.
"""

import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class UserActivity(models.Model):
    """
    User activity tracking for platform usage analytics.
    Records user actions, feature usage, and interaction patterns.
    """

    ACTIVITY_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('content_upload', 'Content Upload'),
        ('content_edit', 'Content Edit'),
        ('content_delete', 'Content Delete'),
        ('playlist_create', 'Playlist Create'),
        ('playlist_edit', 'Playlist Edit'),
        ('device_configure', 'Device Configuration'),
        ('device_control', 'Device Control'),
        ('report_generate', 'Report Generation'),
        ('dashboard_view', 'Dashboard View'),
        ('settings_change', 'Settings Change'),
        ('user_management', 'User Management'),
        ('billing_action', 'Billing Action'),
        ('api_usage', 'API Usage'),
        ('search', 'Search Action'),
        ('export', 'Data Export'),
        ('import', 'Data Import'),
    ]

    ACTIVITY_OUTCOMES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('partial', 'Partial Success'),
        ('cancelled', 'Cancelled'),
        ('timeout', 'Timeout'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User and Tenant Information
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='activity_logs')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='user_activities')

    # Activity Information
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    activity_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    outcome = models.CharField(max_length=20, choices=ACTIVITY_OUTCOMES, default='success')

    # Target Information (what was acted upon)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey('target_content_type', 'target_object_id')
    target_name = models.CharField(max_length=255, blank=True)

    # Performance Metrics
    duration_ms = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    data_processed_bytes = models.BigIntegerField(null=True, blank=True)

    # Context Information
    feature = models.CharField(max_length=100, blank=True)
    page_url = models.URLField(blank=True)
    referrer_url = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)

    # Session Information
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    geolocation = models.JSONField(default=dict, blank=True)

    # Error Information (if outcome was failure)
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=100, blank=True)

    # Additional Data
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_user_activity'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['tenant', '-timestamp']),
            models.Index(fields=['activity_type', '-timestamp']),
            models.Index(fields=['outcome', '-timestamp']),
            models.Index(fields=['feature', '-timestamp']),
            models.Index(fields=['session_id', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.activity_name} ({self.outcome})"


class UserSession(models.Model):
    """
    User session tracking and analytics.
    Monitors user engagement patterns, session duration, and feature usage.
    """

    SESSION_TYPES = [
        ('web', 'Web Session'),
        ('api', 'API Session'),
        ('mobile', 'Mobile App'),
        ('desktop', 'Desktop App'),
    ]

    SESSION_STATUS = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('timeout', 'Timeout'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Session Identification
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='user_sessions')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='user_sessions')

    # Session Information
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='web')
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='active')

    # Timing Information
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(default=timezone.now)
    duration_seconds = models.IntegerField(null=True, blank=True)

    # Activity Metrics
    page_views = models.IntegerField(default=0)
    actions_performed = models.IntegerField(default=0)
    api_calls_made = models.IntegerField(default=0)
    features_used = models.JSONField(default=list, blank=True)

    # Engagement Metrics
    engagement_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    conversion_events = models.IntegerField(default=0)

    # Device and Environment
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    screen_resolution = models.CharField(max_length=20, blank=True)

    # Network Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    geolocation = models.JSONField(default=dict, blank=True)

    # Performance Metrics
    load_times = models.JSONField(default=list, blank=True)
    error_count = models.IntegerField(default=0)
    warnings_count = models.IntegerField(default=0)

    # Content Interaction
    content_created = models.IntegerField(default=0)
    content_modified = models.IntegerField(default=0)
    content_deleted = models.IntegerField(default=0)
    content_viewed = models.IntegerField(default=0)

    # Device Management
    devices_managed = models.IntegerField(default=0)
    devices_configured = models.IntegerField(default=0)
    devices_monitored = models.IntegerField(default=0)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_user_sessions'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', '-start_time']),
            models.Index(fields=['tenant', '-start_time']),
            models.Index(fields=['session_id']),
            models.Index(fields=['status', '-start_time']),
            models.Index(fields=['session_type', '-start_time']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.session_type} session ({self.status})"

    def calculate_duration(self):
        """Calculate session duration in seconds."""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return int((timezone.now() - self.start_time).total_seconds())

    def is_active_session(self, timeout_minutes=30):
        """Check if session is still active based on last activity."""
        if self.status != 'active':
            return False

        timeout_threshold = timezone.now() - timezone.timedelta(minutes=timeout_minutes)
        return self.last_activity > timeout_threshold

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])

    def terminate_session(self):
        """Terminate the session."""
        self.status = 'terminated'
        self.end_time = timezone.now()
        self.duration_seconds = self.calculate_duration()
        self.save()


class UserEngagement(models.Model):
    """
    User engagement metrics and behavioral analytics.
    Tracks user interaction patterns, feature adoption, and platform usage trends.
    """

    ENGAGEMENT_TYPES = [
        ('feature_usage', 'Feature Usage'),
        ('content_interaction', 'Content Interaction'),
        ('device_management', 'Device Management'),
        ('collaboration', 'Collaboration'),
        ('learning', 'Learning/Help'),
        ('customization', 'Customization'),
    ]

    ENGAGEMENT_LEVELS = [
        ('low', 'Low Engagement'),
        ('medium', 'Medium Engagement'),
        ('high', 'High Engagement'),
        ('power_user', 'Power User'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User Information
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='engagement_metrics')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='user_engagement')

    # Engagement Information
    engagement_type = models.CharField(max_length=20, choices=ENGAGEMENT_TYPES)
    engagement_level = models.CharField(max_length=20, choices=ENGAGEMENT_LEVELS, default='medium')

    # Time Period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        default='weekly'
    )

    # Activity Metrics
    sessions_count = models.IntegerField(default=0)
    total_time_seconds = models.BigIntegerField(default=0)
    average_session_duration = models.IntegerField(default=0)
    actions_count = models.IntegerField(default=0)

    # Feature Usage
    features_used = models.JSONField(default=list, blank=True)
    feature_adoption_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    new_features_tried = models.IntegerField(default=0)
    advanced_features_used = models.IntegerField(default=0)

    # Content Metrics
    content_created_count = models.IntegerField(default=0)
    content_modified_count = models.IntegerField(default=0)
    content_shared_count = models.IntegerField(default=0)
    content_consumption_time = models.BigIntegerField(default=0)

    # Device Management Metrics
    devices_managed_count = models.IntegerField(default=0)
    devices_configured_count = models.IntegerField(default=0)
    monitoring_time_seconds = models.BigIntegerField(default=0)
    alerts_handled_count = models.IntegerField(default=0)

    # Collaboration Metrics
    teams_participated = models.IntegerField(default=0)
    messages_sent = models.IntegerField(default=0)
    files_shared = models.IntegerField(default=0)
    comments_made = models.IntegerField(default=0)

    # Learning and Support
    help_articles_viewed = models.IntegerField(default=0)
    tutorials_completed = models.IntegerField(default=0)
    support_tickets_created = models.IntegerField(default=0)
    feedback_provided = models.IntegerField(default=0)

    # Engagement Scores
    overall_engagement_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    feature_engagement_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    content_engagement_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    collaboration_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Behavioral Patterns
    preferred_time_of_day = models.CharField(max_length=50, blank=True)
    preferred_day_of_week = models.CharField(max_length=20, blank=True)
    usage_patterns = models.JSONField(default=dict, blank=True)
    workflow_efficiency = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Retention Metrics
    days_active = models.IntegerField(default=0)
    consecutive_active_days = models.IntegerField(default=0)
    churn_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Satisfaction Indicators
    error_encounters = models.IntegerField(default=0)
    feature_requests = models.IntegerField(default=0)
    satisfaction_indicators = models.JSONField(default=dict, blank=True)

    # Metadata
    calculation_metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_user_engagement'
        ordering = ['-period_end']
        unique_together = [['user', 'engagement_type', 'period_start', 'period_end']]
        indexes = [
            models.Index(fields=['user', '-period_end']),
            models.Index(fields=['tenant', '-period_end']),
            models.Index(fields=['engagement_level', '-period_end']),
            models.Index(fields=['engagement_type', '-period_end']),
            models.Index(fields=['overall_engagement_score', '-period_end']),
            models.Index(fields=['churn_risk_score', '-period_end']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.engagement_type} ({self.engagement_level})"

    def calculate_engagement_level(self):
        """Calculate and update engagement level based on score."""
        score = self.overall_engagement_score
        if score >= 80:
            return 'power_user'
        elif score >= 60:
            return 'high'
        elif score >= 30:
            return 'medium'
        else:
            return 'low'

    def get_activity_summary(self):
        """Get a summary of user activity for this period."""
        return {
            'sessions': self.sessions_count,
            'total_time_hours': round(self.total_time_seconds / 3600, 2),
            'avg_session_minutes': round(self.average_session_duration / 60, 2),
            'actions_per_session': round(self.actions_count / max(self.sessions_count, 1), 2),
            'features_adoption_rate': float(self.feature_adoption_rate),
            'engagement_level': self.engagement_level,
        }