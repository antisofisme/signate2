"""
Billing Analytics Models

Models for tracking billing metrics, usage-based pricing, cost analysis,
and revenue analytics for the multi-tenant digital signage platform.
"""

import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class BillingMetrics(models.Model):
    """
    Comprehensive billing metrics for tenant cost tracking and revenue analysis.
    Tracks usage-based billing, subscription metrics, and revenue optimization.
    """

    BILLING_TYPES = [
        ('subscription', 'Subscription Fee'),
        ('usage', 'Usage-based Billing'),
        ('overage', 'Overage Charges'),
        ('addon', 'Add-on Services'),
        ('support', 'Support Services'),
        ('storage', 'Storage Costs'),
        ('bandwidth', 'Bandwidth Costs'),
        ('api', 'API Usage Costs'),
    ]

    BILLING_STATUS = [
        ('pending', 'Pending'),
        ('billed', 'Billed'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('disputed', 'Disputed'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tenant Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='billing_metrics')

    # Billing Period
    billing_period_start = models.DateTimeField()
    billing_period_end = models.DateTimeField()
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
            ('usage', 'Usage-based'),
        ],
        default='monthly'
    )

    # Billing Information
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPES)
    status = models.CharField(max_length=20, choices=BILLING_STATUS, default='pending')

    # Cost Breakdown
    base_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    usage_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overage_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    addon_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Usage Metrics
    devices_count = models.IntegerField(default=0)
    active_devices_count = models.IntegerField(default=0)
    content_storage_gb = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    bandwidth_usage_gb = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    api_calls_count = models.BigIntegerField(default=0)
    user_accounts_count = models.IntegerField(default=0)

    # Performance Metrics
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    support_tickets_count = models.IntegerField(default=0)
    feature_usage_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Revenue Metrics
    mrr = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Monthly Recurring Revenue
    arr = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Annual Recurring Revenue
    ltv = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Lifetime Value

    # Payment Information
    invoice_id = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)

    # Metadata
    pricing_plan = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, default=1)
    billing_metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_billing_metrics'
        ordering = ['-billing_period_start']
        indexes = [
            models.Index(fields=['tenant', '-billing_period_start']),
            models.Index(fields=['billing_type', '-billing_period_start']),
            models.Index(fields=['status', '-billing_period_start']),
            models.Index(fields=['billing_cycle', '-billing_period_start']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.billing_type} ({self.billing_period_start.strftime('%Y-%m')})"

    def calculate_usage_efficiency(self):
        """Calculate usage efficiency score based on resource utilization."""
        if self.devices_count == 0:
            return 0

        active_ratio = self.active_devices_count / self.devices_count
        # Add more efficiency calculations based on usage patterns
        return min(100, active_ratio * 100)


class UsageMetrics(models.Model):
    """
    Detailed usage metrics for billing calculation and optimization.
    Tracks resource consumption patterns and usage trends.
    """

    USAGE_TYPES = [
        ('device_hours', 'Device Active Hours'),
        ('storage', 'Storage Usage'),
        ('bandwidth', 'Bandwidth Usage'),
        ('api_calls', 'API Calls'),
        ('transcoding', 'Content Transcoding'),
        ('users', 'User Accounts'),
        ('reports', 'Report Generation'),
        ('alerts', 'Alert Notifications'),
    ]

    MEASUREMENT_UNITS = [
        ('hours', 'Hours'),
        ('gb', 'Gigabytes'),
        ('mb', 'Megabytes'),
        ('calls', 'API Calls'),
        ('count', 'Count'),
        ('minutes', 'Minutes'),
        ('events', 'Events'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tenant and Period
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='usage_metrics')
    measurement_date = models.DateField()
    aggregation_period = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )

    # Usage Information
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPES)
    usage_value = models.DecimalField(max_digits=20, decimal_places=6)
    unit = models.CharField(max_length=20, choices=MEASUREMENT_UNITS)

    # Limits and Quotas
    quota_limit = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    quota_used_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_overage = models.BooleanField(default=False)
    overage_amount = models.DecimalField(max_digits=20, decimal_places=6, default=0)

    # Cost Information
    unit_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overage_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Quality Metrics
    efficiency_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    waste_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    optimization_potential = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Trends
    usage_trend = models.CharField(
        max_length=20,
        choices=[
            ('increasing', 'Increasing'),
            ('decreasing', 'Decreasing'),
            ('stable', 'Stable'),
            ('volatile', 'Volatile'),
        ],
        blank=True
    )
    growth_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Metadata
    source_data = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    recorded_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_usage_metrics'
        ordering = ['-measurement_date']
        unique_together = [['tenant', 'usage_type', 'measurement_date', 'aggregation_period']]
        indexes = [
            models.Index(fields=['tenant', 'usage_type', '-measurement_date']),
            models.Index(fields=['usage_type', '-measurement_date']),
            models.Index(fields=['is_overage', '-measurement_date']),
            models.Index(fields=['quota_used_percentage', '-measurement_date']),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.usage_type}: {self.usage_value} {self.unit}"

    def calculate_quota_usage(self):
        """Calculate quota usage percentage."""
        if self.quota_limit and self.quota_limit > 0:
            return min(100, (self.usage_value / self.quota_limit) * 100)
        return None


