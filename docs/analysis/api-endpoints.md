# Anthias API Endpoints Documentation

## Overview
Anthias implements a versioned REST API with comprehensive endpoint coverage for asset management, device control, and system administration. The API follows RESTful conventions with OpenAPI/Swagger documentation.

## API Architecture

### Versioning Strategy
- **v1**: Legacy endpoints (basic functionality)
- **v1.1**: Enhanced asset management
- **v1.2**: Extended device control
- **v2**: Current stable version with full feature set

### Authentication
- Custom `@authorized` decorator
- Session-based authentication
- Basic authentication support
- No OAuth2/JWT (SaaS enhancement needed)

### Documentation
- **drf-spectacular** for OpenAPI generation
- Swagger UI available
- Automated schema generation
- Custom preprocessing hooks

## API v2 Endpoints (Current Stable)

### Asset Management

#### `GET /api/v2/assets`
**Purpose**: List all assets
**Authentication**: Required
**Response**: Array of asset objects
```json
{
  "asset_id": "uuid",
  "name": "string",
  "uri": "string",
  "mimetype": "string",
  "duration": "integer",
  "is_enabled": "boolean",
  "start_date": "datetime",
  "end_date": "datetime",
  "play_order": "integer"
}
```

#### `POST /api/v2/assets`
**Purpose**: Create new asset
**Authentication**: Required
**Request Body**: CreateAssetSerializerV2
```json
{
  "name": "required string",
  "uri": "required string",
  "duration": "optional integer",
  "start_date": "optional datetime",
  "end_date": "optional datetime",
  "mimetype": "optional string"
}
```
**Response**: 201 Created with asset object

#### `GET /api/v2/assets/{asset_id}`
**Purpose**: Retrieve specific asset
**Authentication**: Required
**Parameters**:
- `asset_id` (path): UUID of the asset
**Response**: Asset object

#### `PATCH /api/v2/assets/{asset_id}`
**Purpose**: Partial update of asset
**Authentication**: Required
**Request Body**: UpdateAssetSerializerV2 (partial)
**Response**: Updated asset object

#### `PUT /api/v2/assets/{asset_id}`
**Purpose**: Full update of asset
**Authentication**: Required
**Request Body**: UpdateAssetSerializerV2 (complete)
**Response**: Updated asset object

#### `DELETE /api/v2/assets/{asset_id}`
**Purpose**: Delete asset
**Authentication**: Required
**Response**: 204 No Content

#### `GET /api/v2/assets/{asset_id}/content`
**Purpose**: Retrieve asset content/file
**Authentication**: Required
**Response**: Binary content with appropriate mimetype

### Playlist Management

#### `GET /api/v2/assets/order`
**Purpose**: Get current playlist order
**Authentication**: Required
**Response**: Array of asset IDs in play order
```json
{
  "assets": ["asset_id_1", "asset_id_2", "asset_id_3"]
}
```

#### `POST /api/v2/assets/order`
**Purpose**: Update playlist order
**Authentication**: Required
**Request Body**: Array of asset IDs
**Response**: Success confirmation

### Asset Control

#### `POST /api/v2/assets/control/{command}`
**Purpose**: Control asset playback
**Authentication**: Required
**Commands**:
- `next`: Skip to next asset
- `previous`: Go to previous asset
- `pause`: Pause playback
- `resume`: Resume playback
- `stop`: Stop playback
**Response**: Command execution status

### File Upload

#### `POST /api/v2/file_asset`
**Purpose**: Upload asset file
**Authentication**: Required
**Content-Type**: multipart/form-data
**Request Body**:
```
file: Binary file data
name: Optional asset name
duration: Optional duration override
```
**Response**: Created asset object

### Device Settings

