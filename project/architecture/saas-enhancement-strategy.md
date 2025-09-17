# Anthias SaaS Platform Enhancement Strategy

## Executive Summary

This document outlines a comprehensive strategy to transform the existing Anthias digital signage backend into a scalable B2B SaaS platform while maintaining full backwards compatibility for existing users.

## Current Architecture Analysis

### Existing Components
- **Framework**: Django 3.2.18 with Django REST Framework
- **Database**: SQLite with single Asset model
- **Authentication**: Basic session-based auth with lib.auth
- **Real-time**: ZeroMQ WebSocket communication
- **API**: Versioned REST API (v1, v1.1, v1.2, v2)
- **Architecture**: Single-tenant monolithic design

### Key Models
```python
# Current Asset Model (simplified)
class Asset(models.Model):
    asset_id = models.TextField(primary_key=True)
    name = models.TextField()
    uri = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    duration = models.BigIntegerField()
    mimetype = models.TextField()
    is_enabled = models.BooleanField()
    play_order = models.IntegerField()
```

### Current API Structure
- `/api/v1/` - Legacy endpoints
- `/api/v1.1/` - Enhanced legacy
- `/api/v1.2/` - Extended features
- `/api/v2/` - Current stable version

## SaaS Enhancement Architecture

### 1. Multi-Tenant Database Schema Design

```python
# New Multi-Tenant Models
class Tenant(models.Model):
    tenant_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=100, unique=True)
    custom_domain = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    plan_type = models.CharField(max_length=50, default='basic')
    max_assets = models.IntegerField(default=100)
    max_devices = models.IntegerField(default=5)
    storage_quota_gb = models.IntegerField(default=10)

    class Meta:
        db_table = 'tenants'

class TenantUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer')
    ])
    permissions = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenant_users'
        unique_together = ['user', 'tenant']

# Enhanced Asset Model with Multi-Tenancy
class Asset(models.Model):
    asset_id = models.TextField(primary_key=True, default=generate_asset_id)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    name = models.TextField(blank=True, null=True)
    uri = models.TextField(blank=True, null=True)
    md5 = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    duration = models.BigIntegerField(blank=True, null=True)
    mimetype = models.TextField(blank=True, null=True)
    is_enabled = models.BooleanField(default=False)
    is_processing = models.BooleanField(default=False)
    nocache = models.BooleanField(default=False)
    play_order = models.IntegerField(default=0)
    skip_asset_check = models.BooleanField(default=False)
    # New SaaS fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_shared = models.BooleanField(default=False)
    share_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    tags = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'assets'
        indexes = [
            models.Index(fields=['tenant', 'is_enabled']),
            models.Index(fields=['tenant', 'play_order']),
            models.Index(fields=['share_code']),
        ]

class Subscription(models.Model):
    subscription_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('trialing', 'Trialing')
    ])
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_provider = models.CharField(max_length=50)
    external_subscription_id = models.CharField(max_length=255)
    trial_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'subscriptions'

class QRContent(models.Model):
    qr_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    qr_code = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=50, unique=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'qr_contents'
        indexes = [
            models.Index(fields=['qr_code']),
            models.Index(fields=['barcode']),
            models.Index(fields=['tenant', 'is_active']),
        ]
```

### 2. API Enhancement Strategy (v3 Endpoints)

#### Backwards Compatibility Layer
```python
# api/middleware/tenant_middleware.py
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Legacy compatibility: no tenant for existing endpoints
        if request.path.startswith('/api/v1') or request.path.startswith('/api/v2'):
            request.tenant = None  # Backwards compatibility
        else:
            # New v3+ endpoints require tenant
            request.tenant = self.get_tenant_from_request(request)

        response = self.get_response(request)
        return response

    def get_tenant_from_request(self, request):
        # Extract tenant from subdomain or header
        host = request.get_host().split(':')[0]
        if '.' in host:
            subdomain = host.split('.')[0]
            try:
                return Tenant.objects.get(subdomain=subdomain, is_active=True)
            except Tenant.DoesNotExist:
                pass

        # Fallback to header-based tenant identification
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                return Tenant.objects.get(tenant_id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                pass

        return None
```

#### Enhanced API Versioning
```python
# api/urls/v3.py
from django.urls import path, include
from api.views.v3 import (
    TenantAssetViewSet,
    QRContentViewSet,
    TenantManagementViewSet,
    SubscriptionViewSet
)

def get_url_patterns():
    return [
        # Tenant-aware asset management
        path('v3/assets/', TenantAssetViewSet.as_view({
            'get': 'list',
            'post': 'create'
        })),
        path('v3/assets/<str:asset_id>/', TenantAssetViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy'
        })),

        # QR/Barcode content sharing
        path('v3/qr-content/', QRContentViewSet.as_view({
            'get': 'list',
            'post': 'create'
        })),
        path('v3/qr-content/<str:qr_code>/', QRContentViewSet.as_view({
            'get': 'retrieve'
        })),

        # Tenant management
        path('v3/tenant/', TenantManagementViewSet.as_view({
            'get': 'retrieve',
            'put': 'update'
        })),

        # Subscription management
        path('v3/subscription/', SubscriptionViewSet.as_view({
            'get': 'retrieve',
            'post': 'create',
            'put': 'update'
        })),

        # Legacy endpoints proxy (backwards compatibility)
        path('v3/legacy/', include('api.urls.legacy_proxy')),
    ]
```

