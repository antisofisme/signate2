# Service Architecture with Dependency Injection
# Complete service layer design for Anthias SaaS platform

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


# Base Service Classes
class BaseService(ABC):
    """Base service class with common functionality"""

    def __init__(self, tenant: Optional['Tenant'] = None, user: Optional[User] = None):
        self.tenant = tenant
        self.user = user
        self.logger = logging.getLogger(self.__class__.__name__)

    def log_action(self, action: str, resource_type: str, resource_id: str,
                   old_values: Dict = None, new_values: Dict = None):
        """Log actions for audit trail"""
        if self.tenant:
            from models import AuditLog
            AuditLog.objects.create(
                tenant=self.tenant,
                user=self.user,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values or {},
                new_values=new_values or {}
            )


class ServiceError(Exception):
    """Base service error"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ValidationError(ServiceError):
    """Service validation error"""
    pass


class PermissionError(ServiceError):
    """Service permission error"""
    pass


class LimitExceededError(ServiceError):
    """Service limit exceeded error"""
    pass


# Asset Management Service
class AssetService(BaseService):
    """Asset management service with tenant-aware operations"""

    def create_asset(self, data: Dict[str, Any]) -> 'Asset':
        """Create new asset with validation and limits check"""
        self._validate_asset_limits()
        self._validate_asset_data(data)

        with transaction.atomic():
            asset_data = {
                **data,
                'tenant': self.tenant,
                'created_by': self.user
            }

            # Handle sharing
            if data.get('is_shared', False):
                asset_data['share_code'] = self._generate_share_code()

            # Handle file upload and processing
            if 'file' in data:
                asset_data.update(self._process_file_upload(data['file']))

            from models import Asset
            asset = Asset.objects.create(**asset_data)

            self.log_action('asset.create', 'asset', asset.asset_id,
                          new_values=asset_data)

            # Trigger post-creation hooks
            self._post_asset_creation(asset)

            return asset

    def update_asset(self, asset_id: str, data: Dict[str, Any]) -> 'Asset':
        """Update existing asset"""
        from models import Asset

        try:
            asset = Asset.objects.get(asset_id=asset_id, tenant=self.tenant)
        except Asset.DoesNotExist:
            raise ServiceError(f"Asset {asset_id} not found", "ASSET_NOT_FOUND")

        old_values = {
            'name': asset.name,
            'uri': asset.uri,
            'is_enabled': asset.is_enabled,
            'tags': asset.tags,
            'metadata': asset.metadata
        }

        # Update asset fields
        for field, value in data.items():
            if hasattr(asset, field):
                setattr(asset, field, value)

        asset.updated_by = self.user
        asset.save()

        self.log_action('asset.update', 'asset', asset_id,
                       old_values=old_values, new_values=data)

        return asset

    def delete_asset(self, asset_id: str) -> bool:
        """Delete asset with cleanup"""
        from models import Asset

        try:
            asset = Asset.objects.get(asset_id=asset_id, tenant=self.tenant)
        except Asset.DoesNotExist:
            raise ServiceError(f"Asset {asset_id} not found", "ASSET_NOT_FOUND")

        with transaction.atomic():
            # Cleanup related QR codes
            asset.qrcontent_set.all().delete()

            # Cleanup files if stored locally
            self._cleanup_asset_files(asset)

            asset_data = {'name': asset.name, 'uri': asset.uri}
            asset.delete()

            self.log_action('asset.delete', 'asset', asset_id,
                          old_values=asset_data)

            return True

    def get_tenant_assets(self, filters: Dict = None, ordering: str = '-created_at') -> models.QuerySet:
        """Get tenant assets with filtering"""
        from models import Asset

        if not self.tenant:
            return Asset.objects.none()

        queryset = Asset.objects.filter(tenant=self.tenant)

        if filters:
            # Apply filters
            if 'is_enabled' in filters:
                queryset = queryset.filter(is_enabled=filters['is_enabled'])

            if 'tags' in filters:
                queryset = queryset.filter(tags__overlap=filters['tags'])

            if 'mimetype' in filters:
                queryset = queryset.filter(mimetype__icontains=filters['mimetype'])

            if 'search' in filters:
                from django.db.models import Q
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(tags__overlap=[search_term])
                )

        return queryset.order_by(ordering)

    def bulk_update_assets(self, updates: List[Dict]) -> List['Asset']:
        """Bulk update multiple assets"""
        updated_assets = []

        with transaction.atomic():
            for update_data in updates:
                asset_id = update_data.get('asset_id')
                if asset_id:
                    try:
                        asset = self.update_asset(asset_id, update_data)
                        updated_assets.append(asset)
                    except ServiceError:
                        continue

        return updated_assets

    def generate_share_code(self, asset_id: str) -> str:
        """Generate or regenerate share code for asset"""
        from models import Asset

        try:
            asset = Asset.objects.get(asset_id=asset_id, tenant=self.tenant)
        except Asset.DoesNotExist:
            raise ServiceError(f"Asset {asset_id} not found", "ASSET_NOT_FOUND")

        if not asset.can_be_shared():
            raise ValidationError("Asset cannot be shared in current state")

        asset.generate_share_code()
        asset.is_shared = True
        asset.save()

        self.log_action('asset.share_generated', 'asset', asset_id)

        return asset.share_code

    def _validate_asset_limits(self):
        """Validate tenant asset limits"""
        if not self.tenant:
            return

        current_count = self.tenant.current_asset_count
        if current_count >= self.tenant.max_assets:
            raise LimitExceededError(
                f"Asset limit reached. Current plan allows {self.tenant.max_assets} assets.",
                "ASSET_LIMIT_EXCEEDED"
            )

    def _validate_asset_data(self, data: Dict):
        """Validate asset data"""
        required_fields = ['name', 'uri']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Field '{field}' is required")

        # Validate dates
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise ValidationError("Start date must be before end date")

    def _generate_share_code(self) -> str:
        """Generate unique share code"""
        import secrets
        from models import Asset

        while True:
            code = secrets.token_urlsafe(8)
            if not Asset.objects.filter(share_code=code).exists():
                return code

    def _process_file_upload(self, file) -> Dict[str, Any]:
        """Process file upload and return metadata"""
        # This would integrate with storage service
        return {
            'file_size': file.size,
            'mimetype': file.content_type,
            'md5': self._calculate_md5(file)
        }

    def _calculate_md5(self, file) -> str:
        """Calculate MD5 hash of file"""
        import hashlib
        md5 = hashlib.md5()
        for chunk in file.chunks():
            md5.update(chunk)
        return md5.hexdigest()

    def _cleanup_asset_files(self, asset: 'Asset'):
        """Cleanup asset files from storage"""
        # This would integrate with storage service
        pass

    def _post_asset_creation(self, asset: 'Asset'):
        """Post-creation hooks"""
        # Trigger background processing if needed
        if asset.mimetype and asset.mimetype.startswith('video/'):
            # Queue video processing task
            pass


# QR Content Service
class QRService(BaseService):
    """QR/Barcode content management service"""

    def create_qr_content(self, asset_id: str, data: Dict[str, Any]) -> 'QRContent':
        """Create QR content for asset"""
        from models import Asset, QRContent

        try:
            asset = Asset.objects.get(asset_id=asset_id, tenant=self.tenant)
        except Asset.DoesNotExist:
            raise ServiceError(f"Asset {asset_id} not found", "ASSET_NOT_FOUND")

        qr_data = {
            **data,
            'tenant': self.tenant,
            'asset': asset,
            'qr_code': self._generate_qr_code(),
            'created_by': self.user
        }

        if data.get('include_barcode'):
            qr_data['barcode'] = self._generate_barcode()

        qr_content = QRContent.objects.create(**qr_data)

        self.log_action('qr_content.create', 'qr_content', str(qr_content.qr_id))

        return qr_content

    def track_qr_access(self, qr_code: str, request_data: Dict) -> Dict[str, Any]:
        """Track QR code access"""
        from models import QRContent

        try:
            qr_content = QRContent.objects.get(qr_code=qr_code, is_active=True)
        except QRContent.DoesNotExist:
            raise ServiceError("QR code not found", "QR_NOT_FOUND")

        if not qr_content.is_accessible():
            raise PermissionError("QR content is not accessible", "QR_NOT_ACCESSIBLE")

        # Log the access
        qr_content.log_access(request_data)

        return {
            'asset': qr_content.asset,
            'access_count': qr_content.access_count,
            'title': qr_content.title,
            'description': qr_content.description
        }

    def get_qr_analytics(self, qr_id: str) -> Dict[str, Any]:
        """Get QR content analytics"""
        from models import QRContent

        try:
            qr_content = QRContent.objects.get(qr_id=qr_id, tenant=self.tenant)
        except QRContent.DoesNotExist:
            raise ServiceError("QR content not found", "QR_NOT_FOUND")

        return {
            'qr_code': qr_content.qr_code,
            'total_access': qr_content.access_count,
            'last_accessed': qr_content.last_accessed,
            'created_at': qr_content.created_at,
            'is_accessible': qr_content.is_accessible(),
            'access_log': qr_content.access_log[-10:]  # Last 10 accesses
        }

    def _generate_qr_code(self) -> str:
        """Generate unique QR code"""
        import secrets
        from models import QRContent

        while True:
            code = f"QR{secrets.token_hex(8).upper()}"
            if not QRContent.objects.filter(qr_code=code).exists():
                return code

    def _generate_barcode(self) -> str:
        """Generate unique barcode"""
        import secrets
        from models import QRContent

        while True:
            code = f"BC{secrets.token_hex(6).upper()}"
            if not QRContent.objects.filter(barcode=code).exists():
                return code


# Tenant Management Service
class TenantService(BaseService):
    """Tenant management and user operations"""

    def create_tenant(self, data: Dict[str, Any]) -> 'Tenant':
        """Create new tenant"""
        self._validate_tenant_data(data)

        from models import Tenant, TenantUser

        tenant_data = {
            **data,
            'subdomain': data['subdomain'].lower()
        }

        tenant = Tenant.objects.create(**tenant_data)

        # Create owner relationship
        if self.user:
            TenantUser.objects.create(
                user=self.user,
                tenant=tenant,
                role='owner'
            )

        self.log_action('tenant.create', 'tenant', str(tenant.tenant_id))

        return tenant

    def invite_user(self, email: str, role: str = 'viewer') -> Dict[str, Any]:
        """Invite user to tenant"""
        if not self.tenant:
            raise ServiceError("Tenant context required", "TENANT_REQUIRED")

        # Check user limit
        if self.tenant.current_user_count >= self.tenant.max_users:
            raise LimitExceededError("User limit reached", "USER_LIMIT_EXCEEDED")

        from models import TenantUser

        # Create or get user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email}
        )

        # Check if user already belongs to tenant
        if TenantUser.objects.filter(user=user, tenant=self.tenant).exists():
            raise ValidationError("User already belongs to this tenant")

        tenant_user = TenantUser.objects.create(
            user=user,
            tenant=self.tenant,
            role=role,
            invited_by=self.user
        )

        self.log_action('user.invite', 'tenant_user', str(tenant_user.id))

        # Send invitation email (would integrate with email service)
        self._send_invitation_email(user, tenant_user)

        return {
            'user_id': user.id,
            'email': email,
            'role': role,
            'invitation_sent': True
        }

    def update_user_role(self, user_id: int, new_role: str) -> 'TenantUser':
        """Update user role in tenant"""
        from models import TenantUser

        try:
            tenant_user = TenantUser.objects.get(
                user_id=user_id,
                tenant=self.tenant
            )
        except TenantUser.DoesNotExist:
            raise ServiceError("User not found in tenant", "USER_NOT_FOUND")

        old_role = tenant_user.role
        tenant_user.role = new_role
        tenant_user.save()

        self.log_action('user.role_update', 'tenant_user', str(tenant_user.id),
                       old_values={'role': old_role}, new_values={'role': new_role})

        return tenant_user

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get tenant usage statistics"""
        if not self.tenant:
            raise ServiceError("Tenant context required", "TENANT_REQUIRED")

        return {
            'assets': {
                'current': self.tenant.current_asset_count,
                'limit': self.tenant.max_assets,
                'usage_percentage': (self.tenant.current_asset_count / self.tenant.max_assets) * 100
            },
            'users': {
                'current': self.tenant.current_user_count,
                'limit': self.tenant.max_users,
                'usage_percentage': (self.tenant.current_user_count / self.tenant.max_users) * 100
            },
            'storage': {
                'current_gb': self.tenant.storage_used_gb,
                'limit_gb': self.tenant.storage_quota_gb,
                'usage_percentage': (self.tenant.storage_used_gb / self.tenant.storage_quota_gb) * 100
            }
        }

    def _validate_tenant_data(self, data: Dict):
        """Validate tenant creation data"""
        from models import Tenant

        required_fields = ['name', 'subdomain']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Field '{field}' is required")

        # Validate subdomain uniqueness
        if Tenant.objects.filter(subdomain=data['subdomain'].lower()).exists():
            raise ValidationError("Subdomain already taken")

        # Validate subdomain format
        import re
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', data['subdomain'].lower()):
            raise ValidationError("Invalid subdomain format")

    def _send_invitation_email(self, user: User, tenant_user: 'TenantUser'):
        """Send invitation email to user"""
        # This would integrate with email service
        pass


