# API Versioning Strategy and Migration Guide

## Overview

Anthias API implements a comprehensive versioning strategy that ensures backwards compatibility while enabling continuous innovation. This document outlines the versioning approach, migration paths, and best practices for API consumers.

## Versioning Strategy

### Version Numbering

Anthias API follows semantic versioning (SemVer) principles:

- **Major Version (X.0)**: Breaking changes, new architecture
- **Minor Version (X.Y)**: New features, backwards compatible
- **Patch Version (X.Y.Z)**: Bug fixes, security updates

### Current Versions

| Version | Status | Release Date | End of Life | Features |
|---------|--------|--------------|-------------|----------|
| v1.0 | **Deprecated** | 2022-01-01 | 2024-12-31 | Basic asset management |
| v1.1 | **Deprecated** | 2022-06-01 | 2024-12-31 | Enhanced filtering |
| v1.2 | **Maintained** | 2022-12-01 | 2025-06-01 | Improved error handling |
| v2.0 | **Stable** | 2023-06-01 | 2026-01-01 | REST API, authentication |
| **v3.0** | **Current** | 2024-01-01 | TBD | Tenant-aware, multi-tenant |

## Version Negotiation

### Accept Header Versioning (Recommended)

```http
Accept: application/json; version=3.0
```

### URL Path Versioning

```http
GET /api/v3/assets/
GET /api/v2/assets/
```

### Query Parameter Versioning (Fallback)

```http
GET /api/assets/?version=3.0
```

### Version Header

```http
API-Version: 3.0
```

## API v3 Migration Guide

### Breaking Changes from v2 to v3

#### 1. Tenant Context Required

**v2 (Global scope):**
```http
GET /api/v2/assets/
```

**v3 (Tenant-scoped):**
```http
GET /api/v3/assets/
Authorization: Bearer <jwt_with_tenant_context>
```

#### 2. Authentication Changes

**v2:**
- Simple API key or session auth
- Global resource access

**v3:**
- JWT tokens with tenant context required
- Role-based permissions enforced
- Tenant isolation implemented

#### 3. Response Format Changes

**v2 Asset Response:**
```json
{
  "asset_id": "abc123",
  "name": "Asset Name",
  "uri": "https://example.com/asset.mp4",
  "is_enabled": true,
  "is_active": true
}
```

**v3 Asset Response:**
```json
{
  "asset_id": "abc123",
  "name": "Asset Name",
  "uri": "https://example.com/asset.mp4",
  "is_enabled": true,
  "is_active": true,
  "is_shared": false,
  "tenant_info": {
    "id": "tenant-123",
    "name": "Acme Corp"
  },
  "created_by": {
    "id": 1,
    "username": "john.doe"
  },
  "metadata": {...},
  "tags": ["promotion"],
  "usage_stats": {...}
}
```

#### 4. Error Response Format

**v2:**
```json
{
  "error": "Invalid input"
}
```

**v3:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid input provided",
  "details": {
    "field_name": ["This field is required"]
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req-123456"
}
```

### Migration Steps

#### Step 1: Update Authentication

1. **Obtain JWT Tokens**
   ```bash
   # Replace API key authentication
   curl -X POST "https://api.anthias.io/auth/token/" \
     -H "Content-Type: application/json" \
     -d '{"api_key": "your-api-key"}'
   ```

2. **Include Tenant Context**
   ```javascript
   // Update your API client
   const headers = {
     'Authorization': `Bearer ${jwtToken}`,
     'Content-Type': 'application/json'
   };
   ```

#### Step 2: Update Base URLs

```javascript
// Old v2 base URL
const baseURL = 'https://api.anthias.io/v2';

// New v3 base URL
const baseURL = 'https://api.anthias.io/v3';
```

#### Step 3: Handle New Response Fields

```javascript
// v2 asset handling
function processAsset(asset) {
  return {
    id: asset.asset_id,
    name: asset.name,
    enabled: asset.is_enabled
  };
}