### 3. Service Architecture with Dependency Injection

```python
# services/base.py
from abc import ABC, abstractmethod
from typing import Optional
from django.db import models

class BaseService(ABC):
    def __init__(self, tenant: Optional['Tenant'] = None):
        self.tenant = tenant

# services/asset_service.py
class AssetService(BaseService):
    def create_asset(self, data: dict, user: 'User') -> 'Asset':
        asset_data = {
            **data,
            'tenant': self.tenant,
            'created_by': user
        }

        # Generate share code if sharing is enabled
        if data.get('is_shared', False):
            asset_data['share_code'] = self._generate_share_code()

        asset = Asset.objects.create(**asset_data)
        return asset

    def get_tenant_assets(self, filters: dict = None) -> models.QuerySet:
        queryset = Asset.objects.filter(tenant=self.tenant)
        if filters:
            queryset = queryset.filter(**filters)
        return queryset

    def _generate_share_code(self) -> str:
        import secrets
        return secrets.token_urlsafe(8)

# services/qr_service.py
class QRService(BaseService):
    def create_qr_content(self, asset: 'Asset', data: dict) -> 'QRContent':
        qr_data = {
            **data,
            'tenant': self.tenant,
            'asset': asset,
            'qr_code': self._generate_qr_code(),
            'barcode': self._generate_barcode() if data.get('include_barcode') else None
        }

        return QRContent.objects.create(**qr_data)

    def _generate_qr_code(self) -> str:
        import secrets
        return f"QR{secrets.token_hex(8).upper()}"

    def _generate_barcode(self) -> str:
        import secrets
        return f"BC{secrets.token_hex(6).upper()}"

# services/subscription_service.py
class SubscriptionService(BaseService):
    def __init__(self, tenant: Optional['Tenant'] = None):
        super().__init__(tenant)
        self.payment_provider = self._get_payment_provider()

    def create_subscription(self, plan_name: str, payment_data: dict) -> 'Subscription':
        # Integration with Midtrans or other payment provider
        external_subscription = self.payment_provider.create_subscription(
            plan_name, payment_data
        )

        subscription = Subscription.objects.create(
            tenant=self.tenant,
            plan_name=plan_name,
            external_subscription_id=external_subscription['id'],
            **external_subscription
        )

        return subscription

    def _get_payment_provider(self):
        # Factory pattern for payment providers
        from services.payment_providers import MidtransProvider
        return MidtransProvider()

# Dependency injection container
class ServiceContainer:
    _services = {}

    @classmethod
    def register(cls, service_class, name=None):
        name = name or service_class.__name__.lower()
        cls._services[name] = service_class

    @classmethod
    def get(cls, service_name: str, tenant: Optional['Tenant'] = None):
        service_class = cls._services.get(service_name)
        if not service_class:
            raise ValueError(f"Service {service_name} not registered")
        return service_class(tenant=tenant)

# Register services
ServiceContainer.register(AssetService, 'asset')
ServiceContainer.register(QRService, 'qr')
ServiceContainer.register(SubscriptionService, 'subscription')
```

### 4. Authentication Enhancement (JWT + RBAC)

```python
# authentication/jwt_auth.py
import jwt
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])

            # Set tenant context from token
            tenant_id = payload.get('tenant_id')
            if tenant_id:
                tenant = Tenant.objects.get(tenant_id=tenant_id)
                request.tenant = tenant

            return (user, None)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')

# authentication/rbac.py
class RBACMixin:
    required_permissions = []

    def check_permissions(self, request):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False

        try:
            tenant_user = TenantUser.objects.get(
                user=request.user,
                tenant=request.tenant
            )

            # Check role-based permissions
            user_permissions = set(tenant_user.permissions.get('permissions', []))
            required_permissions = set(self.required_permissions)

            return required_permissions.issubset(user_permissions)
        except TenantUser.DoesNotExist:
            return False

# Enhanced ViewSets with RBAC
class TenantAssetViewSet(RBACMixin, viewsets.ModelViewSet):
    required_permissions = ['assets.view', 'assets.create', 'assets.edit']

    def get_queryset(self):
        if not self.check_permissions(self.request):
            return Asset.objects.none()

        service = ServiceContainer.get('asset', tenant=self.request.tenant)
        return service.get_tenant_assets()
```

### 5. Migration Strategy (SQLite → PostgreSQL)

