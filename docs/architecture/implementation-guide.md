# Multi-Tenant Architecture Implementation Guide

## Overview

This comprehensive implementation guide provides step-by-step instructions for deploying the multi-tenant architecture in the Anthias SaaS platform.

## Prerequisites

### System Requirements
- **Database**: PostgreSQL 12+ (required for Row-Level Security)
- **Python**: 3.8+
- **Django**: 3.2+
- **Redis**: 6.0+ (for caching and sessions)
- **Memory**: Minimum 4GB RAM for production
- **Storage**: SSD recommended for database performance

### Dependencies
```bash
# Core dependencies
pip install django>=3.2
pip install psycopg2-binary>=2.8
pip install redis>=4.0
pip install django-redis>=5.0

# Optional but recommended
pip install celery>=5.0  # For background tasks
pip install sentry-sdk>=1.0  # For error tracking
```

## Step-by-Step Implementation

### 1. Database Setup

#### PostgreSQL Configuration
```sql
-- Create database
CREATE DATABASE anthias_saas;

-- Create user
CREATE USER anthias_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE anthias_saas TO anthias_user;

-- Enable UUID extension
\c anthias_saas;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set up connection pooling (recommended)
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
```

#### Database Migration
```bash
# Create initial migration for tenant models
python manage.py makemigrations --name initial_tenant_models

# Apply migrations
python manage.py migrate

# Setup RLS policies
python manage.py setup_rls setup --all-tables
```

### 2. Django Settings Configuration

#### Update settings.py
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'backend.models',
    'backend.middleware',
    'backend.utils',
]

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'anthias_saas',
        'USER': 'anthias_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 300,
    }
}

# Import multi-tenant settings
from .settings.multi_tenant import *
```

#### Middleware Configuration
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # Tenant middleware (insert after security)
    'middleware.tenant_middleware.TenantMiddleware',
    'middleware.tenant_middleware.TenantUserMiddleware',
    'middleware.tenant_middleware.TenantSecurityMiddleware',

    # ... rest of middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 3. Model Integration

#### Update existing models
```python
# Replace existing Asset model with tenant-aware version
from backend.models.tenant_models import Asset, Device, QRContent

# Update imports in views and serializers
from backend.models.tenant_models import (
    Tenant, TenantUser, Asset, Device, QRContent, APIKey, AuditLog
)
```

#### Data Migration
```python
# Create migration script for existing data
python manage.py makemigrations --empty anthias_app --name migrate_to_multi_tenant

# Edit the migration file to add tenant_id to existing records
# Run the migration
python manage.py migrate
```

### 4. API Updates

#### Tenant-aware serializers
```python
from rest_framework import serializers
from backend.utils.tenant_utils import get_current_tenant

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ('tenant', 'created_by', 'updated_by')

    def create(self, validated_data):
        # Automatically set tenant from context
        validated_data['tenant'] = get_current_tenant()
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
```

#### View updates
```python
from backend.utils.tenant_utils import require_tenant_permission

class AssetViewSet(viewsets.ModelViewSet):
    serializer_class = AssetSerializer

    def get_queryset(self):
        # Automatically filter by current tenant
        return Asset.objects.for_current_tenant()

    @require_tenant_permission('assets.create')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
```

### 5. Frontend Updates

#### Tenant context in templates
```html
<!-- Base template -->
{% load tenant_tags %}

<!DOCTYPE html>
<html>
<head>
    <title>{% get_current_tenant as tenant %}{{ tenant.name }} - Anthias</title>
    <meta name="tenant-id" content="{{ tenant.tenant_id }}">
</head>
<body>
    <!-- Tenant-specific styling -->
    <style>
        :root {
            --primary-color: {{ tenant.settings.theme.primary_color|default:"#007bff" }};
        }
    </style>
</body>
</html>
```

#### JavaScript API client updates
```javascript
// Add tenant header to all API requests
const apiClient = axios.create({
    baseURL: '/api/v2/',
    headers: {
        'X-Tenant-ID': document.querySelector('meta[name="tenant-id"]').content
    }
});

