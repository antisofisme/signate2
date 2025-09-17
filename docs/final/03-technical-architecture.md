# Technical Architecture - Anthias SaaS Enhancement

## Architecture Overview

The enhanced Signate platform transforms the single-tenant Anthias architecture into a scalable multi-tenant SaaS solution while preserving all existing functionality and ensuring backward compatibility.

## Current vs Target Architecture

### Current Anthias Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Single Tenant System                     │
├─────────────────────────────────────────────────────────────┤
│  Frontend: Basic Web UI (React SPA)                        │
├─────────────────────────────────────────────────────────────┤
│  Backend: Django Monolith                                  │
│  - Single Asset model                                      │
│  - Basic authentication                                    │
│  - SQLite database                                         │
│  - Local file storage                                      │
├─────────────────────────────────────────────────────────────┤
│  Database: SQLite (/data/.screenly/screenly.db)            │
└─────────────────────────────────────────────────────────────┘
```

### Target Enhanced Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Tenant SaaS Platform               │
├─────────────────────────────────────────────────────────────┤
│  Frontend: Next.js 14 PWA                                  │
│  - Modern SaaS UI/UX                                       │
│  - Tenant-aware routing                                    │
│  - Real-time updates                                       │
├─────────────────────────────────────────────────────────────┤
│  API Gateway & Load Balancer                               │
│  - Tenant resolution                                       │
│  - Rate limiting                                           │
│  - SSL termination                                         │
├─────────────────────────────────────────────────────────────┤
│  Backend Services                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Django    │ │   Billing   │ │   File      │          │
│  │   Core API  │ │   Service   │ │   Service   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ PostgreSQL  │ │    Redis    │ │     S3      │          │
│  │Multi-tenant │ │   Cache     │ │   Storage   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Multi-Tenant Database Architecture

#### PostgreSQL Schema Design
```sql
-- Core tenant management
CREATE SCHEMA tenant_management;

CREATE TABLE tenant_management.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    domain VARCHAR(255),
    database_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    settings JSONB DEFAULT '{}',

    -- Resource limits
    max_devices INTEGER DEFAULT 5,
    storage_quota_gb INTEGER DEFAULT 10,
    max_users INTEGER DEFAULT 10,

    -- Feature flags
    features JSONB DEFAULT '[]'
);

-- User-tenant relationships
CREATE TABLE tenant_management.tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant_management.tenants(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, user_id)
);

-- Enhanced assets table with tenant isolation
CREATE TABLE public.assets (
    asset_id VARCHAR(32) PRIMARY KEY,
    tenant_id UUID REFERENCES tenant_management.tenants(id) NOT NULL,

    -- Original Anthias fields (preserved)
    name TEXT,
    uri TEXT,
    md5 TEXT,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    duration BIGINT,
    mimetype TEXT,
    is_enabled BOOLEAN DEFAULT FALSE,
    is_processing BOOLEAN DEFAULT FALSE,
    nocache BOOLEAN DEFAULT FALSE,
    play_order INTEGER DEFAULT 0,
    skip_asset_check BOOLEAN DEFAULT FALSE,

    -- Enhanced SaaS fields
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',

    -- Sharing and collaboration
    is_shared BOOLEAN DEFAULT FALSE,
    share_token UUID,
    share_expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,

    -- Storage and processing
    file_size BIGINT,
    processing_status VARCHAR(20) DEFAULT 'pending',
    thumbnail_url TEXT,

    -- Analytics
    view_count INTEGER DEFAULT 0,
    last_viewed TIMESTAMP
);

-- Row-Level Security for tenant isolation
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON assets
    FOR ALL TO PUBLIC
    USING (
        tenant_id = COALESCE(
            current_setting('app.current_tenant_id', true)::UUID,
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::UUID
        )
    );

-- Indexes for performance
CREATE INDEX idx_assets_tenant_enabled ON assets(tenant_id, is_enabled);
CREATE INDEX idx_assets_tenant_play_order ON assets(tenant_id, play_order);
CREATE INDEX idx_assets_created_at ON assets(created_at);
CREATE INDEX idx_assets_share_token ON assets(share_token);
CREATE INDEX idx_assets_tags ON assets USING GIN(tags);
CREATE INDEX idx_assets_metadata ON assets USING GIN(metadata);
```

#### Tenant Database Routing
```python
# Enhanced database router for multi-tenancy
class TenantDatabaseRouter:
    def __init__(self):
        self.tenant_dbs = {}

    def db_for_read(self, model, **hints):
        if hasattr(model._meta, 'tenant_aware') and model._meta.tenant_aware:
            return self._get_tenant_db()
        return 'default'

    def db_for_write(self, model, **hints):
        if hasattr(model._meta, 'tenant_aware') and model._meta.tenant_aware:
            return self._get_tenant_db()
        return 'default'

    def _get_tenant_db(self):
        # Get current tenant from thread-local storage
        from .middleware import get_current_tenant
        tenant = get_current_tenant()
        return tenant.database_name if tenant else 'default'