// v3 asset handling (backwards compatible)
function processAssetV3(asset) {
  return {
    id: asset.asset_id,
    name: asset.name,
    enabled: asset.is_enabled,
    // New v3 fields
    tenantId: asset.tenant_info?.id,
    createdBy: asset.created_by?.username,
    tags: asset.tags || [],
    isShared: asset.is_shared || false
  };
}
```

#### Step 4: Update Error Handling

```javascript
// v2 error handling
function handleError(error) {
  console.error('API Error:', error.response.data.error);
}

// v3 error handling
function handleErrorV3(error) {
  const errorData = error.response.data;
  console.error('API Error:', {
    code: errorData.error,
    message: errorData.message,
    details: errorData.details,
    requestId: errorData.request_id
  });
}
```

#### Step 5: Implement Permission Checks

```javascript
// v3: Check user permissions before actions
async function canUserCreateAsset() {
  const response = await api.get('/permissions/user/');
  return response.data.permissions.includes('asset.create');
}

// Use permission check before creating assets
if (await canUserCreateAsset()) {
  await createAsset(assetData);
} else {
  showPermissionError();
}
```

### Gradual Migration Strategy

#### Phase 1: Dual API Support (Recommended)

Maintain both v2 and v3 implementations during transition:

```javascript
class AnthiasAPI {
  constructor(version = '3.0') {
    this.version = version;
    this.baseURL = `https://api.anthias.io/v${version.split('.')[0]}`;
  }

  async getAssets() {
    if (this.version.startsWith('3')) {
      return this.getAssetsV3();
    } else {
      return this.getAssetsV2();
    }
  }
}
```

#### Phase 2: Feature Migration

Gradually migrate features to v3:

1. **Week 1-2**: Authentication and basic asset listing
2. **Week 3-4**: Asset creation and updates
3. **Week 5-6**: User management (new v3 feature)
4. **Week 7-8**: Analytics and reporting (new v3 feature)

#### Phase 3: Full Migration

Once all features are validated, switch to v3 exclusively.

### Migration Tools and Utilities

#### API Version Compatibility Checker

```bash
#!/bin/bash
# Check API compatibility
curl -H "Accept: application/json; version=3.0" \
  https://api.anthias.io/v3/version/ | jq '.supported_versions'
```

#### Migration Validation Script

```python
import requests

def validate_migration(base_url, jwt_token):
    """Validate API v3 migration readiness"""
    headers = {'Authorization': f'Bearer {jwt_token}'}

    checks = {
        'health': f'{base_url}/health/',
        'tenant_info': f'{base_url}/tenants/current/',
        'assets': f'{base_url}/assets/',
        'permissions': f'{base_url}/permissions/user/'
    }

    results = {}
    for check_name, url in checks.items():
        try:
            response = requests.get(url, headers=headers)
            results[check_name] = response.status_code == 200
        except Exception as e:
            results[check_name] = False

    return results

# Usage
results = validate_migration('https://api.anthias.io/v3', 'your-jwt-token')
print(f"Migration readiness: {all(results.values())}")
```

## Backwards Compatibility

### Automatic Compatibility Layer

API v3 includes automatic compatibility features:

1. **Field Mapping**: v2 field names automatically mapped to v3
2. **Response Filtering**: Extra v3 fields filtered for v2 clients
3. **Error Translation**: v3 errors converted to v2 format when needed

### Compatibility Headers

```http
# Request v2 compatibility in v3 endpoint
X-API-Compatibility: v2

# Response indicates compatibility mode
X-API-Compatibility-Mode: v2
API-Version: 3.0
```

### Deprecation Warnings

v2 endpoints return deprecation warnings:

```http
Warning: 299 - "API version 2.0 is deprecated. Please upgrade to v3.0."
Sunset: 2026-01-01
Link: <https://docs.anthias.io/migration>; rel="successor-version"
```

## Best Practices for API Consumers

### 1. Version Pinning

Always specify API version explicitly:

```javascript
// Good: Explicit version
const api = new AnthiasAPI('3.0');

// Bad: Implicit version (uses default, may change)
const api = new AnthiasAPI();
```

### 2. Error Handling

Implement robust error handling for version-specific responses:

```javascript
function handleAPIResponse(response) {
  if (response.headers['api-version'] === '3.0') {
    return handleV3Response(response);
  } else {
    return handleLegacyResponse(response);
  }
}
```

### 3. Feature Detection

Check for feature availability before using:

```javascript
async function checkFeatureAvailability() {
  const health = await api.get('/health/');
  return health.data.features;
}