#### `GET /api/v2/device_settings`
**Purpose**: Get device configuration
**Authentication**: Required
**Response**: Device settings object
```json
{
  "player_name": "string",
  "audio_output": "string",
  "default_duration": "integer",
  "default_streaming_duration": "integer",
  "date_format": "string",
  "auth_backend": "string",
  "show_splash": "boolean",
  "default_assets": "boolean",
  "shuffle_playlist": "boolean",
  "use_24_hour_clock": "boolean",
  "debug_logging": "boolean",
  "username": "string"
}
```

#### `PATCH /api/v2/device_settings`
**Purpose**: Update device settings
**Authentication**: Required
**Request Body**: UpdateDeviceSettingsSerializerV2
```json
{
  "player_name": "optional string",
  "default_duration": "optional integer",
  "audio_output": "optional string",
  "auth_backend": "optional string",
  "current_password": "optional string",
  "username": "optional string",
  "password": "optional string",
  "password_2": "optional string"
}
```
**Response**: Success message or validation errors

### System Information

#### `GET /api/v2/info`
**Purpose**: Get system information and status
**Authentication**: Required
**Response**: Comprehensive system info
```json
{
  "viewlog": "string",
  "loadavg": "number",
  "free_space": "string",
  "display_power": "string|null",
  "up_to_date": "boolean",
  "anthias_version": "string",
  "device_model": "string",
  "uptime": {
    "days": "integer",
    "hours": "number"
  },
  "memory": {
    "total": "integer",
    "used": "integer",
    "free": "integer",
    "shared": "integer",
    "buff": "integer",
    "available": "integer"
  },
  "ip_addresses": ["string"],
  "mac_address": "string",
  "host_user": "string"
}
```

### Integrations

#### `GET /api/v2/integrations`
**Purpose**: Get integration platform information
**Authentication**: Required
**Response**: Integration details
```json
{
  "is_balena": "boolean",
  "balena_device_id": "optional string",
  "balena_app_id": "optional string",
  "balena_app_name": "optional string",
  "balena_supervisor_version": "optional string",
  "balena_host_os_version": "optional string",
  "balena_device_name_at_init": "optional string"
}
```

### System Control

#### `POST /api/v2/backup`
**Purpose**: Create system backup
**Authentication**: Required
**Response**: Backup creation status

#### `POST /api/v2/recover`
**Purpose**: Restore from backup
**Authentication**: Required
**Request Body**: Backup file or backup ID
**Response**: Recovery status

#### `POST /api/v2/reboot`
**Purpose**: Reboot device
**Authentication**: Required
**Response**: Reboot initiation confirmation

#### `POST /api/v2/shutdown`
**Purpose**: Shutdown device
**Authentication**: Required
**Response**: Shutdown initiation confirmation

## Legacy API Versions

### API v1 (Legacy)
- Basic asset CRUD operations
- Simple playlist management
- Limited error handling
- **Status**: Deprecated, maintained for compatibility

### API v1.1 (Enhanced)
- Added asset scheduling
- Enhanced error responses
- Basic file upload support
- **Status**: Legacy, limited maintenance

### API v1.2 (Extended)
- Device control endpoints
- System information API
- Improved serialization
- **Status**: Legacy, security updates only

## API Common Patterns

### Error Handling
```json
{
  "error": "Error message",
  "details": {
    "field_name": ["Field-specific error messages"]
  }
}
```

### Status Codes
- `200`: Success
- `201`: Created
- `204`: No Content (for deletions)
- `400`: Bad Request (validation errors)
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

### Custom Headers
```http
Content-Type: application/json
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
```

## SaaS Enhancement Requirements

### 1. Multi-Tenant API Design

#### Tenant Context
- Add organization ID to all endpoints
- Implement tenant-aware filtering
- Add tenant validation middleware

#### Enhanced Endpoints
```
GET /api/v3/organizations/{org_id}/assets
POST /api/v3/organizations/{org_id}/assets
GET /api/v3/organizations/{org_id}/devices
GET /api/v3/organizations/{org_id}/users
```

### 2. Authentication & Authorization