```

### 2. Tenant Resolution & Middleware

#### Tenant Middleware Architecture
```python
import threading
from django.db import connection
from django.http import HttpResponseForbidden
from .models import Tenant

# Thread-local storage for tenant context
_tenant_context = threading.local()

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = self.get_tenant_from_request(request)

        if not tenant and self.requires_tenant(request):
            return HttpResponseForbidden("Invalid tenant")

        # Set tenant context
        self.set_tenant_context(tenant)

        # Set database context for RLS
        if tenant:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET app.current_tenant_id = %s",
                    [str(tenant.id)]
                )

        response = self.get_response(request)

        # Clear tenant context
        self.clear_tenant_context()

        return response

    def get_tenant_from_request(self, request):
        # 1. Try subdomain resolution
        host = request.get_host().split(':')[0]
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain != 'www':
                try:
                    return Tenant.objects.get(
                        slug=subdomain,
                        is_active=True
                    )
                except Tenant.DoesNotExist:
                    pass

        # 2. Try custom domain
        try:
            return Tenant.objects.get(
                domain=host,
                is_active=True
            )
        except Tenant.DoesNotExist:
            pass

        # 3. Try header-based tenant (for API clients)
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                return Tenant.objects.get(
                    id=tenant_id,
                    is_active=True
                )
            except Tenant.DoesNotExist:
                pass

        return None

    def requires_tenant(self, request):
        # API v3+ requires tenant context
        return request.path.startswith('/api/v3/')

    def set_tenant_context(self, tenant):
        _tenant_context.tenant = tenant
        request.tenant = tenant

    def clear_tenant_context(self):
        if hasattr(_tenant_context, 'tenant'):
            delattr(_tenant_context, 'tenant')

def get_current_tenant():
    return getattr(_tenant_context, 'tenant', None)
```

### 3. Enhanced Authentication & Authorization

#### JWT Authentication System
```python
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )

            user = User.objects.get(id=payload['user_id'])

            # Validate tenant access
            if request.tenant:
                self.validate_tenant_access(user, request.tenant)

            return (user, token)

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')

    def validate_tenant_access(self, user, tenant):
        if not TenantUser.objects.filter(
            user=user,
            tenant=tenant,
            is_active=True
        ).exists():
            raise AuthenticationFailed('No access to this tenant')

class TokenService:
    @staticmethod
    def generate_tokens(user, tenant=None):
        now = datetime.utcnow()

        # Access token (15 minutes)
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'tenant_id': str(tenant.id) if tenant else None,
            'iat': now,
            'exp': now + timedelta(minutes=15),
            'type': 'access'
        }

        # Refresh token (7 days)
        refresh_payload = {
            'user_id': user.id,
            'iat': now,
            'exp': now + timedelta(days=7),
            'type': 'refresh'
        }

        return {
            'access_token': jwt.encode(
                access_payload,
                settings.JWT_SECRET_KEY,
                algorithm='HS256'
            ),
            'refresh_token': jwt.encode(
                refresh_payload,
                settings.JWT_SECRET_KEY,
                algorithm='HS256'
            ),
            'expires_in': 900  # 15 minutes
        }
```

#### RBAC Permission System
```python
class Permission:
    # Asset permissions
    ASSETS_VIEW = 'assets.view'
    ASSETS_CREATE = 'assets.create'
    ASSETS_EDIT = 'assets.edit'
    ASSETS_DELETE = 'assets.delete'
    ASSETS_SHARE = 'assets.share'

    # Layout permissions
    LAYOUTS_VIEW = 'layouts.view'
    LAYOUTS_CREATE = 'layouts.create'
    LAYOUTS_EDIT = 'layouts.edit'
    LAYOUTS_DELETE = 'layouts.delete'

    # User management permissions
    USERS_VIEW = 'users.view'
    USERS_INVITE = 'users.invite'
    USERS_MANAGE = 'users.manage'

    # Tenant administration
    TENANT_SETTINGS = 'tenant.settings'
    TENANT_BILLING = 'tenant.billing'
    TENANT_ANALYTICS = 'tenant.analytics'

