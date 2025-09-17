"""
Content Analytics Models

Models for tracking content performance, engagement metrics, and viewing patterns.
Provides comprehensive insights into content effectiveness and user interaction.
"""

import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class ContentView(models.Model):
    """
    Individual content view tracking.
    Records each time content is displayed on a device with detailed context.
    """

    VIEW_TYPES = [
        ('scheduled', 'Scheduled Playback'),
        ('manual', 'Manual Selection'),
        ('interactive', 'Interactive Trigger'),
        ('emergency', 'Emergency Override'),
        ('test', 'Test Playback'),
    ]

    COMPLETION_STATUS = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('interrupted', 'Interrupted'),
        ('skipped', 'Skipped'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Content Reference
    asset = models.ForeignKey('anthias_app.Asset', on_delete=models.CASCADE, related_name='view_analytics')
    device = models.ForeignKey('analytics.Device', on_delete=models.CASCADE, related_name='content_views')

    # Tenant for multi-tenant isolation
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='content_views')

    # View Information
    view_type = models.CharField(max_length=20, choices=VIEW_TYPES, default='scheduled')
    completion_status = models.CharField(max_length=20, choices=COMPLETION_STATUS, default='started')

    # Timing Information
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    content_duration = models.IntegerField(null=True, blank=True)  # Expected duration

    # Engagement Metrics
    interaction_count = models.IntegerField(default=0)
    attention_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Quality Metrics
    load_time_ms = models.IntegerField(null=True, blank=True)
    error_count = models.IntegerField(default=0)
    quality_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Context Information
    playlist_position = models.IntegerField(null=True, blank=True)
    playlist_id = models.CharField(max_length=100, blank=True)
    trigger_source = models.CharField(max_length=100, blank=True)

    # Environmental Context
    viewer_count = models.IntegerField(null=True, blank=True)
    ambient_light = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    audio_level = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Additional Metadata
    metadata = models.JSONField(default=dict, blank=True)
    user_agent = models.TextField(blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_content_views'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['asset', '-start_time']),
            models.Index(fields=['device', '-start_time']),
            models.Index(fields=['tenant', '-start_time']),
            models.Index(fields=['completion_status', '-start_time']),
            models.Index(fields=['view_type', '-start_time']),
            models.Index(fields=['start_time', 'end_time']),
        ]

    def __str__(self):
        return f"{self.asset.name} on {self.device.name} at {self.start_time}"

    def calculate_completion_rate(self):
        """Calculate the completion rate as a percentage."""
        if not self.duration_seconds or not self.content_duration:
            return None
        return min(100, (self.duration_seconds / self.content_duration) * 100)

    def is_successful_view(self):
        """Determine if this was a successful content view."""
        return (
            self.completion_status == 'completed' and
            self.error_count == 0 and
            (self.quality_score is None or self.quality_score >= 70)
        )


class ContentPerformance(models.Model):
    """
    Aggregated content performance metrics.
    Pre-calculated statistics for efficient dashboard queries.
    """

    AGGREGATION_PERIODS = [
        ('hour', 'Hourly'),
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Content Reference
    asset = models.ForeignKey('anthias_app.Asset', on_delete=models.CASCADE, related_name='performance_analytics')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='content_performance')

    # Aggregation Information
    aggregation_period = models.CharField(max_length=20, choices=AGGREGATION_PERIODS)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    # View Statistics
    total_views = models.IntegerField(default=0)
    completed_views = models.IntegerField(default=0)
    interrupted_views = models.IntegerField(default=0)
    error_views = models.IntegerField(default=0)

    # Performance Metrics
    avg_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_load_time_ms = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    avg_quality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Engagement Metrics
    total_interactions = models.IntegerField(default=0)
    avg_attention_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    unique_devices = models.IntegerField(default=0)

    # Duration Metrics
    total_duration_seconds = models.BigIntegerField(default=0)
    avg_duration_seconds = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Success Metrics
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    error_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Comparative Metrics
    performance_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    ranking = models.IntegerField(null=True, blank=True)

    # Metadata
    calculation_metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_content_performance'
        ordering = ['-period_start']
        unique_together = [['asset', 'aggregation_period', 'period_start']]
        indexes = [
            models.Index(fields=['asset', 'aggregation_period', '-period_start']),
            models.Index(fields=['tenant', 'aggregation_period', '-period_start']),
            models.Index(fields=['performance_score', '-period_start']),
            models.Index(fields=['success_rate', '-period_start']),
        ]

    def __str__(self):
        return f"{self.asset.name} - {self.aggregation_period} ({self.period_start.date()})"


