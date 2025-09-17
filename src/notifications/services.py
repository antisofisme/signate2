"""
Notification Services

Implementation of various notification delivery services including
email, SMS, webhooks, Slack, and push notifications.
"""

import logging
import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
import boto3
from twilio.rest import Client as TwilioClient

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of a notification attempt."""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    delivery_time_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationService(ABC):
    """
    Abstract base class for notification services.
    """

    def __init__(self, channel_config: Dict[str, Any]):
        self.config = channel_config
        self.enabled = channel_config.get('enabled', True)

    @abstractmethod
    async def send_notification(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        """Send notification to recipients."""
        pass

    def is_available(self) -> bool:
        """Check if the notification service is available."""
        return self.enabled

    def validate_recipients(self, recipients: List[str]) -> List[str]:
        """Validate and filter recipient list."""
        return [r for r in recipients if r and r.strip()]


class EmailNotificationService(NotificationService):
    """
    Email notification service with template support.
    """

    def __init__(self, channel_config: Dict[str, Any]):
        super().__init__(channel_config)
        self.smtp_settings = channel_config.get('smtp', {})
        self.template_base = channel_config.get('template_base', 'notifications/email')

    async def send_notification(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        """Send email notification."""
        start_time = timezone.now()

        try:
            valid_recipients = self.validate_recipients(recipients)
            if not valid_recipients:
                return NotificationResult(
                    success=False,
                    error_message="No valid email recipients"
                )

            # Prepare email content
            context = context or {}
            context.update({
                'subject': subject,
                'message': message,
                'timestamp': timezone.now(),
            })

            # Render HTML template if available
            html_content = None
            try:
                html_content = render_to_string(
                    f'{self.template_base}/alert.html',
                    context
                )
            except:
                logger.warning("HTML email template not found, using plain text")

            # Send email
            if html_content:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=valid_recipients
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=valid_recipients,
                    fail_silently=False
                )

            delivery_time = int((timezone.now() - start_time).total_seconds() * 1000)

            return NotificationResult(
                success=True,
                message_id=f"email_{timezone.now().timestamp()}",
                delivery_time_ms=delivery_time,
                metadata={
                    'recipients_count': len(valid_recipients),
                    'has_html': html_content is not None
                }
            )

        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return NotificationResult(
                success=False,
                error_message=str(e)
            )


class SMSNotificationService(NotificationService):
    """
    SMS notification service using Twilio.
    """

    def __init__(self, channel_config: Dict[str, Any]):
        super().__init__(channel_config)
        self.account_sid = channel_config.get('account_sid')
        self.auth_token = channel_config.get('auth_token')
        self.from_number = channel_config.get('from_number')

        if self.enabled and self.account_sid and self.auth_token:
            self.client = TwilioClient(self.account_sid, self.auth_token)
        else:
            self.client = None
            self.enabled = False

    async def send_notification(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        """Send SMS notification."""
        start_time = timezone.now()

        try:
            if not self.client:
                return NotificationResult(
                    success=False,
                    error_message="SMS service not configured"
                )

            valid_recipients = self.validate_recipients(recipients)
            if not valid_recipients:
                return NotificationResult(
                    success=False,
                    error_message="No valid phone numbers"
                )

            # Prepare SMS content (combine subject and message)
            sms_content = f"{subject}\n\n{message}"
            if len(sms_content) > 1600:  # SMS limit
                sms_content = sms_content[:1590] + "... (truncated)"

            # Send SMS to each recipient
            successful_sends = 0
            errors = []

            for phone_number in valid_recipients:
                try:
                    message_obj = self.client.messages.create(
                        body=sms_content,
                        from_=self.from_number,
                        to=phone_number
                    )
                    successful_sends += 1
                    logger.info(f"SMS sent to {phone_number}: {message_obj.sid}")

                except Exception as e:
                    errors.append(f"{phone_number}: {str(e)}")
                    logger.error(f"Failed to send SMS to {phone_number}: {e}")

            delivery_time = int((timezone.now() - start_time).total_seconds() * 1000)

            if successful_sends > 0:
                return NotificationResult(
                    success=True,
                    message_id=f"sms_{timezone.now().timestamp()}",
                    delivery_time_ms=delivery_time,
                    metadata={
                        'successful_sends': successful_sends,
                        'total_recipients': len(valid_recipients),
                        'errors': errors
                    }
                )
            else:
                return NotificationResult(
                    success=False,
                    error_message=f"All SMS sends failed: {errors}"
                )

        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
            return NotificationResult(
                success=False,
                error_message=str(e)
            )


class WebhookNotificationService(NotificationService):
    """
    Webhook notification service for custom integrations.
    """

    def __init__(self, channel_config: Dict[str, Any]):
        super().__init__(channel_config)
        self.webhook_url = channel_config.get('webhook_url')
        self.headers = channel_config.get('headers', {})
        self.timeout = channel_config.get('timeout', 30)
        self.retry_count = channel_config.get('retry_count', 3)

    async def send_notification(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        """Send webhook notification."""
        start_time = timezone.now()

        try:
            if not self.webhook_url:
                return NotificationResult(
                    success=False,
                    error_message="Webhook URL not configured"
                )

            # Prepare webhook payload
            payload = {
                'type': 'alert_notification',
                'subject': subject,
                'message': message,
                'recipients': recipients,
                'timestamp': timezone.now().isoformat(),
                'context': context or {}
            }

            # Set default headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'SignageAnalytics/1.0',
                **self.headers
            }

            # Attempt to send webhook with retries
            last_error = None
            for attempt in range(self.retry_count):
                try:
                    response = requests.post(
                        self.webhook_url,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout
                    )

                    if response.status_code < 400:
                        delivery_time = int((timezone.now() - start_time).total_seconds() * 1000)
                        return NotificationResult(
                            success=True,
                            message_id=f"webhook_{timezone.now().timestamp()}",
                            delivery_time_ms=delivery_time,
                            metadata={
                                'status_code': response.status_code,
                                'response_headers': dict(response.headers),
                                'attempt': attempt + 1
                            }
                        )
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text}"

                except requests.exceptions.RequestException as e:
                    last_error = str(e)

                # Wait before retry (exponential backoff)
                if attempt < self.retry_count - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

            return NotificationResult(
                success=False,
                error_message=f"Webhook failed after {self.retry_count} attempts: {last_error}"
            )

        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return NotificationResult(
                success=False,
                error_message=str(e)
            )


class SlackNotificationService(NotificationService):
    """
    Slack notification service using webhooks.
    """

    def __init__(self, channel_config: Dict[str, Any]):
        super().__init__(channel_config)
        self.webhook_url = channel_config.get('webhook_url')
        self.channel = channel_config.get('channel')
        self.username = channel_config.get('username', 'Analytics Bot')
        self.icon_emoji = channel_config.get('icon_emoji', ':robot_face:')

    async def send_notification(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        """Send Slack notification."""
        start_time = timezone.now()

        try:
            if not self.webhook_url:
                return NotificationResult(
                    success=False,
                    error_message="Slack webhook URL not configured"
                )

            # Get severity from context for color coding
            severity = context.get('severity', 'info') if context else 'info'
            color_map = {
                'critical': '#ff0000',
                'error': '#ff6b6b',
                'warning': '#ffa500',
                'info': '#36a2eb',
                'success': '#4caf50'
            }

            # Prepare Slack payload
            payload = {
                'username': self.username,
                'icon_emoji': self.icon_emoji,
                'attachments': [
                    {
                        'color': color_map.get(severity, '#36a2eb'),
                        'title': subject,
                        'text': message,
                        'footer': 'Digital Signage Analytics',
                        'ts': int(timezone.now().timestamp()),
                        'fields': []
                    }
                ]
            }

            # Add channel if specified
            if self.channel:
                payload['channel'] = self.channel

            # Add context fields
            if context:
                fields = []
                if 'device_name' in context:
                    fields.append({
                        'title': 'Device',
                        'value': context['device_name'],
                        'short': True
                    })
                if 'tenant_name' in context:
                    fields.append({
                        'title': 'Tenant',
                        'value': context['tenant_name'],
                        'short': True
                    })

                payload['attachments'][0]['fields'] = fields

            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )

            delivery_time = int((timezone.now() - start_time).total_seconds() * 1000)

            if response.status_code == 200:
                return NotificationResult(
                    success=True,
                    message_id=f"slack_{timezone.now().timestamp()}",
                    delivery_time_ms=delivery_time,
                    metadata={
                        'channel': self.channel,
                        'severity': severity
                    }
                )
            else:
                return NotificationResult(
                    success=False,
                    error_message=f"Slack API error: {response.status_code} - {response.text}"
                )

        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return NotificationResult(
                success=False,
                error_message=str(e)
            )


class PushNotificationService(NotificationService):
    """
    Push notification service for mobile apps.
    """

    def __init__(self, channel_config: Dict[str, Any]):
        super().__init__(channel_config)
        self.fcm_server_key = channel_config.get('fcm_server_key')
        self.apns_config = channel_config.get('apns', {})

    async def send_notification(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        """Send push notification."""
        start_time = timezone.now()

        try:
            if not self.fcm_server_key:
                return NotificationResult(
                    success=False,
                    error_message="FCM server key not configured"
                )

            valid_tokens = self.validate_recipients(recipients)
            if not valid_tokens:
                return NotificationResult(
                    success=False,
                    error_message="No valid device tokens"
                )

            # Prepare FCM payload
            fcm_payload = {
                'registration_ids': valid_tokens,
                'notification': {
                    'title': subject,
                    'body': message,
                    'icon': 'ic_notification',
                    'sound': 'default'
                },
                'data': {
                    'type': 'alert',
                    'timestamp': timezone.now().isoformat(),
                    **(context or {})
                }
            }

            headers = {
                'Authorization': f'key={self.fcm_server_key}',
                'Content-Type': 'application/json'
            }

            # Send to FCM
            response = requests.post(
                'https://fcm.googleapis.com/fcm/send',
                json=fcm_payload,
                headers=headers,
                timeout=30
            )

            delivery_time = int((timezone.now() - start_time).total_seconds() * 1000)

            if response.status_code == 200:
                result_data = response.json()
                return NotificationResult(
                    success=True,
                    message_id=f"push_{timezone.now().timestamp()}",
                    delivery_time_ms=delivery_time,
                    metadata={
                        'success_count': result_data.get('success', 0),
                        'failure_count': result_data.get('failure', 0),
                        'canonical_ids': result_data.get('canonical_ids', 0)
                    }
                )
            else:
                return NotificationResult(
                    success=False,
                    error_message=f"FCM error: {response.status_code} - {response.text}"
                )

        except Exception as e:
            logger.error(f"Push notification failed: {e}")
            return NotificationResult(
                success=False,
                error_message=str(e)
            )


class NotificationServiceFactory:
    """
    Factory for creating notification services.
    """

    _services = {
        'email': EmailNotificationService,
        'sms': SMSNotificationService,
        'webhook': WebhookNotificationService,
        'slack': SlackNotificationService,
        'push': PushNotificationService,
    }

    @classmethod
    def create_service(
        self,
        service_type: str,
        config: Dict[str, Any]
    ) -> Optional[NotificationService]:
        """Create a notification service instance."""
        service_class = self._services.get(service_type)
        if service_class:
            return service_class(config)
        return None

    @classmethod
    def get_available_services(cls) -> List[str]:
        """Get list of available service types."""
        return list(cls._services.keys())