class CostAnalysis(models.Model):
    """
    Cost analysis and optimization recommendations.
    Provides insights for cost reduction and usage optimization.
    """

    ANALYSIS_TYPES = [
        ('cost_breakdown', 'Cost Breakdown Analysis'),
        ('usage_optimization', 'Usage Optimization'),
        ('trend_analysis', 'Trend Analysis'),
        ('comparative', 'Comparative Analysis'),
        ('forecast', 'Cost Forecast'),
        ('roi', 'ROI Analysis'),
    ]

    RECOMMENDATION_PRIORITY = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Analysis Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='cost_analyses')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)
    analysis_period_start = models.DateTimeField()
    analysis_period_end = models.DateTimeField()

    # Cost Data
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)
    cost_breakdown = models.JSONField(default=dict, blank=True)
    cost_per_device = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_per_user = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Optimization Insights
    potential_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    optimization_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    efficiency_rating = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('average', 'Average'),
            ('poor', 'Poor'),
        ],
        blank=True
    )

    # Recommendations
    recommendations = models.JSONField(default=list, blank=True)
    top_recommendation = models.TextField(blank=True)
    recommendation_priority = models.CharField(max_length=20, choices=RECOMMENDATION_PRIORITY, default='medium')

    # Trends and Forecasts
    cost_trend = models.CharField(
        max_length=20,
        choices=[
            ('increasing', 'Increasing'),
            ('decreasing', 'Decreasing'),
            ('stable', 'Stable'),
        ],
        blank=True
    )
    projected_monthly_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    projected_annual_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Benchmarking
    industry_percentile = models.IntegerField(null=True, blank=True)
    peer_comparison = models.JSONField(default=dict, blank=True)
    cost_efficiency_rank = models.IntegerField(null=True, blank=True)

    # Action Items
    action_items = models.JSONField(default=list, blank=True)
    estimated_implementation_effort = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low Effort'),
            ('medium', 'Medium Effort'),
            ('high', 'High Effort'),
        ],
        blank=True
    )

    # Metadata
    analysis_metadata = models.JSONField(default=dict, blank=True)
    data_sources = models.JSONField(default=list, blank=True)

    # Timestamp
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_cost_analysis'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['tenant', '-generated_at']),
            models.Index(fields=['analysis_type', '-generated_at']),
            models.Index(fields=['optimization_score', '-generated_at']),
            models.Index(fields=['recommendation_priority', '-generated_at']),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.analysis_type} Analysis"

    def get_top_cost_categories(self, limit=5):
        """Get the top cost categories from the breakdown."""
        if not self.cost_breakdown:
            return []

        sorted_costs = sorted(
            self.cost_breakdown.items(),
            key=lambda x: float(x[1]),
            reverse=True
        )
        return sorted_costs[:limit]


class TenantUsage(models.Model):
    """
    Comprehensive tenant usage summary for billing and analytics.
    Aggregated usage data across all tenant resources and services.
    """

    TENANT_TIERS = [
        ('free', 'Free Tier'),
        ('basic', 'Basic Plan'),
        ('professional', 'Professional Plan'),
        ('enterprise', 'Enterprise Plan'),
        ('custom', 'Custom Plan'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tenant Information
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='usage_summaries')
    tier = models.CharField(max_length=20, choices=TENANT_TIERS, default='basic')

    # Reporting Period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        default='monthly'
    )

    # Device Usage
    total_devices = models.IntegerField(default=0)
    active_devices = models.IntegerField(default=0)
    device_hours = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    device_utilization_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Content Usage
    content_items_total = models.IntegerField(default=0)
    content_storage_gb = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    content_bandwidth_gb = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    content_views_total = models.BigIntegerField(default=0)

    # User Activity
    active_users = models.IntegerField(default=0)
    total_user_sessions = models.IntegerField(default=0)
    total_user_hours = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    api_calls_total = models.BigIntegerField(default=0)

    # Feature Usage
    features_used = models.JSONField(default=list, blank=True)
    advanced_features_used = models.IntegerField(default=0)
    integrations_active = models.IntegerField(default=0)

    # Support and Services
    support_tickets = models.IntegerField(default=0)
    alerts_generated = models.IntegerField(default=0)
    reports_generated = models.IntegerField(default=0)

    # Performance Metrics
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    average_response_time = models.IntegerField(null=True, blank=True)  # milliseconds
    error_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Billing Summary
    total_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overage_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credits_applied = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Quota Status
    quota_status = models.JSONField(default=dict, blank=True)
    quota_warnings = models.IntegerField(default=0)
    quota_violations = models.IntegerField(default=0)

    # Growth Metrics
    growth_metrics = models.JSONField(default=dict, blank=True)
    month_over_month_growth = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Health Score
    tenant_health_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100
    )

    # Metadata
    summary_metadata = models.JSONField(default=dict, blank=True)

    # Timestamp
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_tenant_usage'
        ordering = ['-period_end']
        unique_together = [['tenant', 'period_start', 'period_end']]
        indexes = [
            models.Index(fields=['tenant', '-period_end']),
            models.Index(fields=['tier', '-period_end']),
            models.Index(fields=['period_type', '-period_end']),
            models.Index(fields=['tenant_health_score', '-period_end']),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.period_type} usage ({self.period_start.strftime('%Y-%m')})"

    def calculate_efficiency_score(self):
        """Calculate overall efficiency score based on utilization metrics."""
        scores = []

        # Device utilization
        if self.total_devices > 0:
            device_score = min(100, self.device_utilization_rate)
            scores.append(device_score)

        # User engagement
        if self.active_users > 0 and self.total_user_sessions > 0:
            avg_sessions_per_user = self.total_user_sessions / self.active_users
            user_score = min(100, avg_sessions_per_user * 10)  # Arbitrary scaling
            scores.append(user_score)

        # Feature adoption
        total_features = 50  # Assume total available features
        feature_score = min(100, (len(self.features_used) / total_features) * 100)
        scores.append(feature_score)

        return sum(scores) / len(scores) if scores else 0