// Use tenant analytics only if available
const features = await checkFeatureAvailability();
if (features.analytics) {
  const analytics = await api.getTenantAnalytics();
}
```

### 4. Graceful Degradation

Implement fallbacks for new features:

```javascript
async function getAssetAnalytics(assetId) {
  try {
    // Try v3 analytics endpoint
    return await api.get(`/assets/${assetId}/analytics/`);
  } catch (error) {
    if (error.status === 404) {
      // Fallback to basic asset info
      return await api.get(`/assets/${assetId}/`);
    }
    throw error;
  }
}
```

## Timeline and Support

### Deprecation Timeline

| Date | Milestone |
|------|-----------|
| 2024-01-01 | v3.0 released, v1.0-1.1 deprecated |
| 2024-06-01 | v1.0-1.1 deprecation warnings added |
| 2024-12-31 | v1.0-1.1 end of life |
| 2025-06-01 | v1.2 deprecation warnings |
| 2026-01-01 | v2.0 deprecation warnings |

### Support Channels

- **Migration Support**: support@anthias.io
- **Developer Documentation**: https://docs.anthias.io/migration
- **Community Forum**: https://community.anthias.io/api-migration
- **GitHub Discussions**: https://github.com/anthias-labs/anthias/discussions

### Migration Assistance

Free migration assistance available for:
- Enterprise customers
- High-volume API users
- Open source projects

Contact support@anthias.io to schedule migration consultation.

## Common Migration Issues

### Issue 1: Tenant Context Missing

**Problem**: 401 Unauthorized errors after migration

**Solution**: Ensure JWT tokens include tenant context
```bash
# Verify token contains tenant claim
echo $JWT_TOKEN | base64 -d | jq '.tenant_id'
```

### Issue 2: Permission Denied Errors

**Problem**: 403 Permission denied for previously accessible resources

**Solution**: Update user roles in tenant context
```bash
# Check user permissions
curl -H "Authorization: Bearer $JWT_TOKEN" \
  https://api.anthias.io/v3/permissions/user/
```

### Issue 3: Rate Limiting

**Problem**: 429 Too Many Requests errors

**Solution**: Implement retry logic with exponential backoff
```javascript
async function apiCallWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fetch(url, options);
    } catch (error) {
      if (error.status === 429 && i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000; // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
}
```

### Issue 4: Response Format Changes

**Problem**: Unexpected response structure

**Solution**: Update response parsing to handle both formats
```javascript
function parseAssetResponse(data) {
  // Handle both v2 and v3 response formats
  return {
    id: data.asset_id,
    name: data.name,
    enabled: data.is_enabled,
    // v3 specific fields (optional)
    tenantId: data.tenant_info?.id,
    metadata: data.metadata || {},
    tags: data.tags || []
  };
}
```

## Testing Your Migration

### Migration Test Checklist

- [ ] Authentication with JWT tokens works
- [ ] All existing API calls return expected data
- [ ] Error handling works with new error format
- [ ] Rate limiting is properly handled
- [ ] New v3 features are accessible (if needed)
- [ ] Fallback logic works for optional features
- [ ] Performance is acceptable with new API

### Testing Tools

#### Postman Collection
Download the official Postman collection for API v3 testing:
```bash
curl -O https://docs.anthias.io/postman/anthias-api-v3.json
```

#### API Testing Script
```bash
#!/bin/bash
# Test API v3 migration
BASE_URL="https://api.anthias.io/v3"
JWT_TOKEN="your-jwt-token"

echo "Testing API v3 endpoints..."

# Test health endpoint
curl -s "$BASE_URL/health/" | jq '.status'

# Test authentication
curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  "$BASE_URL/tenants/current/" | jq '.name'

# Test asset listing
curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  "$BASE_URL/assets/" | jq '.meta.total'

echo "Migration test complete"
```

This comprehensive migration guide should help teams successfully transition from API v2 to v3 while maintaining system stability and taking advantage of new tenant-aware features.