# Tenant Provisioning Guide

## Overview

This guide provides comprehensive instructions for provisioning new tenants in the Anthias SaaS platform, including automated setup, configuration management, and best practices.

## Quick Start

### Single Tenant Creation
```bash
# Basic tenant creation
./manage.py create_tenant "Acme Corp" acme-corp --plan professional

# With owner setup
./manage.py create_tenant "Acme Corp" acme-corp \
    --plan professional \
    --owner-email admin@acme.com \
    --owner-password SecurePass123 \
    --contact-email billing@acme.com

# With custom limits
./manage.py create_tenant "Enterprise Client" enterprise-client \
    --plan enterprise \
    --max-assets 2000 \
    --max-users 200 \
    --storage-quota 500 \
    --custom-domain client.enterprise.com
```

### Bulk Tenant Creation
```bash
# From CSV file
./manage.py bulk_create_tenants tenants.csv

# Dry run first
./manage.py bulk_create_tenants tenants.csv --dry-run
```

## Detailed Provisioning Process

### 1. Pre-Provisioning Checklist

#### Resource Planning
- [ ] Determine subscription plan requirements
- [ ] Calculate resource quotas (assets, users, storage)
- [ ] Plan subdomain and custom domain needs
- [ ] Identify initial user requirements

#### Infrastructure Readiness
- [ ] Database capacity available
- [ ] Storage space allocated
- [ ] Monitoring configured
- [ ] Backup systems ready

#### Security Requirements
- [ ] IP restrictions if needed
- [ ] 2FA requirements
- [ ] Custom security policies
- [ ] Compliance requirements (GDPR, HIPAA, etc.)

### 2. Tenant Creation Steps

#### Step 1: Basic Tenant Setup
```python
from backend.utils.tenant_utils import TenantManager

# Create tenant with default settings
tenant = TenantManager.create_tenant(
    name="Client Organization",
    subdomain="client-org",
    plan_type="professional",
    contact_email="admin@client.com"
)
```

#### Step 2: Configure Limits and Features
```python
# Set custom limits
tenant.max_assets = 1000
tenant.max_users = 50
tenant.max_devices = 25
tenant.storage_quota_gb = 100

# Enable features
tenant.set_feature('analytics_dashboard', True)
tenant.set_feature('api_access', True)
tenant.set_feature('custom_branding', True)

tenant.save()
```

#### Step 3: Setup Initial Users
```python
from backend.utils.tenant_utils import TenantUserManager

# Create tenant owner
owner_user = TenantUserManager.invite_user(
    tenant=tenant,
    email="owner@client.com",
    role="owner",
    permissions={'admin': True}
)

# Add additional administrators
admin_user = TenantUserManager.invite_user(
    tenant=tenant,
    email="admin@client.com",
    role="admin"
)
```

#### Step 4: Database Setup
```bash
# Run tenant-specific migrations
./manage.py migrate_tenant --tenant client-org --setup-rls

# Create initial data structures
./manage.py setup_tenant_data --tenant client-org
```

### 3. Advanced Configuration

#### Custom Domain Setup
```python
# Configure custom domain
tenant.custom_domain = "dashboard.client.com"
tenant.save()

# DNS Configuration Required:
# CNAME: dashboard.client.com → app.yourdomain.com
# SSL Certificate setup for custom domain
```

#### API Access Configuration
```python
from backend.utils.tenant_utils import APIKeyManager

# Generate API key for tenant
api_key, plain_key = APIKeyManager.generate_api_key(
    tenant=tenant,
    name="Primary API Key",
    permissions=['assets.*', 'devices.*'],
    expires_days=365
)

print(f"API Key: {plain_key}")
```

#### Security Policy Setup
```python
# Configure tenant security settings
tenant.enable_2fa = True
tenant.session_timeout_minutes = 240  # 4 hours
tenant.password_policy = {
    'min_length': 12,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_numbers': True,
    'require_symbols': True,
    'password_history': 5
}

# IP restrictions (optional)
tenant.allowed_ip_ranges = [
    "192.168.1.0/24",
    "10.0.0.0/8"
]

tenant.save()
```

