"""
Analytics Models Tests

Test suite for analytics data models including device analytics,
content analytics, system metrics, and reporting models.
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal

from src.analytics.models import (
    Device, DeviceHealth, DeviceMetrics, DeviceEvent, DeviceAlert,
    ContentView, ContentPerformance, ContentEngagement, ViewSession,
    SystemMetrics, ResourceUsage, APIUsage, ErrorLog,
    UserActivity, UserSession, UserEngagement,
    BillingMetrics, UsageMetrics, CostAnalysis, TenantUsage,
    AlertRule, Alert, NotificationChannel, EscalationPolicy,
    Report, ReportSchedule, ReportTemplate, ReportExecution
)


class DeviceAnalyticsModelTests(TestCase):
    """Test device analytics models."""

    def setUp(self):
        """Set up test data."""
        self.tenant = self.create_test_tenant()
        self.device = Device.objects.create(
            tenant=self.tenant,
            name="Test Display",
            device_id="TEST-001",
            device_type="display",
            location="Test Location",
            ip_address="192.168.1.100",
            status="online"
        )

    def create_test_tenant(self):
        """Create a test tenant."""
        from django.contrib.auth.models import User
        # This would create a proper tenant in the real implementation
        user = User.objects.create_user(username='testuser', email='test@example.com')
        return user  # Simplified for testing

    def test_device_creation(self):
        """Test device model creation."""
        self.assertEqual(self.device.name, "Test Display")
        self.assertEqual(self.device.device_id, "TEST-001")
        self.assertEqual(self.device.status, "online")
        self.assertTrue(self.device.analytics_enabled)

    def test_device_is_online(self):
        """Test device online status check."""
        # Device without heartbeat should be offline
        self.assertFalse(self.device.is_online())

        # Device with recent heartbeat should be online
        self.device.last_heartbeat = timezone.now()
        self.device.save()
        self.assertTrue(self.device.is_online())

        # Device with old heartbeat should be offline
        self.device.last_heartbeat = timezone.now() - timedelta(minutes=10)
        self.device.save()
        self.assertFalse(self.device.is_online())

    def test_device_health_creation(self):
        """Test device health record creation."""
        health = DeviceHealth.objects.create(
            device=self.device,
            health_score=85,
            status="good",
            cpu_usage=Decimal("45.5"),
            memory_usage=Decimal("62.3"),
            temperature=Decimal("42.0")
        )

        self.assertEqual(health.device, self.device)
        self.assertEqual(health.health_score, 85)
        self.assertEqual(health.status, "good")

    def test_device_metrics_creation(self):
        """Test device metrics creation."""
        metrics = DeviceMetrics.objects.create(
            device=self.device,
            metric_type="performance",
            metric_name="cpu_usage",
            metric_value=Decimal("75.5"),
            metric_unit="percent"
        )

        self.assertEqual(metrics.device, self.device)
        self.assertEqual(metrics.metric_type, "performance")
        self.assertEqual(float(metrics.metric_value), 75.5)

    def test_device_event_creation(self):
        """Test device event creation."""
        event = DeviceEvent.objects.create(
            device=self.device,
            event_type="startup",
            severity="info",
            title="Device Started",
            description="Device started successfully"
        )

        self.assertEqual(event.device, self.device)
        self.assertEqual(event.event_type, "startup")
        self.assertEqual(event.severity, "info")

    def test_device_alert_creation_and_acknowledgment(self):
        """Test device alert creation and acknowledgment."""
        alert = DeviceAlert.objects.create(
            device=self.device,
            alert_type="health",
            priority="high",
            title="High Temperature",
            message="Device temperature exceeds threshold",
            threshold_value=Decimal("60.0"),
            current_value=Decimal("65.0")
        )

        self.assertEqual(alert.device, self.device)
        self.assertEqual(alert.state, "active")
        self.assertIsNone(alert.acknowledged_by)

        # Test acknowledgment
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='admin', email='admin@example.com')
        alert.acknowledge(user)

        self.assertEqual(alert.state, "acknowledged")
        self.assertEqual(alert.acknowledged_by, user)
        self.assertIsNotNone(alert.acknowledged_at)


class ContentAnalyticsModelTests(TestCase):
    """Test content analytics models."""

    def setUp(self):
        """Set up test data."""
        self.tenant = self.create_test_tenant()
        self.device = Device.objects.create(
            tenant=self.tenant,
            name="Test Display",
            device_id="TEST-001",
            device_type="display"
        )
        # This would be a proper Asset model in the real implementation
        self.asset = self.create_test_asset()

    def create_test_tenant(self):
        """Create a test tenant."""
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='testuser', email='test@example.com')
        return user

    def create_test_asset(self):
        """Create a test asset."""
        # This would create a proper Asset in the real implementation
        return type('Asset', (), {'id': 1, 'name': 'Test Content'})()

    def test_content_view_creation(self):
        """Test content view tracking."""
        view = ContentView.objects.create(
            asset_id=self.asset.id,
            device=self.device,
            tenant=self.tenant,
            view_type="scheduled",
            start_time=timezone.now(),
            duration_seconds=120,
            content_duration=180
        )

        self.assertEqual(view.device, self.device)
        self.assertEqual(view.view_type, "scheduled")
        self.assertEqual(view.duration_seconds, 120)

    def test_content_view_completion_rate(self):
        """Test content view completion rate calculation."""
        view = ContentView.objects.create(
            asset_id=self.asset.id,
            device=self.device,
            tenant=self.tenant,
            duration_seconds=90,
            content_duration=120
        )

        completion_rate = view.calculate_completion_rate()
        self.assertEqual(completion_rate, 75.0)

    def test_content_performance_aggregation(self):
        """Test content performance aggregation."""
        performance = ContentPerformance.objects.create(
            asset_id=self.asset.id,
            tenant=self.tenant,
            aggregation_period="daily",
            period_start=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0),
            period_end=timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999),
            total_views=100,
            completed_views=85,
            avg_completion_rate=Decimal("85.0")
        )

        self.assertEqual(performance.total_views, 100)
        self.assertEqual(performance.completed_views, 85)
        self.assertEqual(float(performance.avg_completion_rate), 85.0)

    def test_view_session_tracking(self):
        """Test view session tracking."""
        session = ViewSession.objects.create(
            session_id="session_123",
            device=self.device,
            tenant=self.tenant,
            session_type="continuous",
            start_time=timezone.now(),
            content_count=5,
            completed_content_count=4
        )

        completion_rate = session.calculate_completion_rate()
        self.assertEqual(completion_rate, 80.0)


class SystemAnalyticsModelTests(TestCase):
    """Test system analytics models."""

    def setUp(self):
        """Set up test data."""
        self.tenant = self.create_test_tenant()

    def create_test_tenant(self):
        """Create a test tenant."""
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='testuser', email='test@example.com')
        return user

    def test_system_metrics_creation(self):
        """Test system metrics creation."""
        metrics = SystemMetrics.objects.create(
            tenant=self.tenant,
            metric_name="cpu_utilization",
            metric_category="performance",
            value=Decimal("75.5"),
            unit="percent",
            threshold_warning=Decimal("80.0"),
            threshold_critical=Decimal("90.0")
        )

        self.assertEqual(metrics.metric_name, "cpu_utilization")
        self.assertFalse(metrics.is_warning())
        self.assertFalse(metrics.is_critical())

        # Test threshold checking
        metrics.value = Decimal("85.0")
        self.assertTrue(metrics.is_warning())
        self.assertFalse(metrics.is_critical())

        metrics.value = Decimal("95.0")
        self.assertTrue(metrics.is_critical())

    def test_resource_usage_tracking(self):
        """Test resource usage tracking."""
        usage = ResourceUsage.objects.create(
            tenant=self.tenant,
            resource_type="memory",
            resource_name="Application Memory",
            component="django_app",
            current_usage=Decimal("4096.0"),
            total_capacity=Decimal("8192.0"),
            utilization_percentage=Decimal("50.0")
        )

        self.assertEqual(usage.resource_type, "memory")
        self.assertEqual(float(usage.utilization_percentage), 50.0)
        self.assertFalse(usage.is_at_warning_level())

    def test_api_usage_tracking(self):
        """Test API usage tracking."""
        usage = APIUsage.objects.create(
            tenant=self.tenant,
            endpoint="/api/v1/devices",
            method="GET",
            response_status=200,
            response_category="2xx",
            response_time_ms=150
        )

        self.assertEqual(usage.endpoint, "/api/v1/devices")
        self.assertTrue(usage.is_successful())
        self.assertFalse(usage.is_slow_request(threshold_ms=1000))

    def test_error_log_creation(self):
        """Test error log creation and resolution."""
        error = ErrorLog.objects.create(
            tenant=self.tenant,
            error_level="error",
            error_category="application",
            error_message="Database connection failed",
            component="database",
            occurrence_count=1
        )

        self.assertEqual(error.error_level, "error")
        self.assertFalse(error.is_resolved)

        # Test resolution
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='admin', email='admin@example.com')
        error.resolve(user, "Fixed database configuration")

        self.assertTrue(error.is_resolved)
        self.assertEqual(error.resolved_by, user)
        self.assertIsNotNone(error.resolved_at)


class BillingAnalyticsModelTests(TestCase):
    """Test billing analytics models."""

    def setUp(self):
        """Set up test data."""
        self.tenant = self.create_test_tenant()

    def create_test_tenant(self):
        """Create a test tenant."""
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='testuser', email='test@example.com')
        return user

    def test_billing_metrics_creation(self):
        """Test billing metrics creation."""
        billing = BillingMetrics.objects.create(
            tenant=self.tenant,
            billing_period_start=timezone.now().replace(day=1),
            billing_period_end=timezone.now(),
            billing_type="subscription",
            base_cost=Decimal("100.00"),
            usage_cost=Decimal("50.00"),
            total_amount=Decimal("150.00"),
            devices_count=10,
            active_devices_count=8
        )

        self.assertEqual(float(billing.total_amount), 150.00)
        self.assertEqual(billing.devices_count, 10)

        efficiency = billing.calculate_usage_efficiency()
        self.assertEqual(efficiency, 80.0)

    def test_usage_metrics_tracking(self):
        """Test usage metrics tracking."""
        usage = UsageMetrics.objects.create(
            tenant=self.tenant,
            measurement_date=timezone.now().date(),
            usage_type="device_hours",
            usage_value=Decimal("240.0"),
            unit="hours",
            quota_limit=Decimal("300.0")
        )

        quota_usage = usage.calculate_quota_usage()
        self.assertEqual(quota_usage, 80.0)

    def test_tenant_usage_summary(self):
        """Test tenant usage summary."""
        usage = TenantUsage.objects.create(
            tenant=self.tenant,
            period_start=timezone.now().replace(day=1),
            period_end=timezone.now(),
            total_devices=15,
            active_devices=12,
            device_hours=Decimal("3600.0"),
            content_views_total=50000,
            total_charges=Decimal("500.00")
        )

        efficiency = usage.calculate_efficiency_score()
        self.assertGreater(efficiency, 0)


class AlertingModelTests(TestCase):
    """Test alerting and notification models."""

    def setUp(self):
        """Set up test data."""
        self.tenant = self.create_test_tenant()

    def create_test_tenant(self):
        """Create a test tenant."""
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='testuser', email='test@example.com')
        return user

    def test_notification_channel_creation(self):
        """Test notification channel creation."""
        channel = NotificationChannel.objects.create(
            tenant=self.tenant,
            name="Email Alerts",
            channel_type="email",
            configuration={"smtp_server": "smtp.example.com"}
        )

        self.assertEqual(channel.name, "Email Alerts")
        self.assertEqual(channel.channel_type, "email")
        self.assertTrue(channel.can_send_notification())

    def test_alert_rule_creation(self):
        """Test alert rule creation."""
        rule = AlertRule.objects.create(
            tenant=self.tenant,
            name="High CPU Usage",
            rule_type="threshold",
            severity="warning",
            metric_name="cpu_usage",
            comparison_operator="gt",
            threshold_value=Decimal("80.0")
        )

        self.assertEqual(rule.name, "High CPU Usage")
        self.assertTrue(rule.should_evaluate())

    def test_alert_lifecycle(self):
        """Test alert creation and lifecycle."""
        rule = AlertRule.objects.create(
            tenant=self.tenant,
            name="Test Rule",
            rule_type="threshold",
            metric_name="test_metric",
            threshold_value=Decimal("100.0")
        )

        alert = Alert.objects.create(
            tenant=self.tenant,
            alert_rule=rule,
            title="Test Alert",
            message="Test alert message",
            severity="warning",
            metric_value=Decimal("150.0"),
            threshold_value=Decimal("100.0")
        )

        self.assertEqual(alert.state, "active")

        # Test acknowledgment
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='admin', email='admin@example.com')
        alert.acknowledge(user)
        self.assertEqual(alert.state, "acknowledged")

        # Test resolution
        alert.resolve(user)
        self.assertEqual(alert.state, "resolved")


class ReportingModelTests(TestCase):
    """Test reporting models."""

    def setUp(self):
        """Set up test data."""
        self.tenant = self.create_test_tenant()

    def create_test_tenant(self):
        """Create a test tenant."""
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='testuser', email='test@example.com')
        return user

    def test_report_template_creation(self):
        """Test report template creation."""
        template = ReportTemplate.objects.create(
            tenant=self.tenant,
            name="Device Performance Report",
            template_type="performance",
            category="technical",
            data_sources=["device_metrics", "device_health"],
            metrics=["cpu_usage", "memory_usage", "uptime"]
        )

        self.assertEqual(template.name, "Device Performance Report")
        self.assertEqual(template.template_type, "performance")

    def test_report_schedule_creation(self):
        """Test report schedule creation."""
        template = ReportTemplate.objects.create(
            tenant=self.tenant,
            name="Test Template",
            template_type="dashboard"
        )

        schedule = ReportSchedule.objects.create(
            tenant=self.tenant,
            template=template,
            name="Daily Report",
            frequency="daily",
            start_date=timezone.now()
        )

        self.assertEqual(schedule.name, "Daily Report")
        self.assertEqual(schedule.frequency, "daily")

    def test_report_generation(self):
        """Test report generation."""
        template = ReportTemplate.objects.create(
            tenant=self.tenant,
            name="Test Template",
            template_type="dashboard"
        )

        report = Report.objects.create(
            tenant=self.tenant,
            template=template,
            name="Test Report",
            trigger="manual",
            output_format="pdf",
            status="completed",
            file_path="/reports/test_report.pdf"
        )

        self.assertEqual(report.name, "Test Report")
        self.assertEqual(report.status, "completed")
        self.assertFalse(report.is_expired())


@pytest.mark.django_db
class AnalyticsModelIntegrationTests:
    """Integration tests for analytics models."""

    def test_device_health_score_calculation(self):
        """Test device health score calculation integration."""
        # This would test the integration between Device and DeviceHealth models
        pass

    def test_content_performance_aggregation(self):
        """Test content performance aggregation from individual views."""
        pass

    def test_alert_rule_evaluation(self):
        """Test alert rule evaluation against metrics."""
        pass

    def test_billing_cost_calculation(self):
        """Test billing cost calculation from usage metrics."""
        pass