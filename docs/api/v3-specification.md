# Anthias API v3 Specification

## Overview

Anthias API v3 introduces tenant-aware endpoints with advanced features including role-based access control, asset sharing across tenants, comprehensive analytics, and intelligent rate limiting. This version maintains full backwards compatibility while providing enhanced functionality for multi-tenant environments.

## Key Features

### 🏢 Tenant Isolation
- Complete data isolation between tenants
- Automatic tenant context resolution from JWT tokens
- Tenant-scoped resource filtering and access control

### 🔐 Advanced Authentication & Authorization
- JWT-based authentication with tenant context
- Role-based permission system (Owner, Admin, Manager, Editor, Viewer, Guest)
- Resource-level permission checking
- Cross-tenant sharing with permission validation

### 🚀 Enhanced Performance
- Tenant-aware rate limiting and quotas
- Adaptive throttling based on system load
- Burst handling with token bucket algorithm
- Optimized database queries with tenant filtering

### 📊 Analytics & Monitoring
- Real-time usage analytics per tenant
- API call tracking and quota monitoring
- Asset usage statistics and insights
- Performance metrics and health monitoring

### 🔄 Versioning & Migration
- Seamless backwards compatibility with v1/v2
- API version negotiation via headers
- Gradual migration path for existing clients
- Deprecation warnings for legacy endpoints

## Base URL

```
Production: https://api.anthias.io/v3
Development: http://localhost:8000/api/v3
```

## Authentication

### JWT Authentication
Include JWT token in Authorization header:
```http
Authorization: Bearer <jwt_token>
```

### API Key Authentication (Alternative)
```http
Authorization: ApiKey <api_key>
```

The JWT token must include tenant context for proper resource scoping.

## API Endpoints

### Health & Version

#### GET /health/
Check API health status
```json
{
  "status": "healthy",
  "version": "3.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "features": {
    "tenant_isolation": true,
    "asset_sharing": true,
    "advanced_permissions": true,
    "rate_limiting": true,
    "analytics": true
  }
}
```

#### GET /version/
Get API version information
```json
{
  "current_version": "3.0",
  "supported_versions": ["1.0", "1.1", "1.2", "2.0", "3.0"],
  "deprecated_versions": ["1.0", "1.1"],
  "sunset_date": "2024-12-31"
}
```

### Tenant Management

#### GET /tenants/current/
Get current tenant information
```json
{
  "id": "tenant-123",
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "subscription_tier": "pro",
  "created_at": "2024-01-01T00:00:00Z",
  "settings": {
    "timezone": "UTC",
    "date_format": "YYYY-MM-DD"
  },
  "user_count": 25,
  "asset_count": 150,
  "quota_usage": {
    "api_calls_this_month": 8500,
    "storage_used_mb": 2048,
    "users_count": 25,
    "assets_count": 150
  }
}
```

#### PATCH /tenants/current/
Update tenant settings (Admin only)

### Asset Management

#### GET /assets/
List tenant assets with filtering and pagination

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `status`: Filter by status (`active`, `inactive`)
- `mimetype`: Filter by MIME type
- `tags`: Filter by tags (comma-separated)
- `search`: Search in name and URI
- `ordering`: Sort by field (`name`, `created_at`, `start_date`, `play_order`)

**Response:**
```json
{
  "data": [
    {
      "asset_id": "asset-abc123",
      "name": "Holiday Promotion",
      "uri": "https://storage.example.com/holiday.mp4",
      "md5": "d41d8cd98f00b204e9800998ecf8427e",
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z",
      "duration": 30000,
      "mimetype": "video/mp4",
      "is_enabled": true,
      "is_processing": false,
      "is_active": true,
      "is_shared": false,
      "metadata": {
        "resolution": "1920x1080",
        "fps": 30
      },
      "tags": ["promotion", "holiday"],
      "created_by": {
        "id": 1,
        "username": "john.doe",
        "full_name": "John Doe"
      },
      "tenant_info": {
        "id": "tenant-123",
        "name": "Acme Corporation",
        "slug": "acme-corp"
      },
      "usage_stats": {
        "play_count": 45,
        "total_play_time": 1350000,
        "last_played": "2024-01-15T14:30:00Z"
      }
    }
  ],
  "meta": {
    "page": 1,
    "pages": 5,
    "per_page": 20,
    "total": 95,
    "has_next": true,
    "has_prev": false
  }
}
```

#### POST /assets/
Create new asset

**Request Body:**
```json
{
  "name": "New Asset",
  "uri": "https://example.com/asset.mp4",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z",
  "duration": 30000,
  "is_enabled": true,
  "metadata": {
    "description": "Asset description"
  },
  "tags": ["tag1", "tag2"]
}
```

#### GET /assets/{asset_id}/
Get asset details

#### PUT/PATCH /assets/{asset_id}/
Update asset

#### DELETE /assets/{asset_id}/
Delete asset

#### POST /assets/{asset_id}/share/
Share asset with other tenants