## Subscription Plans

### Plan Configurations

#### Basic Plan
```yaml
plan_type: basic
max_assets: 100
max_users: 10
max_devices: 5
storage_quota_gb: 10
features:
  - basic_dashboard
  - standard_support
price_monthly: $29
```

#### Professional Plan
```yaml
plan_type: professional
max_assets: 500
max_users: 50
max_devices: 25
storage_quota_gb: 100
features:
  - advanced_dashboard
  - analytics
  - api_access
  - priority_support
price_monthly: $99
```

#### Enterprise Plan
```yaml
plan_type: enterprise
max_assets: 2000
max_users: 200
max_devices: 100
storage_quota_gb: 500
features:
  - full_dashboard
  - advanced_analytics
  - api_access
  - custom_branding
  - sso_integration
  - dedicated_support
price_monthly: $299
```

### Plan Upgrades
```python
from backend.utils.tenant_utils import TenantQuotaManager

# Upgrade tenant plan
new_limits = {
    'max_assets': 2000,
    'max_users': 200,
    'max_devices': 100,
    'storage_quota_gb': 500
}

TenantQuotaManager.upgrade_tenant_plan(
    tenant=tenant,
    new_plan='enterprise',
    new_limits=new_limits
)
```

## Automation Scripts

### Tenant Provisioning Script
```python
#!/usr/bin/env python
"""
Automated tenant provisioning script
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anthias_django.settings')
django.setup()

from backend.utils.tenant_utils import TenantManager, TenantUserManager

class TenantProvisioner:
    def __init__(self):
        self.created_tenants = []
        self.failed_tenants = []

    def provision_tenant(self, config):
        """Provision a single tenant with full setup"""
        try:
            # Create tenant
            tenant = TenantManager.create_tenant(**config['tenant'])

            # Setup users
            for user_config in config.get('users', []):
                TenantUserManager.invite_user(
                    tenant=tenant,
                    **user_config
                )

            # Apply custom settings
            if 'settings' in config:
                tenant.settings.update(config['settings'])
                tenant.save()

            # Enable features
            for feature, enabled in config.get('features', {}).items():
                tenant.set_feature(feature, enabled)

            self.created_tenants.append(tenant)
            print(f"✓ Created tenant: {tenant.name}")

            return tenant

        except Exception as e:
            self.failed_tenants.append((config['tenant']['name'], str(e)))
            print(f"✗ Failed to create tenant {config['tenant']['name']}: {e}")
            return None

    def provision_from_config(self, config_file):
        """Provision tenants from configuration file"""
        import json

        with open(config_file, 'r') as f:
            configs = json.load(f)

        for config in configs:
            self.provision_tenant(config)

        # Summary
        print(f"\nProvisioning complete:")
        print(f"  Successful: {len(self.created_tenants)}")
        print(f"  Failed: {len(self.failed_tenants)}")

        if self.failed_tenants:
            print("\nFailed tenants:")
            for name, error in self.failed_tenants:
                print(f"  - {name}: {error}")

# Example usage
if __name__ == "__main__":
    provisioner = TenantProvisioner()
    provisioner.provision_from_config('tenant_configs.json')
```

### Configuration File Example
```json
[
  {
    "tenant": {
      "name": "Acme Corporation",
      "subdomain": "acme-corp",
      "plan_type": "professional",
      "contact_email": "billing@acme.com",
      "max_assets": 750,
      "max_users": 40
    },
    "users": [
      {
        "email": "admin@acme.com",
        "role": "owner"
      },
      {
        "email": "manager@acme.com",
        "role": "admin"
      }
    ],
    "features": {
      "analytics_dashboard": true,
      "api_access": true,
      "custom_branding": false
    },
    "settings": {
      "theme": "corporate",
      "timezone": "America/New_York",
      "notifications": {
        "email": true,
        "in_app": true
      }
    }
  }
]
```

## Post-Provisioning Tasks