// Handle tenant-not-found errors
apiClient.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.data?.code === 'TENANT_NOT_FOUND') {
            window.location.href = '/tenant-select/';
        }
        return Promise.reject(error);
    }
);
```

### 6. Tenant Provisioning

#### Create first tenant
```bash
# Create tenant with owner
python manage.py create_tenant \
    "Your Organization" \
    "your-org" \
    --plan professional \
    --owner-email admin@yourorg.com \
    --owner-password SecurePassword123 \
    --contact-email billing@yourorg.com

# Verify tenant creation
python manage.py validate_tenant your-org
```

#### Bulk tenant creation
```bash
# Create tenants from CSV
python manage.py bulk_create_tenants tenants.csv

# CSV format:
# name,subdomain,plan_type,contact_email,max_assets,max_users
# "Acme Corp",acme,professional,admin@acme.com,500,50
# "Beta Inc",beta,basic,admin@beta.com,100,10
```

### 7. DNS and Domain Configuration

#### Subdomain setup
```nginx
# Nginx configuration for subdomains
server {
    listen 80;
    server_name *.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name *.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/wildcard.yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/wildcard.yourdomain.com.key;

    # Proxy to Django
    location / {
        proxy_pass http://django-backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Custom domain support
```nginx
# Custom domain configuration
server {
    listen 443 ssl http2;
    server_name client-domain.com;

    # SSL certificate for custom domain
    ssl_certificate /etc/ssl/certs/client-domain.com.crt;
    ssl_certificate_key /etc/ssl/private/client-domain.com.key;

    # Same proxy configuration
    location / {
        proxy_pass http://django-backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 8. Security Hardening

#### Row-Level Security validation
```bash
# Test RLS policies
python manage.py setup_rls validate

# Test tenant isolation
python manage.py test_tenant_isolation --tenant1 acme --tenant2 beta
```

#### Security headers
```python
# Additional security middleware
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Tenant-specific CSP
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
```

### 9. Monitoring and Logging

#### Setup monitoring
```python
# Sentry configuration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True
)

# Add tenant context to Sentry
def add_tenant_context(event, hint):
    from backend.utils.tenant_utils import get_current_tenant
    tenant = get_current_tenant()
    if tenant:
        event['tags']['tenant_id'] = str(tenant.tenant_id)
        event['tags']['tenant_subdomain'] = tenant.subdomain
    return event

sentry_sdk.add_global_event_processor(add_tenant_context)
```

#### Logging configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'tenant_formatter': {
            'format': '[{asctime}] {levelname} [Tenant: {tenant_id}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'tenant_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/anthias/tenant.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'tenant_formatter',
        },
    },
    'loggers': {
        'tenant': {
            'handlers': ['tenant_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 10. Performance Optimization

#### Database indexing
```sql
-- Add performance indexes
CREATE INDEX CONCURRENTLY idx_assets_tenant_enabled
ON assets (tenant_id, is_enabled) WHERE is_enabled = TRUE;

CREATE INDEX CONCURRENTLY idx_assets_tenant_created
ON assets (tenant_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_tenant_users_active
ON tenant_users (tenant_id, is_active) WHERE is_active = TRUE;

-- Analyze tables
ANALYZE assets;
ANALYZE tenants;
ANALYZE tenant_users;
```

#### Caching strategy
```python
# Redis cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'anthias',
        'TIMEOUT': 300,
    },
    'tenant_cache': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'TIMEOUT': 600,  # 10 minutes for tenant data
        'KEY_PREFIX': 'tenant',
    }
}
```

### 11. Backup and Recovery

#### Automated backups
```bash
#!/bin/bash
# Tenant backup script