**Request Body:**
```json
{
  "target_tenant_ids": ["tenant-456", "tenant-789"],
  "permission_level": "view",
  "message": "Sharing this asset for collaboration",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

#### DELETE /assets/{asset_id}/unshare/
Remove asset sharing

#### GET /assets/{asset_id}/analytics/
Get asset usage analytics

#### POST /assets/{asset_id}/duplicate/
Create a copy of the asset

### User Management

#### GET /users/
List tenant users

#### GET /users/{user_id}/
Get user details

#### POST /users/invite/
Invite user to tenant

**Request Body:**
```json
{
  "email": "new.user@example.com",
  "role": "viewer",
  "message": "Welcome to our team!",
  "expires_in_days": 7
}
```

#### PATCH /users/{user_id}/role/
Update user role

**Request Body:**
```json
{
  "role": "editor"
}
```

#### DELETE /users/{user_id}/remove/
Remove user from tenant

### Analytics

#### POST /tenants/current/analytics/
Get tenant analytics with filters

**Request Body:**
```json
{
  "period": "month",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "metrics": ["api_calls", "asset_views", "user_activity"]
}
```

**Response:**
```json
{
  "tenant_id": "tenant-123",
  "period": "month",
  "metrics": {
    "api_calls": {
      "total": 8500,
      "by_endpoint": {
        "/assets/": 3200,
        "/users/": 800,
        "/analytics/": 150
      },
      "by_day": [...]
    },
    "asset_views": {
      "total": 12500,
      "by_asset": {...},
      "by_day": [...]
    },
    "user_activity": {
      "active_users": 18,
      "new_users": 3,
      "login_frequency": {...}
    }
  },
  "quota_status": {
    "api_calls_used": 8500,
    "api_calls_limit": 10000,
    "storage_used_mb": 2048,
    "storage_limit_mb": 5000
  }
}
```

### Permissions

#### GET /permissions/
List all available permissions

#### GET /permissions/user/
Get current user's permissions in tenant context

## Rate Limiting

API v3 implements sophisticated rate limiting based on tenant tiers:

### Rate Limits by Tenant Tier

| Tier | API Calls/Hour | Asset Operations/Hour | User Operations/Hour | Monthly Quota |
|------|----------------|----------------------|---------------------|---------------|
| Free | 1,000 | 100 | 50 | 10,000 |
| Pro | 5,000 | 1,000 | 200 | 100,000 |
| Enterprise | 20,000 | 5,000 | 1,000 | 1,000,000 |
| Admin | 50,000 | 10,000 | 2,000 | Unlimited |

### Throttling Headers

All responses include throttling headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Tier: pro
```

### Adaptive Throttling

The system automatically adjusts rate limits based on:
- System load (CPU and memory usage)
- Tenant usage patterns
- Time of day and historical traffic

## Error Handling

### Error Response Format
```json
{
  "error": "VALIDATION_ERROR",
  "message": "The provided data is invalid",
  "details": {
    "field_name": ["This field is required"]
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req-123456"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| VALIDATION_ERROR | 400 | Request data validation failed |
| UNAUTHORIZED | 401 | Authentication required |
| PERMISSION_DENIED | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMITED | 429 | Rate limit exceeded |
| QUOTA_EXCEEDED | 429 | Monthly quota exceeded |
| SERVER_ERROR | 500 | Internal server error |

## Permissions System

### Role Hierarchy

1. **Owner** - Full access to all tenant resources
2. **Admin** - Manage tenant, users, assets, layouts, settings
3. **Manager** - Manage assets, layouts, invite users
4. **Editor** - Create/edit assets and layouts
5. **Viewer** - View assets and layouts
6. **Guest** - Limited read-only access

### Permission Format

Permissions follow the format: `resource.action`

Examples:
- `asset.view` - View assets
- `asset.create` - Create new assets
- `asset.manage` - Full asset management
- `user.invite` - Invite users to tenant
- `tenant.manage` - Manage tenant settings

## Pagination

All list endpoints support pagination:

### Query Parameters
- `page`: Page number (1-based)
- `per_page`: Items per page (max 100)

### Response Metadata
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "pages": 10,
    "per_page": 20,
    "total": 200,
    "has_next": true,
    "has_prev": false
  }
}
```

## Filtering and Search

### Common Filter Parameters
- `search`: Text search across relevant fields
- `ordering`: Sort by field (prefix with `-` for descending)
- `is_enabled`: Filter by enabled status
- `created_at__gte`: Filter by creation date (greater than or equal)
- `created_at__lte`: Filter by creation date (less than or equal)

### Asset-Specific Filters
- `mimetype`: Filter by MIME type
- `tags`: Filter by tags (comma-separated)
- `status`: Filter by status (`active`, `inactive`)
- `is_shared`: Filter by sharing status

## Webhooks (Future Enhancement)

API v3 is designed to support webhooks for real-time notifications:

### Planned Webhook Events
- `asset.created`
- `asset.updated`
- `asset.deleted`
- `asset.shared`
- `user.invited`
- `user.joined`
- `tenant.quota_warning`

## SDK and Examples

### cURL Examples

#### Create Asset
```bash
curl -X POST "https://api.anthias.io/v3/assets/" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Asset",
    "uri": "https://example.com/video.mp4",
    "is_enabled": true
  }'
```

#### Get Tenant Analytics
```bash
curl -X POST "https://api.anthias.io/v3/tenants/current/analytics/" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "period": "week",
    "metrics": ["api_calls", "asset_views"]
  }'
```

### Python SDK Example
```python
import requests

class AnthiasAPIv3:
    def __init__(self, jwt_token, base_url="https://api.anthias.io/v3"):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        })
        self.base_url = base_url

    def create_asset(self, name, uri, **kwargs):
        data = {"name": name, "uri": uri, **kwargs}
        return self.session.post(f"{self.base_url}/assets/", json=data)

    def get_tenant_info(self):
        return self.session.get(f"{self.base_url}/tenants/current/")

# Usage
api = AnthiasAPIv3("your-jwt-token")
response = api.create_asset("Test Asset", "https://example.com/test.mp4")
```

## Migration from v2 to v3

See [API Migration Guide](./versioning-strategy.md) for detailed migration instructions.

## Support

- **Documentation**: https://docs.anthias.io/api/v3
- **GitHub Issues**: https://github.com/anthias-labs/anthias/issues
- **Community**: https://community.anthias.io