# Subscription Service
class SubscriptionService(BaseService):
    """Subscription and billing management"""

    def __init__(self, tenant: Optional['Tenant'] = None, user: Optional[User] = None):
        super().__init__(tenant, user)
        self.payment_provider = self._get_payment_provider()

    def create_subscription(self, plan_name: str, payment_data: Dict) -> 'Subscription':
        """Create new subscription"""
        if not self.tenant:
            raise ServiceError("Tenant context required", "TENANT_REQUIRED")

        # Get plan details
        plan_config = self._get_plan_config(plan_name)

        # Create subscription with payment provider
        external_subscription = self.payment_provider.create_subscription(
            tenant=self.tenant,
            plan_config=plan_config,
            payment_data=payment_data
        )

        from models import Subscription

        subscription = Subscription.objects.create(
            tenant=self.tenant,
            plan_name=plan_name,
            billing_cycle=plan_config['billing_cycle'],
            amount=plan_config['amount'],
            currency=plan_config['currency'],
            status='active',
            current_period_start=timezone.now(),
            current_period_end=self._calculate_period_end(plan_config['billing_cycle']),
            payment_provider='midtrans',
            external_subscription_id=external_subscription['subscription_id'],
            external_customer_id=external_subscription['customer_id']
        )

        # Update tenant limits based on plan
        self._update_tenant_limits(plan_config)

        self.log_action('subscription.create', 'subscription', str(subscription.subscription_id))

        return subscription

    def upgrade_plan(self, new_plan_name: str) -> 'Subscription':
        """Upgrade subscription plan"""
        if not self.tenant:
            raise ServiceError("Tenant context required", "TENANT_REQUIRED")

        try:
            subscription = self.tenant.subscription
        except:
            raise ServiceError("No active subscription found", "SUBSCRIPTION_NOT_FOUND")

        old_plan = subscription.plan_name
        plan_config = self._get_plan_config(new_plan_name)

        # Upgrade with payment provider
        self.payment_provider.upgrade_subscription(
            subscription.external_subscription_id,
            plan_config
        )

        # Update subscription
        subscription.plan_name = new_plan_name
        subscription.amount = plan_config['amount']
        subscription.save()

        # Update tenant limits
        self._update_tenant_limits(plan_config)

        self.log_action('subscription.upgrade', 'subscription', str(subscription.subscription_id),
                       old_values={'plan': old_plan}, new_values={'plan': new_plan_name})

        return subscription

    def cancel_subscription(self) -> bool:
        """Cancel subscription"""
        if not self.tenant:
            raise ServiceError("Tenant context required", "TENANT_REQUIRED")

        try:
            subscription = self.tenant.subscription
        except:
            raise ServiceError("No active subscription found", "SUBSCRIPTION_NOT_FOUND")

        # Cancel with payment provider
        self.payment_provider.cancel_subscription(subscription.external_subscription_id)

        # Update subscription status
        subscription.status = 'canceled'
        subscription.canceled_at = timezone.now()
        subscription.save()

        self.log_action('subscription.cancel', 'subscription', str(subscription.subscription_id))

        return True

    def _get_payment_provider(self):
        """Get payment provider instance"""
        from services.payment_providers import PaymentProviderFactory
        return PaymentProviderFactory.get_provider('midtrans')

    def _get_plan_config(self, plan_name: str) -> Dict:
        """Get plan configuration"""
        plans = {
            'basic': {
                'max_assets': 100,
                'max_devices': 5,
                'max_users': 10,
                'storage_quota_gb': 10,
                'amount': 29.99,
                'currency': 'USD',
                'billing_cycle': 'monthly'
            },
            'professional': {
                'max_assets': 500,
                'max_devices': 25,
                'max_users': 50,
                'storage_quota_gb': 100,
                'amount': 99.99,
                'currency': 'USD',
                'billing_cycle': 'monthly'
            },
            'enterprise': {
                'max_assets': 9999,
                'max_devices': 9999,
                'max_users': 9999,
                'storage_quota_gb': 1000,
                'amount': 299.99,
                'currency': 'USD',
                'billing_cycle': 'monthly'
            }
        }

        if plan_name not in plans:
            raise ValidationError(f"Invalid plan: {plan_name}")

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

    def _update_tenant_limits(self, plan_config: Dict):
        """Update tenant limits based on plan"""
        self.tenant.max_assets = plan_config['max_assets']
        self.tenant.max_devices = plan_config['max_devices']
        self.tenant.max_users = plan_config['max_users']
        self.tenant.storage_quota_gb = plan_config['storage_quota_gb']
        self.tenant.save()


