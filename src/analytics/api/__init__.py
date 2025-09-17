"""
Analytics API Package

Comprehensive API endpoints for analytics data collection, querying,
and management for the digital signage platform.
"""

from .device_analytics_api import (
    DeviceMetricsViewSet, DeviceHealthViewSet, DeviceEventViewSet,
    DeviceAlertViewSet, DeviceAnalyticsViewSet
)
from .content_analytics_api import (
    ContentViewViewSet, ContentPerformanceViewSet, ContentEngagementViewSet,
    ViewSessionViewSet, ContentAnalyticsViewSet
)
from .system_analytics_api import (
    SystemMetricsViewSet, ResourceUsageViewSet, APIUsageViewSet,
    ErrorLogViewSet, SystemAnalyticsViewSet
)
from .user_analytics_api import (
    UserActivityViewSet, UserSessionViewSet, UserEngagementViewSet,
    UserAnalyticsViewSet
)
from .billing_analytics_api import (
    BillingMetricsViewSet, UsageMetricsViewSet, CostAnalysisViewSet,
    TenantUsageViewSet, BillingAnalyticsViewSet
)
from .reporting_api import (
    ReportTemplateViewSet, ReportScheduleViewSet, ReportViewSet,
    ReportExecutionViewSet, ReportingViewSet
)
from .alert_api import (
    AlertRuleViewSet, AlertViewSet, NotificationChannelViewSet,
    EscalationPolicyViewSet, AlertingViewSet
)
from .dashboard_api import (
    DashboardViewSet, DashboardWidgetViewSet, DashboardAnalyticsViewSet
)

__all__ = [
    # Device Analytics
    'DeviceMetricsViewSet', 'DeviceHealthViewSet', 'DeviceEventViewSet',
    'DeviceAlertViewSet', 'DeviceAnalyticsViewSet',

    # Content Analytics
    'ContentViewViewSet', 'ContentPerformanceViewSet', 'ContentEngagementViewSet',
    'ViewSessionViewSet', 'ContentAnalyticsViewSet',

    # System Analytics
    'SystemMetricsViewSet', 'ResourceUsageViewSet', 'APIUsageViewSet',
    'ErrorLogViewSet', 'SystemAnalyticsViewSet',

    # User Analytics
    'UserActivityViewSet', 'UserSessionViewSet', 'UserEngagementViewSet',
    'UserAnalyticsViewSet',

    # Billing Analytics
    'BillingMetricsViewSet', 'UsageMetricsViewSet', 'CostAnalysisViewSet',
    'TenantUsageViewSet', 'BillingAnalyticsViewSet',

    # Reporting
    'ReportTemplateViewSet', 'ReportScheduleViewSet', 'ReportViewSet',
    'ReportExecutionViewSet', 'ReportingViewSet',

    # Alerting
    'AlertRuleViewSet', 'AlertViewSet', 'NotificationChannelViewSet',
    'EscalationPolicyViewSet', 'AlertingViewSet',

    # Dashboard
    'DashboardViewSet', 'DashboardWidgetViewSet', 'DashboardAnalyticsViewSet',
]