class Role:
    TENANT_ADMIN = 'tenant_admin'
    CONTENT_MANAGER = 'content_manager'
    DEVICE_OPERATOR = 'device_operator'
    VIEWER = 'viewer'

    PERMISSIONS = {
        TENANT_ADMIN: ['*'],  # All permissions
        CONTENT_MANAGER: [
            Permission.ASSETS_VIEW,
            Permission.ASSETS_CREATE,
            Permission.ASSETS_EDIT,
            Permission.ASSETS_DELETE,
            Permission.ASSETS_SHARE,
            Permission.LAYOUTS_VIEW,
            Permission.LAYOUTS_CREATE,
            Permission.LAYOUTS_EDIT,
            Permission.LAYOUTS_DELETE,
        ],
        DEVICE_OPERATOR: [
            Permission.ASSETS_VIEW,
            Permission.LAYOUTS_VIEW,
        ],
        VIEWER: [
            Permission.ASSETS_VIEW,
            Permission.LAYOUTS_VIEW,
        ]
    }

class RBACMixin:
    required_permissions = []

    def check_permissions(self, request):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False

        if not hasattr(request, 'tenant') or not request.tenant:
            return False

        try:
            tenant_user = TenantUser.objects.get(
                user=request.user,
                tenant=request.tenant,
                is_active=True
            )

            # Check if user has required permissions
            user_permissions = self.get_user_permissions(tenant_user)
            required_permissions = set(self.required_permissions)

            # Admin role has all permissions
            if '*' in user_permissions:
                return True

            return required_permissions.issubset(user_permissions)

        except TenantUser.DoesNotExist:
            return False

    def get_user_permissions(self, tenant_user):
        role_permissions = set(Role.PERMISSIONS.get(tenant_user.role, []))
        custom_permissions = set(tenant_user.permissions)
        return role_permissions.union(custom_permissions)
```

### 4. API Architecture & Versioning

#### API Versioning Strategy
```python
# URL structure for API versioning
/api/v1/        # Legacy Anthias API (preserved)
/api/v1.1/      # Legacy Anthias API (preserved)
/api/v1.2/      # Legacy Anthias API (preserved)
/api/v2/        # Current Anthias API (preserved)
/api/v3/        # New multi-tenant API

# v3 API structure
/api/v3/auth/                    # Authentication endpoints
/api/v3/tenants/current/         # Current tenant information
/api/v3/assets/                  # Tenant-scoped asset management
/api/v3/layouts/                 # Layout management
/api/v3/users/                   # User management
/api/v3/billing/                 # Billing and subscriptions
/api/v3/analytics/               # Analytics and reporting
/api/v3/sharing/                 # Content sharing
```

#### Enhanced API Endpoints
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class TenantAssetViewSet(RBACMixin, viewsets.ModelViewSet):
    required_permissions = [Permission.ASSETS_VIEW]
    serializer_class = AssetSerializer
    filterset_fields = ['mimetype', 'is_enabled', 'tags']
    search_fields = ['name', 'metadata']
    ordering_fields = ['created_at', 'play_order', 'name']

    def get_queryset(self):
        if not self.check_permissions(self.request):
            return Asset.objects.none()

        return Asset.objects.filter(
            tenant_id=self.request.tenant.id
        ).select_related('created_by')

    def perform_create(self, serializer):
        serializer.save(
            tenant_id=self.request.tenant.id,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'],
            required_permissions=[Permission.ASSETS_SHARE])
    def share(self, request, pk=None):
        asset = self.get_object()
        share_token = uuid.uuid4()
        expires_at = timezone.now() + timedelta(days=30)

        asset.is_shared = True
        asset.share_token = share_token
        asset.share_expires_at = expires_at
        asset.save()

        share_url = f"https://{request.get_host()}/share/{share_token}"

        return Response({
            'share_url': share_url,
            'share_token': str(share_token),
            'expires_at': expires_at
        })

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        original_asset = self.get_object()

        # Create duplicate with new asset_id
        duplicate_asset = Asset.objects.create(
            tenant_id=self.request.tenant.id,
            name=f"{original_asset.name} (Copy)",
            uri=original_asset.uri,
            mimetype=original_asset.mimetype,
            duration=original_asset.duration,
            metadata=original_asset.metadata.copy(),
            tags=original_asset.tags.copy(),
            created_by=request.user
        )

        serializer = self.get_serializer(duplicate_asset)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

### 5. Frontend Architecture (Next.js 14)

#### Application Structure
```typescript
// app/ directory structure (App Router)
app/
  globals.css
  layout.tsx

  (auth)/                    # Auth group
    login/page.tsx
    register/page.tsx
    forgot-password/page.tsx
    layout.tsx

  (dashboard)/               # Dashboard group
    [tenant]/                # Dynamic tenant route
      layout.tsx             # Tenant-aware layout
      page.tsx               # Dashboard home

      assets/                # Asset management
        page.tsx             # Asset list
        [id]/                # Asset details
          page.tsx
          edit/page.tsx
        upload/page.tsx

      layouts/               # Layout management
        page.tsx
        designer/page.tsx    # Drag-drop designer
        [id]/page.tsx

      users/                 # User management
        page.tsx
        invite/page.tsx

      billing/               # Billing management
        page.tsx
        subscription/page.tsx
        invoices/page.tsx

      settings/              # Tenant settings
        page.tsx
        integrations/page.tsx

  api/                       # API routes (Next.js)
    auth/
      route.ts
    upload/
      route.ts

  share/                     # Public sharing routes
    [token]/page.tsx