BACKUP_DIR="/backups/tenants"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup each tenant
python manage.py list_tenants --active | while read tenant_id subdomain; do
    echo "Backing up tenant: $subdomain"

    # Database backup with RLS context
    pg_dump --dbname=anthias_saas \
            --username=anthias_user \
            --host=localhost \
            --no-password \
            --format=custom \
            --file="$BACKUP_DIR/${subdomain}_${DATE}.dump" \
            --table=assets \
            --table=devices \
            --table=qr_contents \
            --where="tenant_id='$tenant_id'"

    # Compress backup
    gzip "$BACKUP_DIR/${subdomain}_${DATE}.dump"
done

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

#### Recovery procedures
```bash
# Restore tenant from backup
python manage.py restore_tenant_backup \
    --tenant your-org \
    --backup-file /backups/tenants/your-org_20240101_120000.dump.gz \
    --confirm-restore
```

### 12. Testing

#### Unit tests
```python
from django.test import TestCase
from backend.models.tenant_models import Tenant, Asset
from backend.utils.tenant_utils import tenant_context

class TenantIsolationTest(TestCase):
    def setUp(self):
        self.tenant1 = Tenant.objects.create(
            name="Tenant 1",
            subdomain="tenant1"
        )
        self.tenant2 = Tenant.objects.create(
            name="Tenant 2",
            subdomain="tenant2"
        )

    def test_tenant_isolation(self):
        # Create asset in tenant1 context
        with tenant_context(self.tenant1):
            asset1 = Asset.objects.create(name="Asset 1")

        # Create asset in tenant2 context
        with tenant_context(self.tenant2):
            asset2 = Asset.objects.create(name="Asset 2")

            # Should only see tenant2 assets
            visible_assets = Asset.objects.all()
            self.assertEqual(visible_assets.count(), 1)
            self.assertEqual(visible_assets.first().name, "Asset 2")
```

#### Integration tests
```bash
# Run tenant isolation tests
python manage.py test backend.tests.tenant_isolation

# Performance tests
python manage.py test backend.tests.tenant_performance

# API tests
python manage.py test backend.tests.tenant_api
```

### 13. Deployment

#### Production checklist
- [ ] Database backups configured
- [ ] SSL certificates installed
- [ ] DNS records configured
- [ ] Monitoring setup
- [ ] Log rotation configured
- [ ] Security hardening applied
- [ ] Performance optimization completed
- [ ] RLS policies validated

#### Docker deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run migrations and setup RLS
RUN python manage.py migrate
RUN python manage.py setup_rls setup --all-tables

EXPOSE 8000
CMD ["gunicorn", "anthias_django.wsgi:application", "--bind", "0.0.0.0:8000"]
```

#### Environment variables
```bash
# Production environment
export DJANGO_SETTINGS_MODULE=anthias_django.settings.production
export DATABASE_URL=postgresql://user:pass@host:5432/db
export REDIS_URL=redis://localhost:6379/1
export SECRET_KEY=your-secret-key
export ALLOWED_HOSTS=yourdomain.com,*.yourdomain.com
```

## Troubleshooting

### Common Issues

#### Tenant not found errors
```python
# Debug tenant resolution
from backend.middleware.tenant_middleware import TenantMiddleware

middleware = TenantMiddleware(None)
tenant = middleware._resolve_tenant(request)
if not tenant:
    # Check subdomain/domain configuration
    print(f"Host: {request.get_host()}")
    print(f"Path: {request.path}")
```

#### RLS policy issues
```sql
-- Check RLS status
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE tablename IN ('assets', 'devices');

-- Check policies
SELECT * FROM pg_policies WHERE tablename = 'assets';

-- Test policy
SET app.current_tenant_id = 'tenant-uuid-here';
SELECT COUNT(*) FROM assets;  -- Should only show tenant assets
```

#### Performance issues
```sql
-- Check slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE query LIKE '%tenant_id%'
ORDER BY mean_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('assets', 'tenants');
```

This comprehensive implementation guide ensures a successful deployment of the multi-tenant architecture with robust isolation, security, and performance characteristics.