```python
# management/commands/migrate_to_postgresql.py
from django.core.management.base import BaseCommand
from django.db import transaction
import sqlite3
import psycopg2

class Command(BaseCommand):
    help = 'Migrate from SQLite to PostgreSQL with tenant setup'

    def add_arguments(self, parser):
        parser.add_argument('--sqlite-db', type=str, required=True)
        parser.add_argument('--tenant-name', type=str, required=True)
        parser.add_argument('--tenant-subdomain', type=str, required=True)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create default tenant for existing installation
            tenant = self._create_default_tenant(
                options['tenant_name'],
                options['tenant_subdomain']
            )

            # Migrate existing assets to new tenant
            self._migrate_assets(options['sqlite_db'], tenant, options['dry_run'])

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully migrated to tenant: {tenant.name}'
                )
            )

    def _create_default_tenant(self, name, subdomain):
        tenant, created = Tenant.objects.get_or_create(
            subdomain=subdomain,
            defaults={
                'name': name,
                'plan_type': 'legacy',
                'max_assets': 9999,
                'max_devices': 9999,
                'storage_quota_gb': 1000
            }
        )
        return tenant

    def _migrate_assets(self, sqlite_db, tenant, dry_run):
        conn = sqlite3.connect(sqlite_db)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets")
        assets = cursor.fetchall()

        for asset_data in assets:
            if not dry_run:
                # Create asset with tenant relationship
                Asset.objects.update_or_create(
                    asset_id=asset_data[0],
                    defaults={
                        'tenant': tenant,
                        'name': asset_data[1],
                        'uri': asset_data[2],
                        # ... other fields
                    }
                )

            self.stdout.write(f"Migrated asset: {asset_data[1]}")

        conn.close()
```

### 6. Plugin Architecture Framework

```python
# plugins/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePlugin(ABC):
    name = ""
    version = ""
    description = ""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]):
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

# plugins/registry.py
class PluginRegistry:
    _plugins = {}

    @classmethod
    def register(cls, plugin_class):
        cls._plugins[plugin_class.name] = plugin_class

    @classmethod
    def get_plugin(cls, name):
        return cls._plugins.get(name)

    @classmethod
    def list_plugins(cls):
        return list(cls._plugins.keys())

# Example payment plugin
class MidtransPaymentPlugin(BasePlugin):
    name = "midtrans_payment"
    version = "1.0.0"
    description = "Midtrans payment integration"

    def initialize(self, config):
        self.server_key = config['server_key']
        self.client_key = config['client_key']
        self.is_production = config.get('is_production', False)

    def execute(self, context):
        # Implement Midtrans payment processing
        payment_data = context['payment_data']
        # ... payment logic
        return {'status': 'success', 'transaction_id': 'xxx'}

# Register plugins
PluginRegistry.register(MidtransPaymentPlugin)
```

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
1. Database schema enhancement
2. Basic multi-tenancy implementation
3. Authentication system upgrade
4. Backwards compatibility layer

### Phase 2: Core SaaS Features (Weeks 5-8)
1. Subscription management
2. QR/Barcode content sharing
3. Enhanced API v3 endpoints
4. Plugin architecture foundation

### Phase 3: Advanced Features (Weeks 9-12)
1. Payment integration (Midtrans)
2. Advanced RBAC
3. Migration tools
4. Comprehensive testing

### Phase 4: Production Ready (Weeks 13-16)
1. Performance optimization
2. Security hardening
3. Documentation
4. Deployment automation

## Backwards Compatibility Guarantee

1. **Existing API Endpoints**: All v1, v1.1, v1.2, and v2 endpoints remain functional
2. **Database Migration**: Transparent migration with zero downtime
3. **Configuration**: Existing settings continue to work
4. **Authentication**: Legacy auth methods supported alongside new JWT
5. **Data Integrity**: All existing assets and configurations preserved

## Security Considerations

1. **Tenant Isolation**: Database-level tenant separation
2. **API Security**: JWT tokens with proper validation
3. **RBAC**: Fine-grained permission system
4. **Data Encryption**: Sensitive data encrypted at rest
5. **Audit Logging**: Comprehensive activity tracking

## Performance Optimizations

1. **Database Indexing**: Optimized indexes for multi-tenant queries
2. **Caching Strategy**: Redis-based caching for frequently accessed data
3. **CDN Integration**: Asset delivery optimization
4. **Background Jobs**: Async processing for heavy operations
5. **Database Connection Pooling**: Efficient connection management

## Monitoring and Observability

1. **Health Checks**: Comprehensive system health monitoring
2. **Metrics Collection**: Key performance indicators tracking
3. **Error Tracking**: Centralized error logging and alerting
4. **User Analytics**: Usage patterns and feature adoption
5. **Performance Monitoring**: Real-time performance metrics

This enhancement strategy ensures a smooth transition from single-tenant to multi-tenant SaaS while maintaining full backwards compatibility and providing a robust foundation for future growth.