# Dependency Injection Container
class ServiceContainer:
    """Service container for dependency injection"""
    _services = {}
    _instances = {}

    @classmethod
    def register(cls, service_class, name: str = None):
        """Register service class"""
        name = name or service_class.__name__.lower().replace('service', '')
        cls._services[name] = service_class

    @classmethod
    def get(cls, service_name: str, tenant: Optional['Tenant'] = None,
            user: Optional[User] = None, **kwargs):
        """Get service instance"""
        if service_name not in cls._services:
            raise ValueError(f"Service '{service_name}' not registered")

        # Create cache key for singleton services
        cache_key = f"{service_name}_{id(tenant)}_{id(user)}"

        if cache_key not in cls._instances:
            service_class = cls._services[service_name]
            cls._instances[cache_key] = service_class(tenant=tenant, user=user, **kwargs)

        return cls._instances[cache_key]

    @classmethod
    def clear_cache(cls):
        """Clear service instances cache"""
        cls._instances.clear()


# Register all services
ServiceContainer.register(AssetService, 'asset')
ServiceContainer.register(QRService, 'qr')
ServiceContainer.register(TenantService, 'tenant')
ServiceContainer.register(SubscriptionService, 'subscription')


# Service Factory for easy access
class ServiceFactory:
    """Factory for creating service instances"""

    @staticmethod
    def create_asset_service(tenant: 'Tenant', user: User) -> AssetService:
        return ServiceContainer.get('asset', tenant=tenant, user=user)

    @staticmethod
    def create_qr_service(tenant: 'Tenant', user: User) -> QRService:
        return ServiceContainer.get('qr', tenant=tenant, user=user)

    @staticmethod
    def create_tenant_service(tenant: 'Tenant' = None, user: User = None) -> TenantService:
        return ServiceContainer.get('tenant', tenant=tenant, user=user)

    @staticmethod
    def create_subscription_service(tenant: 'Tenant', user: User) -> SubscriptionService:
        return ServiceContainer.get('subscription', tenant=tenant, user=user)