"""
Analytics Models Package

Comprehensive analytics and monitoring models for digital signage platform.
Includes device health, content performance, user engagement, and system metrics.
"""

from .device_analytics import (
    Device, DeviceHealth, DeviceMetrics, DeviceEvent, DeviceAlert
)
from .content_analytics import (
    ContentView, ContentPerformance, ContentEngagement, ViewSession
)
from .system_analytics import (
    SystemMetrics, ResourceUsage, APIUsage, ErrorLog
)
from .user_analytics import (
    UserActivity, UserSession, UserEngagement
)
from .billing_analytics import (
    BillingMetrics, UsageMetrics, CostAnalysis, TenantUsage
)
from .report_models import (
    Report, ReportSchedule, ReportExecution, ReportTemplate
)
from .alert_models import (
    AlertRule, Alert, NotificationChannel, EscalationPolicy
)

__all__ = [
    # Device Analytics
    'Device', 'DeviceHealth', 'DeviceMetrics', 'DeviceEvent', 'DeviceAlert',

    # Content Analytics
    'ContentView', 'ContentPerformance', 'ContentEngagement', 'ViewSession',

    # System Analytics
    'SystemMetrics', 'ResourceUsage', 'APIUsage', 'ErrorLog',

    # User Analytics
    'UserActivity', 'UserSession', 'UserEngagement',

    # Billing Analytics
    'BillingMetrics', 'UsageMetrics', 'CostAnalysis', 'TenantUsage',

    # Reporting
    'Report', 'ReportSchedule', 'ReportExecution', 'ReportTemplate',

    # Alerting
    'AlertRule', 'Alert', 'NotificationChannel', 'EscalationPolicy',
]