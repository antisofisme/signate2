# Subscription Billing Integration Architecture
# Complete billing system with Midtrans integration and multi-provider support

import json
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.core.mail import send_mail
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


# Abstract Payment Provider Interface
class PaymentProviderInterface:
    """Abstract interface for payment providers"""

    def create_customer(self, tenant: 'Tenant', customer_data: Dict) -> Dict[str, Any]:
        """Create customer in payment provider"""
        raise NotImplementedError

    def create_subscription(self, customer_id: str, plan_data: Dict) -> Dict[str, Any]:
        """Create subscription"""
        raise NotImplementedError

    def update_subscription(self, subscription_id: str, plan_data: Dict) -> Dict[str, Any]:
        """Update existing subscription"""
        raise NotImplementedError

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel subscription"""
        raise NotImplementedError

    def create_one_time_payment(self, customer_id: str, amount: Decimal, currency: str) -> Dict[str, Any]:
        """Create one-time payment"""
        raise NotImplementedError

    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription status from provider"""
        raise NotImplementedError

    def validate_webhook(self, payload: str, signature: str) -> bool:
        """Validate webhook signature"""
        raise NotImplementedError

    def process_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Process webhook data"""
        raise NotImplementedError


# Midtrans Payment Provider Implementation
class MidtransProvider(PaymentProviderInterface):
    """Midtrans payment provider implementation"""

    def __init__(self):
        self.server_key = settings.MIDTRANS_SERVER_KEY
        self.client_key = settings.MIDTRANS_CLIENT_KEY
        self.is_production = settings.MIDTRANS_IS_PRODUCTION
        self.base_url = (
            "https://api.midtrans.com/v2" if self.is_production
            else "https://api.sandbox.midtrans.com/v2"
        )
        self.snap_url = (
            "https://app.midtrans.com/snap/v1" if self.is_production
            else "https://app.sandbox.midtrans.com/snap/v1"
        )

    def create_customer(self, tenant: 'Tenant', customer_data: Dict) -> Dict[str, Any]:
        """Create customer in Midtrans"""
        # Midtrans doesn't have separate customer creation,
        # customer data is included in each transaction
        return {
            'customer_id': f"tenant_{tenant.tenant_id}",
            'provider': 'midtrans',
            'customer_details': customer_data
        }

    def create_subscription(self, customer_id: str, plan_data: Dict) -> Dict[str, Any]:
        """Create subscription using Midtrans Snap"""
        subscription_id = f"sub_{timezone.now().strftime('%Y%m%d%H%M%S')}_{customer_id}"

        # For recurring payments, we'll use Midtrans Core API
        # and handle recurring logic ourselves
        transaction_data = {
            'transaction_details': {
                'order_id': subscription_id,
                'gross_amount': int(plan_data['amount'] * 100)  # Convert to cents
            },
            'customer_details': plan_data.get('customer_details', {}),
            'item_details': [{
                'id': plan_data['plan_id'],
                'price': int(plan_data['amount'] * 100),
                'quantity': 1,
                'name': f"{plan_data['plan_name']} Subscription"
            }],
            'credit_card': {
                'secure': True
            }
        }

        try:
            response = self._make_request('POST', f"{self.snap_url}/transactions", transaction_data)

            if response.get('token'):
                return {
                    'subscription_id': subscription_id,
                    'payment_token': response['token'],
                    'payment_url': response['redirect_url'],
                    'status': 'pending'
                }
            else:
                raise Exception(f"Failed to create payment token: {response}")

        except Exception as e:
            logger.error(f"Midtrans subscription creation failed: {str(e)}")
            raise

    def update_subscription(self, subscription_id: str, plan_data: Dict) -> Dict[str, Any]:
        """Update subscription plan"""
        # For plan changes, we cancel current and create new
        self.cancel_subscription(subscription_id)
        return self.create_subscription(subscription_id.split('_')[1], plan_data)

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel subscription"""
        try:
            response = self._make_request('POST', f"{self.base_url}/{subscription_id}/cancel")
            return {
                'subscription_id': subscription_id,
                'status': 'cancelled',
                'cancelled_at': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Midtrans subscription cancellation failed: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def create_one_time_payment(self, customer_id: str, amount: Decimal, currency: str = 'IDR') -> Dict[str, Any]:
        """Create one-time payment"""
        order_id = f"pay_{timezone.now().strftime('%Y%m%d%H%M%S')}_{customer_id}"

        transaction_data = {
            'transaction_details': {
                'order_id': order_id,
                'gross_amount': int(amount * 100)
            },
            'credit_card': {
                'secure': True
            }
        }

        try:
            response = self._make_request('POST', f"{self.snap_url}/transactions", transaction_data)
            return {
                'payment_id': order_id,
                'payment_token': response['token'],
                'payment_url': response['redirect_url'],
                'status': 'pending'
            }
        except Exception as e:
            logger.error(f"Midtrans payment creation failed: {str(e)}")
            raise

    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription status"""
        try:
            response = self._make_request('GET', f"{self.base_url}/{subscription_id}/status")
            return {
                'subscription_id': subscription_id,
                'status': response.get('transaction_status'),
                'payment_type': response.get('payment_type'),
                'transaction_time': response.get('transaction_time')
            }
        except Exception as e:
            logger.error(f"Failed to get subscription status: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def validate_webhook(self, payload: str, signature: str) -> bool:
        """Validate Midtrans webhook signature"""
        expected_signature = hashlib.sha512(
            (payload + self.server_key).encode('utf-8')
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)

    def process_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Process Midtrans webhook"""
        order_id = webhook_data.get('order_id')
        transaction_status = webhook_data.get('transaction_status')
        payment_type = webhook_data.get('payment_type')

        return {
            'order_id': order_id,
            'status': transaction_status,
            'payment_type': payment_type,
            'processed_at': timezone.now(),
            'raw_data': webhook_data
        }

    def _make_request(self, method: str, url: str, data: Dict = None) -> Dict:
        """Make authenticated request to Midtrans API"""
        import base64

        auth_string = base64.b64encode(f"{self.server_key}:".encode()).decode()
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Midtrans API request failed: {str(e)}")
            raise


# Stripe Provider (Alternative Implementation)
class StripeProvider(PaymentProviderInterface):
    """Stripe payment provider implementation"""

    def __init__(self):
        try:
            import stripe
            self.stripe = stripe
            self.stripe.api_key = settings.STRIPE_SECRET_KEY
        except ImportError:
            raise ImportError("Stripe library not installed")

    def create_customer(self, tenant: 'Tenant', customer_data: Dict) -> Dict[str, Any]:
        """Create Stripe customer"""
        try:
            customer = self.stripe.Customer.create(
                email=customer_data.get('email'),
                name=customer_data.get('name', tenant.name),
                metadata={
                    'tenant_id': str(tenant.tenant_id),
                    'tenant_name': tenant.name
                }
            )

            return {
                'customer_id': customer.id,
                'provider': 'stripe',
                'customer_details': customer_data
            }

        except Exception as e:
            logger.error(f"Stripe customer creation failed: {str(e)}")
            raise

    def create_subscription(self, customer_id: str, plan_data: Dict) -> Dict[str, Any]:
        """Create Stripe subscription"""
        try:
            subscription = self.stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price_data': {
                        'currency': plan_data.get('currency', 'usd'),
                        'product_data': {
                            'name': plan_data['plan_name']
                        },
                        'unit_amount': int(plan_data['amount'] * 100),
                        'recurring': {
                            'interval': plan_data.get('billing_cycle', 'month')
                        }
                    }
                }],
                trial_period_days=plan_data.get('trial_days', 0)
            )

            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end
            }

        except Exception as e:
            logger.error(f"Stripe subscription creation failed: {str(e)}")
            raise

    def validate_webhook(self, payload: str, signature: str) -> bool:
        """Validate Stripe webhook signature"""
        try:
            self.stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            return True
        except:
            return False

    def process_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Process Stripe webhook"""
        event_type = webhook_data.get('type')
        data = webhook_data.get('data', {}).get('object', {})

        return {
            'event_type': event_type,
            'subscription_id': data.get('id'),
            'status': data.get('status'),
            'processed_at': timezone.now(),
            'raw_data': webhook_data
        }


# Payment Provider Factory
class PaymentProviderFactory:
    """Factory for creating payment provider instances"""

    _providers = {
        'midtrans': MidtransProvider,
        'stripe': StripeProvider
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> PaymentProviderInterface:
        """Get payment provider instance"""
        if provider_name not in cls._providers:
            raise ValueError(f"Unsupported payment provider: {provider_name}")

        return cls._providers[provider_name]()

    @classmethod
    def register_provider(cls, name: str, provider_class):
        """Register new payment provider"""
        cls._providers[name] = provider_class


# Subscription Management Service
class SubscriptionService:
    """Service for managing subscriptions and billing"""

    def __init__(self, tenant: 'Tenant'):
        self.tenant = tenant
        self.provider_name = getattr(settings, 'DEFAULT_PAYMENT_PROVIDER', 'midtrans')
        self.provider = PaymentProviderFactory.get_provider(self.provider_name)

    def create_subscription(self, plan_name: str, customer_data: Dict,
                          payment_method: str = None) -> 'Subscription':
        """Create new subscription"""
        from models import Subscription

        plan_config = self._get_plan_config(plan_name)

        with transaction.atomic():
            # Create customer in payment provider
            customer_result = self.provider.create_customer(self.tenant, customer_data)

            # Create subscription in payment provider
            subscription_data = {
                **plan_config,
                'customer_details': customer_data,
                'payment_method': payment_method
            }

            provider_result = self.provider.create_subscription(
                customer_result['customer_id'],
                subscription_data
            )

            # Create subscription record
            subscription = Subscription.objects.create(
                tenant=self.tenant,
                plan_name=plan_name,
                plan_features=plan_config.get('features', {}),
                billing_cycle=plan_config['billing_cycle'],
                status='pending',
                amount=plan_config['amount'],
                currency=plan_config.get('currency', 'USD'),
                current_period_start=timezone.now(),
                current_period_end=self._calculate_period_end(plan_config['billing_cycle']),
                payment_provider=self.provider_name,
                external_subscription_id=provider_result['subscription_id'],
                external_customer_id=customer_result['customer_id']
            )

            # Update tenant plan
            self._update_tenant_plan(plan_config)

            # Store payment token for completion
            if 'payment_token' in provider_result:
                cache.set(
                    f"payment_token_{subscription.subscription_id}",
                    provider_result['payment_token'],
                    timeout=3600  # 1 hour
                )

            return subscription

    def upgrade_subscription(self, new_plan_name: str) -> 'Subscription':
        """Upgrade subscription to new plan"""
        from models import Subscription

        try:
            subscription = self.tenant.subscription
        except Subscription.DoesNotExist:
            raise ValueError("No active subscription found")

        old_plan = subscription.plan_name
        new_plan_config = self._get_plan_config(new_plan_name)

        with transaction.atomic():
            # Calculate prorated amount
            prorated_amount = self._calculate_proration(subscription, new_plan_config)

            # Update with payment provider
            provider_result = self.provider.update_subscription(
                subscription.external_subscription_id,
                new_plan_config
            )

            # Update subscription record
            subscription.plan_name = new_plan_name
            subscription.plan_features = new_plan_config.get('features', {})
            subscription.amount = new_plan_config['amount']
            subscription.save()

            # Update tenant limits
            self._update_tenant_plan(new_plan_config)

            # Record billing event
            self._record_billing_event(
                subscription,
                'plan_upgrade',
                {
                    'old_plan': old_plan,
                    'new_plan': new_plan_name,
                    'prorated_amount': prorated_amount
                }
            )

            # Send notification
            self._send_upgrade_notification(subscription, old_plan, new_plan_name)

            return subscription

    def cancel_subscription(self, cancellation_reason: str = None) -> bool:
        """Cancel subscription"""
        from models import Subscription

        try:
            subscription = self.tenant.subscription
        except Subscription.DoesNotExist:
            raise ValueError("No active subscription found")

        with transaction.atomic():
            # Cancel with payment provider
            self.provider.cancel_subscription(subscription.external_subscription_id)

            # Update subscription status
            subscription.status = 'canceled'
            subscription.canceled_at = timezone.now()
            subscription.save()

            # Downgrade tenant to free plan
            self._downgrade_to_free_plan()

            # Record billing event
            self._record_billing_event(
                subscription,
                'cancellation',
                {'reason': cancellation_reason}
            )

            # Send cancellation confirmation
            self._send_cancellation_notification(subscription, cancellation_reason)

            return True

    def process_payment_webhook(self, webhook_data: Dict, signature: str) -> Dict[str, Any]:
        """Process payment webhook"""
        # Validate webhook
        if not self.provider.validate_webhook(json.dumps(webhook_data), signature):
            raise ValueError("Invalid webhook signature")

        # Process webhook data
        processed_data = self.provider.process_webhook(webhook_data)

        # Update subscription based on webhook
        self._handle_webhook_event(processed_data)

        return processed_data

    def get_billing_history(self, limit: int = 50) -> List[Dict]:
        """Get billing history for tenant"""
        from models import BillingEvent

        events = BillingEvent.objects.filter(
            subscription__tenant=self.tenant
        ).order_by('-created_at')[:limit]

        return [{
            'event_type': event.event_type,
            'amount': event.amount,
            'currency': event.currency,
            'description': event.description,
            'created_at': event.created_at,
            'metadata': event.metadata
        } for event in events]

    def _get_plan_config(self, plan_name: str) -> Dict:
        """Get plan configuration"""
        plans = {
            'basic': {
                'plan_id': 'basic_monthly',
                'max_assets': 100,
                'max_devices': 5,
                'max_users': 10,
                'storage_quota_gb': 10,
                'amount': Decimal('29.99'),
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'features': {
                    'qr_sharing': True,
                    'analytics': True,
                    'api_access': True,
                    'support_level': 'email'
                }
            },
            'professional': {
                'plan_id': 'pro_monthly',
                'max_assets': 500,
                'max_devices': 25,
                'max_users': 50,
                'storage_quota_gb': 100,
                'amount': Decimal('99.99'),
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'features': {
                    'qr_sharing': True,
                    'analytics': True,
                    'api_access': True,
                    'custom_branding': True,
                    'support_level': 'priority'
                }
            },
            'enterprise': {
                'plan_id': 'enterprise_monthly',
                'max_assets': 9999,
                'max_devices': 9999,
                'max_users': 9999,
                'storage_quota_gb': 1000,
                'amount': Decimal('299.99'),
                'currency': 'USD',
                'billing_cycle': 'monthly',
                'features': {
                    'qr_sharing': True,
                    'analytics': True,
                    'api_access': True,
                    'custom_branding': True,
                    'white_label': True,
                    'support_level': 'dedicated'
                }
            }
        }

        if plan_name not in plans:
            raise ValueError(f"Invalid plan: {plan_name}")

        return plans[plan_name]

    def _calculate_period_end(self, billing_cycle: str):
        """Calculate subscription period end"""
        from dateutil.relativedelta import relativedelta

        if billing_cycle == 'monthly':
            return timezone.now() + relativedelta(months=1)
        elif billing_cycle == 'yearly':
            return timezone.now() + relativedelta(years=1)
        else:
            return timezone.now() + relativedelta(months=1)

    def _calculate_proration(self, subscription: 'Subscription', new_plan_config: Dict) -> Decimal:
        """Calculate prorated amount for plan upgrade"""
        # Simple proration calculation
        days_remaining = (subscription.current_period_end - timezone.now()).days
        total_days = 30  # Assume 30-day billing cycle

        old_daily_rate = subscription.amount / total_days
        new_daily_rate = new_plan_config['amount'] / total_days

        return (new_daily_rate - old_daily_rate) * days_remaining

    def _update_tenant_plan(self, plan_config: Dict):
        """Update tenant limits based on plan"""
        self.tenant.plan_type = plan_config.get('plan_id', 'basic')
        self.tenant.max_assets = plan_config['max_assets']
        self.tenant.max_devices = plan_config['max_devices']
        self.tenant.max_users = plan_config['max_users']
        self.tenant.storage_quota_gb = plan_config['storage_quota_gb']
        self.tenant.save()

    def _downgrade_to_free_plan(self):
        """Downgrade tenant to free plan limits"""
        self.tenant.plan_type = 'free'
        self.tenant.max_assets = 10
        self.tenant.max_devices = 1
        self.tenant.max_users = 1
        self.tenant.storage_quota_gb = 1
        self.tenant.save()

    def _record_billing_event(self, subscription: 'Subscription', event_type: str, metadata: Dict):
        """Record billing event"""
        from models import BillingEvent

        BillingEvent.objects.create(
            subscription=subscription,
            event_type=event_type,
            amount=subscription.amount,
            currency=subscription.currency,
            description=f"Subscription {event_type}",
            metadata=metadata
        )

    def _handle_webhook_event(self, processed_data: Dict):
        """Handle webhook event and update subscription"""
        from models import Subscription

        subscription_id = processed_data.get('subscription_id') or processed_data.get('order_id')
        if not subscription_id:
            return

        try:
            subscription = Subscription.objects.get(
                external_subscription_id=subscription_id
            )

            status = processed_data.get('status')
            if status in ['settlement', 'capture', 'success']:
                subscription.status = 'active'
            elif status in ['failure', 'deny', 'cancel', 'expire']:
                subscription.status = 'past_due'
            elif status in ['pending']:
                subscription.status = 'pending'

            subscription.save()

            # Record webhook event
            self._record_billing_event(
                subscription,
                f"webhook_{status}",
                processed_data
            )

        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found for webhook: {subscription_id}")

    def _send_upgrade_notification(self, subscription: 'Subscription', old_plan: str, new_plan: str):
        """Send plan upgrade notification"""
        # Implementation would send email notification
        pass

    def _send_cancellation_notification(self, subscription: 'Subscription', reason: str):
        """Send cancellation confirmation"""
        # Implementation would send email notification
        pass


# Billing Event Model (add to models.py)
class BillingEvent:
    """Model for tracking billing events"""

    def __init__(self):
        # This would be added to the models.py file
        pass

"""
# Add to models.py:

