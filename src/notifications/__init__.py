"""
Notifications Package

Comprehensive notification and alerting system with multiple delivery channels.
Supports email, SMS, webhooks, and real-time notifications.
"""

from .services import (
    NotificationService, EmailNotificationService, SMSNotificationService,
    WebhookNotificationService, SlackNotificationService, PushNotificationService
)
from .managers import AlertManager, EscalationManager, NotificationManager
from .models import NotificationLog, NotificationTemplate
from .tasks import (
    send_notification_task, process_alert_task, check_escalation_task,
    cleanup_old_notifications_task
)

__all__ = [
    # Services
    'NotificationService', 'EmailNotificationService', 'SMSNotificationService',
    'WebhookNotificationService', 'SlackNotificationService', 'PushNotificationService',

    # Managers
    'AlertManager', 'EscalationManager', 'NotificationManager',

    # Models
    'NotificationLog', 'NotificationTemplate',

    # Tasks
    'send_notification_task', 'process_alert_task', 'check_escalation_task',
    'cleanup_old_notifications_task'
]