// components/ directory
components/
  ui/                        # shadcn/ui components
    button.tsx
    input.tsx
    dialog.tsx
    ...

  auth/                      # Authentication components
    LoginForm.tsx
    AuthProvider.tsx
    ProtectedRoute.tsx

  dashboard/                 # Dashboard components
    Sidebar.tsx
    TopBar.tsx
    TenantSwitcher.tsx
    QuickActions.tsx

  assets/                    # Asset management
    AssetGrid.tsx
    AssetCard.tsx
    AssetUpload.tsx
    AssetPreview.tsx

  layouts/                   # Layout designer
    LayoutDesigner.tsx
    GridSystem.tsx
    AssetPalette.tsx
    PropertyPanel.tsx

  billing/                   # Billing components
    SubscriptionCard.tsx
    UsageChart.tsx
    InvoiceList.tsx
```

#### Tenant-Aware Routing
```typescript
// middleware.ts - Tenant resolution
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host')
  const url = request.nextUrl.clone()

  // Extract subdomain
  const subdomain = hostname?.split('.')[0]

  if (subdomain && subdomain !== 'www' && subdomain !== 'app') {
    // Rewrite to tenant-specific route
    url.pathname = `/${subdomain}${url.pathname}`
    return NextResponse.rewrite(url)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)']
}

// app/[tenant]/layout.tsx - Tenant layout
interface TenantLayoutProps {
  children: React.ReactNode
  params: { tenant: string }
}

export default async function TenantLayout({
  children,
  params
}: TenantLayoutProps) {
  const tenant = await getTenantBySlug(params.tenant)

  if (!tenant) {
    notFound()
  }

  return (
    <TenantProvider tenant={tenant}>
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <TopBar />
          {children}
        </main>
      </div>
    </TenantProvider>
  )
}
```

### 6. Caching & Performance Architecture

#### Redis Caching Strategy
```python
# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Tenant-aware caching
class TenantCache:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.cache = cache

    def get_key(self, key):
        return f"tenant:{self.tenant_id}:{key}"

    def get(self, key, default=None):
        return self.cache.get(self.get_key(key), default)

    def set(self, key, value, timeout=300):
        return self.cache.set(self.get_key(key), value, timeout)

    def delete(self, key):
        return self.cache.delete(self.get_key(key))

# Asset caching decorator
def cache_asset_data(timeout=300):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if hasattr(self.request, 'tenant'):
                cache_key = f"assets:{self.request.tenant.id}:{func.__name__}"
                cached_result = cache.get(cache_key)
                if cached_result:
                    return cached_result

                result = func(self, *args, **kwargs)
                cache.set(cache_key, result, timeout)
                return result

            return func(self, *args, **kwargs)
        return wrapper
    return decorator