class BillingEvent(models.Model):
    billing_event_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)

    event_type = models.CharField(max_length=50)  # payment, refund, upgrade, etc.
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    description = models.TextField()
    metadata = models.JSONField(default=dict)

    external_transaction_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'billing_events'
        indexes = [
            models.Index(fields=['subscription', 'created_at']),
            models.Index(fields=['event_type']),
        ]
"""

# Background Tasks
@shared_task
def process_subscription_renewals():
    """Background task to process subscription renewals"""
    from models import Subscription

    # Get subscriptions expiring in next 3 days
    upcoming_renewals = Subscription.objects.filter(
        status='active',
        current_period_end__lte=timezone.now() + timedelta(days=3),
        current_period_end__gte=timezone.now()
    )

    for subscription in upcoming_renewals:
        try:
            service = SubscriptionService(subscription.tenant)
            # Process renewal logic here
            logger.info(f"Processing renewal for subscription {subscription.subscription_id}")

        except Exception as e:
            logger.error(f"Renewal processing failed for {subscription.subscription_id}: {str(e)}")


@shared_task
def handle_failed_payments():
    """Handle failed payment retries"""
    from models import Subscription

    # Get subscriptions with failed payments
    failed_subscriptions = Subscription.objects.filter(
        status='past_due'
    )

    for subscription in failed_subscriptions:
        try:
            # Implement retry logic
            service = SubscriptionService(subscription.tenant)
            # Attempt payment retry
            logger.info(f"Retrying payment for subscription {subscription.subscription_id}")

        except Exception as e:
            logger.error(f"Payment retry failed for {subscription.subscription_id}: {str(e)}")


# Webhook Views
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
import json

@csrf_exempt
@require_POST
def midtrans_webhook(request):
    """Handle Midtrans webhook"""
    try:
        webhook_data = json.loads(request.body)
        signature = request.headers.get('X-Signature', '')

        # Process webhook
        provider = PaymentProviderFactory.get_provider('midtrans')
        if provider.validate_webhook(request.body.decode(), signature):
            result = provider.process_webhook(webhook_data)

            # Find subscription and update
            # Implementation would update subscription status

            return HttpResponse('OK', status=200)
        else:
            return HttpResponse('Invalid signature', status=400)

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        return HttpResponse('Error', status=500)


# Settings Configuration
BILLING_SETTINGS = {
    'DEFAULT_PAYMENT_PROVIDER': 'midtrans',
    'MIDTRANS_SERVER_KEY': 'your-midtrans-server-key',
    'MIDTRANS_CLIENT_KEY': 'your-midtrans-client-key',
    'MIDTRANS_IS_PRODUCTION': False,
    'STRIPE_SECRET_KEY': 'your-stripe-secret-key',
    'STRIPE_WEBHOOK_SECRET': 'your-stripe-webhook-secret',
    'BILLING_EMAIL_FROM': 'billing@anthias.com',
    'BILLING_GRACE_PERIOD_DAYS': 7,
    'MAX_PAYMENT_RETRIES': 3,
}