### 1. Verification Checklist
- [ ] Tenant accessible via subdomain
- [ ] Owner can login successfully
- [ ] Dashboard loads correctly
- [ ] API endpoints respond properly
- [ ] File uploads work within quota
- [ ] User invitation system functional

### 2. Initial Configuration
```python
# Setup default assets or templates
from backend.models.tenant_models import Asset

with tenant_context(tenant):
    # Create welcome asset
    welcome_asset = Asset.objects.create(
        name="Welcome to Anthias",
        uri="welcome-template.html",
        mimetype="text/html",
        is_enabled=True,
        created_by=owner_user.user
    )
```

### 3. Monitoring Setup
```python
# Configure tenant-specific monitoring
from backend.utils.monitoring import setup_tenant_monitoring

setup_tenant_monitoring(tenant, {
    'alerts': {
        'storage_threshold': 0.8,  # 80% of quota
        'user_threshold': 0.9,     # 90% of user limit
        'asset_threshold': 0.9     # 90% of asset limit
    },
    'notification_channels': [
        'email:admin@client.com',
        'slack:tenant-alerts'
    ]
})
```

## Troubleshooting

### Common Issues

#### Subdomain Already Exists
```bash
# Check subdomain availability
./manage.py check_subdomain acme-corp

# Suggest alternatives
./manage.py suggest_subdomains "acme corp"
```

#### Migration Failures
```bash
# Check migration status
./manage.py migrate_tenant --tenant acme-corp --plan

# Force migration with fake-initial
./manage.py migrate_tenant --tenant acme-corp --fake-initial

# Rollback and retry
./manage.py migrate_tenant --tenant acme-corp --backwards
```

#### RLS Policy Issues
```sql
-- Check RLS status
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE tablename IN ('assets', 'devices', 'qr_contents');

-- Recreate policies
DROP POLICY IF EXISTS tenant_policy ON assets;
CREATE POLICY tenant_policy ON assets FOR ALL TO current_user
USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

### Recovery Procedures

#### Tenant Deletion (Emergency)
```python
# Safe tenant deletion with confirmation
from backend.utils.tenant_utils import TenantManager

success = TenantManager.delete_tenant(
    tenant_id="uuid-here",
    confirm_name="Exact Tenant Name"
)
```

#### Data Recovery
```bash
# Restore from backup
./manage.py restore_tenant_backup tenant_backup_20240101.sql

# Partial data recovery
./manage.py recover_tenant_data --tenant acme-corp --table assets
```

## Best Practices

### Development
1. Always test provisioning in staging environment
2. Use configuration files for repeatable setups
3. Implement validation at each step
4. Log all provisioning activities

### Production
1. Monitor provisioning performance
2. Implement rate limiting for bulk operations
3. Use database transactions for atomic operations
4. Maintain audit trails for all tenant operations

### Security
1. Validate all input parameters
2. Use secure password generation
3. Implement proper access controls
4. Regular security audits of tenant isolation

### Performance
1. Batch operations when possible
2. Use parallel processing for bulk provisioning
3. Monitor resource usage during provisioning
4. Implement provisioning queues for high volume

## Integration Examples

### CI/CD Pipeline Integration
```yaml
# .github/workflows/tenant-provisioning.yml
name: Tenant Provisioning
on:
  workflow_dispatch:
    inputs:
      config_file:
        description: 'Tenant configuration file'
        required: true

jobs:
  provision:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Provision tenants
        run: |
          python manage.py provision_from_config ${{ github.event.inputs.config_file }}
```

### API Integration
```python
# REST API endpoint for tenant provisioning
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def provision_tenant(request):
    """API endpoint for tenant provisioning"""
    config = request.data

    try:
        tenant = TenantManager.create_tenant(**config)
        return Response({
            'success': True,
            'tenant_id': str(tenant.tenant_id),
            'subdomain': tenant.subdomain,
            'access_url': f"https://{tenant.subdomain}.yourdomain.com"
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
```

This comprehensive provisioning guide ensures reliable, secure, and scalable tenant creation for the Anthias SaaS platform.