```

### 7. File Storage & CDN Integration

#### S3-Compatible Storage Architecture
```python
# Storage backends configuration
if settings.USE_S3_STORAGE:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.StaticS3Boto3Storage'

    AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
    AWS_S3_REGION_NAME = settings.AWS_S3_REGION_NAME
    AWS_S3_CUSTOM_DOMAIN = settings.AWS_S3_CUSTOM_DOMAIN

    # Tenant-specific storage paths
    AWS_LOCATION = 'media'

class TenantFileStorage:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.storage = default_storage

    def save(self, name, content):
        # Save files in tenant-specific directories
        tenant_path = f"tenants/{self.tenant_id}/{name}"
        return self.storage.save(tenant_path, content)

    def url(self, name):
        return self.storage.url(name)

    def delete(self, name):
        return self.storage.delete(name)

    def get_tenant_usage(self):
        # Calculate storage usage for tenant
        total_size = 0
        for asset in Asset.objects.filter(tenant_id=self.tenant_id):
            if asset.file_size:
                total_size += asset.file_size
        return total_size
```

### 8. Background Job Processing

#### Celery Task Architecture
```python
# tasks.py - Background processing
from celery import shared_task
from django.core.files.storage import default_storage
import ffmpeg

@shared_task
def process_video_asset(asset_id):
    try:
        asset = Asset.objects.get(asset_id=asset_id)
        asset.processing_status = 'processing'
        asset.save()

        # Generate thumbnail
        thumbnail_path = generate_video_thumbnail(asset.uri)
        asset.thumbnail_url = thumbnail_path

        # Extract metadata
        metadata = extract_video_metadata(asset.uri)
        asset.metadata.update(metadata)

        asset.processing_status = 'completed'
        asset.save()

        # Invalidate cache
        cache.delete(f"asset:{asset.tenant_id}:{asset_id}")

    except Exception as e:
        asset.processing_status = 'failed'
        asset.save()
        raise

@shared_task
def generate_usage_report(tenant_id, period='monthly'):
    tenant = Tenant.objects.get(id=tenant_id)

    # Calculate usage metrics
    asset_count = Asset.objects.filter(tenant_id=tenant_id).count()
    storage_usage = TenantFileStorage(tenant_id).get_tenant_usage()
    api_calls = get_api_usage_for_period(tenant_id, period)

    # Generate report
    report = {
        'tenant_id': tenant_id,
        'period': period,
        'metrics': {
            'asset_count': asset_count,
            'storage_usage_gb': storage_usage / (1024**3),
            'api_calls': api_calls,
            'active_devices': get_active_device_count(tenant_id)
        }
    }

    # Store report for billing
    UsageReport.objects.create(
        tenant_id=tenant_id,
        period=period,
        data=report
    )

    return report
```

## Security Architecture

### Data Protection & Encryption
```python
# Encryption at rest
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'sslmode': 'require',
            'options': '-c default_transaction_isolation=serializable'
        }
    }
}

# Field-level encryption for sensitive data
from django_cryptography.fields import encrypt

class TenantSecrets(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE)
    api_keys = encrypt(models.JSONField(default=dict))
    webhook_secrets = encrypt(models.JSONField(default=dict))
    payment_credentials = encrypt(models.JSONField(default=dict))
```

### Input Validation & Sanitization
```python
# API input validation
class AssetSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=255,
        validators=[validate_safe_string]
    )
    metadata = serializers.JSONField(
        validators=[validate_metadata_structure]
    )

    def validate_uri(self, value):
        # Validate file URLs and prevent SSRF
        if not is_safe_url(value):
            raise serializers.ValidationError("Invalid URL")
        return value

def validate_safe_string(value):
    # Prevent XSS and injection attacks
    if has_malicious_content(value):
        raise ValidationError("Invalid content detected")
    return value
```

## Monitoring & Observability

### Application Monitoring
```python
# Health check endpoints
@api_view(['GET'])
def health_check(request):
    checks = {
        'database': check_database_connection(),
        'redis': check_redis_connection(),
        'storage': check_storage_access(),
        'external_services': check_external_services()
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return Response({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': timezone.now().isoformat()
    }, status=status_code)

# Performance monitoring
import time
from django.utils.deprecation import MiddlewareMixin

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            # Log slow requests
            if duration > 1.0:  # 1 second threshold
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s"
                )

            # Add performance headers
            response['X-Response-Time'] = f"{duration:.3f}s"

        return response
```

This technical architecture provides a robust foundation for transforming Anthias into a scalable, secure, and performant multi-tenant SaaS platform while maintaining full backward compatibility and preserving all existing functionality.