class ContentEngagement(models.Model):
    """
    Content engagement tracking for interactive content.
    Records user interactions and engagement patterns.
    """

    INTERACTION_TYPES = [
        ('touch', 'Touch Interaction'),
        ('click', 'Click'),
        ('hover', 'Hover'),
        ('gesture', 'Gesture'),
        ('voice', 'Voice Command'),
        ('proximity', 'Proximity Sensor'),
        ('dwell', 'Dwell Time'),
        ('navigation', 'Navigation'),
    ]

    ENGAGEMENT_OUTCOMES = [
        ('conversion', 'Conversion'),
        ('bounce', 'Bounce'),
        ('engagement', 'Engagement'),
        ('completion', 'Completion'),
        ('abandonment', 'Abandonment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Content and Device Reference
    content_view = models.ForeignKey(ContentView, on_delete=models.CASCADE, related_name='engagements')
    asset = models.ForeignKey('anthias_app.Asset', on_delete=models.CASCADE, related_name='engagement_analytics')
    device = models.ForeignKey('analytics.Device', on_delete=models.CASCADE, related_name='content_engagements')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='content_engagements')

    # Interaction Information
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    interaction_element = models.CharField(max_length=255, blank=True)
    interaction_data = models.JSONField(default=dict, blank=True)

    # Timing
    interaction_time = models.DateTimeField(default=timezone.now)
    duration_ms = models.IntegerField(null=True, blank=True)
    sequence_number = models.IntegerField(default=1)

    # Position and Context
    screen_x = models.IntegerField(null=True, blank=True)
    screen_y = models.IntegerField(null=True, blank=True)
    element_id = models.CharField(max_length=100, blank=True)
    page_section = models.CharField(max_length=100, blank=True)

    # Engagement Metrics
    engagement_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    outcome = models.CharField(max_length=20, choices=ENGAGEMENT_OUTCOMES, blank=True)

    # User Context
    session_id = models.CharField(max_length=100, blank=True)
    user_segment = models.CharField(max_length=100, blank=True)
    user_demographics = models.JSONField(default=dict, blank=True)

    # Environmental Context
    crowd_density = models.CharField(max_length=20, blank=True)
    time_of_day = models.CharField(max_length=20, blank=True)
    day_of_week = models.CharField(max_length=20, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_content_engagement'
        ordering = ['-interaction_time']
        indexes = [
            models.Index(fields=['content_view', 'interaction_time']),
            models.Index(fields=['asset', '-interaction_time']),
            models.Index(fields=['device', '-interaction_time']),
            models.Index(fields=['tenant', '-interaction_time']),
            models.Index(fields=['interaction_type', '-interaction_time']),
            models.Index(fields=['outcome', '-interaction_time']),
        ]

    def __str__(self):
        return f"{self.interaction_type} on {self.asset.name} at {self.interaction_time}"


class ViewSession(models.Model):
    """
    Viewing session tracking for grouped content views.
    Represents a continuous viewing session across multiple content pieces.
    """

    SESSION_TYPES = [
        ('continuous', 'Continuous Viewing'),
        ('playlist', 'Playlist Session'),
        ('interactive', 'Interactive Session'),
        ('event', 'Event-based Session'),
    ]

    SESSION_STATUS = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('interrupted', 'Interrupted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Session Identification
    session_id = models.CharField(max_length=100, unique=True)
    device = models.ForeignKey('analytics.Device', on_delete=models.CASCADE, related_name='view_sessions')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='view_sessions')

    # Session Information
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='continuous')
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='active')

    # Timing
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    # Content Statistics
    content_count = models.IntegerField(default=0)
    completed_content_count = models.IntegerField(default=0)
    total_interactions = models.IntegerField(default=0)

    # Engagement Metrics
    average_attention_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Quality Metrics
    average_load_time_ms = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    error_count = models.IntegerField(default=0)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Session Context
    playlist_id = models.CharField(max_length=100, blank=True)
    event_id = models.CharField(max_length=100, blank=True)
    trigger_source = models.CharField(max_length=100, blank=True)

    # User Context
    estimated_viewers = models.IntegerField(null=True, blank=True)
    audience_type = models.CharField(max_length=100, blank=True)
    demographics = models.JSONField(default=dict, blank=True)

    # Environmental Context
    location_context = models.JSONField(default=dict, blank=True)
    weather_conditions = models.JSONField(default=dict, blank=True)
    special_events = models.JSONField(default=list, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_view_sessions'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['device', '-start_time']),
            models.Index(fields=['tenant', '-start_time']),
            models.Index(fields=['status', '-start_time']),
            models.Index(fields=['session_type', '-start_time']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"Session {self.session_id} on {self.device.name}"

    def calculate_completion_rate(self):
        """Calculate session completion rate."""
        if self.content_count == 0:
            return 0
        return (self.completed_content_count / self.content_count) * 100

    def get_session_views(self):
        """Get all content views in this session."""
        return ContentView.objects.filter(
            device=self.device,
            start_time__gte=self.start_time,
            start_time__lte=self.end_time if self.end_time else timezone.now()
        )