#### JWT/OAuth2 Implementation
```http
Authorization: Bearer {jwt_token}
X-Organization-ID: {org_uuid}
```

#### API Key Authentication
```http
X-API-Key: {api_key}
X-Organization-ID: {org_uuid}
```

#### Role-Based Access Control
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "admin|editor|viewer",
    "permissions": ["create_assets", "delete_assets", "manage_users"],
    "organization": {
      "id": "uuid",
      "name": "Organization Name",
      "plan": "pro"
    }
  }
}
```

### 3. Rate Limiting

#### Implementation Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Retry-After: 60
```

#### Rate Limiting Strategy
- **Free Plan**: 100 requests/hour
- **Pro Plan**: 1000 requests/hour
- **Enterprise**: 10000 requests/hour

### 4. Pagination & Filtering

#### Pagination
```
GET /api/v3/assets?page=1&page_size=20
```

Response:
```json
{
  "count": 100,
  "next": "https://api.example.com/v3/assets?page=2",
  "previous": null,
  "results": [...]
}
```

#### Filtering & Search
```
GET /api/v3/assets?search=video&mimetype=video/*&is_enabled=true
GET /api/v3/assets?created_after=2023-01-01&tags=marketing,promotion
```

### 5. Webhook Support

#### Webhook Endpoints
```json
{
  "webhooks": [
    {
      "id": "uuid",
      "url": "https://client.example.com/webhooks/anthias",
      "events": ["asset.created", "asset.updated", "device.offline"],
      "secret": "webhook_secret"
    }
  ]
}
```

#### Event Types
- `asset.created`
- `asset.updated`
- `asset.deleted`
- `playlist.updated`
- `device.online`
- `device.offline`
- `user.invited`

### 6. API Analytics

#### Usage Metrics
```json
{
  "api_usage": {
    "requests_today": 245,
    "requests_this_month": 8760,
    "most_used_endpoints": [
      {"endpoint": "/api/v3/assets", "count": 150},
      {"endpoint": "/api/v3/devices", "count": 95}
    ],
    "error_rate": 0.02
  }
}
```

## Security Considerations

### Input Validation
- Strict data type validation
- File upload size limits
- Content-type verification
- SQL injection prevention

### Output Sanitization
- XSS prevention
- Sensitive data filtering
- Error message sanitization

### API Security Headers
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

## Performance Optimization

### Caching Strategy
- Redis caching for frequently accessed data
- CDN integration for asset content
- ETag support for conditional requests
- Gzip compression for responses

### Database Optimization
- Proper indexing for API queries
- Query optimization for large datasets
- Connection pooling
- Read replica support

### Monitoring & Logging
- Request/response logging
- Performance metrics collection
- Error tracking and alerting
- API usage analytics

## Testing Strategy

### API Test Coverage
- Unit tests for all endpoints
- Integration tests for workflows
- Load testing for performance
- Security testing for vulnerabilities

### Test Documentation
- Postman collections
- OpenAPI test suites
- Automated regression testing
- Performance benchmarking

## Migration Strategy

### API Version Migration
1. **Phase 1**: Implement v3 with multi-tenancy
2. **Phase 2**: Enhanced authentication
3. **Phase 3**: Advanced features (webhooks, analytics)
4. **Phase 4**: Deprecate v1/v1.1/v1.2

### Backwards Compatibility
- Maintain existing endpoints during transition
- Gradual deprecation with clear timelines
- Migration guides and tools
- Client SDK updates

## Conclusion

The current API architecture provides a solid foundation with good versioning practices and comprehensive functionality. SaaS enhancement requires multi-tenancy implementation, enhanced authentication, and enterprise features while maintaining backwards compatibility.

**Key Priorities:**
1. Multi-tenant API design (v3)
2. JWT/OAuth2 authentication
3. Rate limiting and quotas
4. Webhook system implementation
5. API analytics and monitoring