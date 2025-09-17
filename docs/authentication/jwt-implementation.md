# JWT Authentication Implementation Guide

## Overview

This document provides a comprehensive guide to the JWT (JSON Web Token) authentication system implemented for the multi-tenant SaaS application. The system provides secure, scalable authentication with tenant-aware tokens and role-based permissions.

## Architecture

### Core Components

1. **JWT Authentication Backend** (`authentication/jwt_auth.py`)
   - Token generation and validation
   - Encryption of sensitive claims
   - Blacklist management
   - Multi-tenant context support

2. **Token Manager** (`authentication/token_manager.py`)
   - Session lifecycle management
   - Token refresh logic
   - Rate limiting
   - Analytics and monitoring

3. **JWT Middleware** (`middleware/jwt_middleware.py`)
   - Request authentication
   - Tenant context setup
   - Permission validation
   - Security headers

4. **Authentication Serializers** (`serializers/auth_serializers.py`)
   - Request/response validation
   - Data formatting
   - Error handling

5. **Authentication Views** (`views/auth_views.py`)
   - API endpoints
   - Business logic
   - Security enforcement

6. **Token Utilities** (`utils/token_utils.py`)
   - Helper functions
   - Security utilities
   - Debug tools

## Token Structure

### Access Token Claims

```json
{
  \"user_id\": 123,
  \"username\": \"john_doe\",
  \"email_encrypted\": \"gAAAAABh...\",
  \"tenant_id\": 456,
  \"tenant_slug\": \"acme-corp\",
  \"tenant_role\": \"admin\",
  \"tenant_permissions_encrypted\": \"gAAAAABh...\",
  \"token_type\": \"access\",
  \"session_id\": \"abc123...\",
  \"iat\": 1640995200,
  \"exp\": 1640996100,
  \"iss\": \"anthias-saas\",
  \"scope\": \"access\"
}
```

### Refresh Token Claims

```json
{
  \"user_id\": 123,
  \"username\": \"john_doe\",
  \"token_type\": \"refresh\",
  \"session_id\": \"abc123...\",
  \"jti\": \"unique_token_id\",
  \"iat\": 1640995200,
  \"exp\": 1641600000,
  \"iss\": \"anthias-saas\",
  \"scope\": \"refresh\"
}
```

## Security Features

### 1. Token Encryption

Sensitive claims like email and permissions are encrypted using Fernet encryption:

```python
# Sensitive fields are encrypted in JWT payload
sensitive_fields = ['email', 'tenant_permissions']
for field in sensitive_fields:
    if field in claims:
        encrypted_data = cipher_suite.encrypt(
            json.dumps(claims[field]).encode()
        )
        claims[f'{field}_encrypted'] = encrypted_data.decode()
        del claims[field]
```

### 2. Token Blacklisting

Tokens can be blacklisted for immediate revocation:

```python
# Blacklist token with automatic TTL
token_hash = hashlib.sha256(token.encode()).hexdigest()
cache.set(f'blacklisted_token:{token_hash}', True, ttl)
```

### 3. Rate Limiting

Multiple layers of rate limiting:

- Authentication endpoints: 10 requests/minute
- Refresh endpoints: 5 attempts/hour per user
- Brute force protection: IP + username based

### 4. Session Management

Comprehensive session tracking:

```python
session_info = {
    'session_id': session_id,
    'user_id': user.id,
    'tenant_id': tenant.id,
    'device_info': device_info,
    'created_at': timezone.now(),
    'last_activity': timezone.now(),
    'is_active': True
}
```

## Implementation Guide

### 1. Setting Up JWT Backend

```python
# settings.py
JWT_SECRET_KEY = 'your-super-secure-secret-key'
JWT_ENCRYPTION_KEY = 'your-encryption-key'
JWT_ISSUER = 'your-app-name'

# Add to AUTHENTICATION_BACKENDS
AUTHENTICATION_BACKENDS = [
    'authentication.jwt_auth.JWTAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

### 2. Adding Middleware

```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'middleware.jwt_middleware.JWTAuthenticationMiddleware',
    # ... rest of middleware
]
```

### 3. Configuring URLs

```python
# urls.py
from django.urls import path, include
from views.auth_views import (
    LoginAPIView, RefreshTokenAPIView, RegisterAPIView,
    LogoutAPIView, UserProfileAPIView, ChangePasswordAPIView
)

urlpatterns = [
    path('api/auth/login/', LoginAPIView.as_view(), name='login'),
    path('api/auth/refresh/', RefreshTokenAPIView.as_view(), name='refresh'),
    path('api/auth/register/', RegisterAPIView.as_view(), name='register'),
    path('api/auth/logout/', LogoutAPIView.as_view(), name='logout'),
    path('api/auth/profile/', UserProfileAPIView.as_view(), name='profile'),
    path('api/auth/change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
]
```

## API Usage Examples

### 1. User Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"username\": \"john_doe\",
    \"password\": \"secure_password\",
    \"tenant_slug\": \"acme-corp\",
    \"remember_me\": false,
    \"device_info\": {
      \"user_agent\": \"Mozilla/5.0...\",
      \"platform\": \"web\"
    }
  }'
```

Response:
```json
{
  \"success\": true,
  \"message\": \"Login successful.\",
  \"data\": {
    \"access_token\": \"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...\",
    \"refresh_token\": \"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...\",
    \"expires_in\": 900,
    \"token_type\": \"Bearer\",
    \"user\": {
      \"id\": 123,
      \"username\": \"john_doe\",
      \"email\": \"john@example.com\"
    },
    \"tenant\": {
      \"id\": 456,
      \"name\": \"ACME Corp\",
      \"slug\": \"acme-corp\"
    }
  }
}
```

### 2. Token Refresh

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"refresh_token\": \"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...\"
  }'
```

### 3. Authenticated Request

```bash
curl -X GET http://localhost:8000/api/protected-endpoint/ \\
  -H \"Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...\"
```

## View Decorators and Mixins

### 1. JWT Required Decorator

```python
from middleware.jwt_middleware import jwt_required

@jwt_required
def protected_view(request):
    user = request.user  # Authenticated user
    tenant = request.tenant  # Current tenant
    return JsonResponse({'message': 'Success'})
```

### 2. Permission Required Decorator

```python
from middleware.jwt_middleware import permission_required

@permission_required('can_manage_users', tenant_scoped=True)
def admin_view(request):
    # Only users with 'can_manage_users' permission can access
    return JsonResponse({'message': 'Admin access granted'})
```

### 3. Role Required Decorator

```python
from middleware.jwt_middleware import role_required

@role_required('admin')
def admin_only_view(request):
    # Only users with 'admin' role can access
    return JsonResponse({'message': 'Admin only'})
```

### 4. Class-Based View Mixin

```python
from middleware.jwt_middleware import JWTRequiredMixin

class ProtectedAPIView(JWTRequiredMixin, APIView):
    def get(self, request):
        # Automatically requires JWT authentication
        return Response({'user_id': request.user.id})
```

## Error Handling

### Common Error Responses

1. **Invalid Token**
```json
{
  \"error\": \"authentication_failed\",
  \"message\": \"Invalid or expired token\",
  \"timestamp\": \"2024-01-01T12:00:00Z\"
}
```

2. **Rate Limited**
```json
{
  \"error\": \"rate_limit_exceeded\",
  \"message\": \"Too many requests. Please try again later.\",
  \"retry_after\": 3600,
  \"timestamp\": \"2024-01-01T12:00:00Z\"
}
```

3. **Permission Denied**
```json
{
  \"error\": \"permission_denied\",
  \"message\": \"Permission 'can_manage_users' required for this endpoint.\",
  \"timestamp\": \"2024-01-01T12:00:00Z\"
}
```

## Multi-Tenant Integration

### Tenant Context in Tokens

Tokens include tenant information when the user logs in with a tenant context:

```python
# Login with tenant
user, tenant = authenticate_user(username, password, tenant_slug)

# Token includes tenant claims
claims = {
    'tenant_id': tenant.id,
    'tenant_slug': tenant.slug,
    'tenant_role': membership.role,
    'tenant_permissions': list(permissions)
}
```

### Tenant-Aware Middleware

The JWT middleware automatically sets tenant context:

```python
def process_request(self, request):
    # Extract tenant from JWT claims
    tenant_id = claims.get('tenant_id')
    if tenant_id:
        tenant = Tenant.objects.get(id=tenant_id)
        request.tenant = tenant
        request.tenant_role = claims.get('tenant_role')
        request.tenant_permissions = set(claims.get('tenant_permissions', []))
```

## Backwards Compatibility

### Dual Authentication Support

The system supports both JWT and session-based authentication:

```python
# settings.py
AUTHENTICATION_BACKENDS = [
    'authentication.jwt_auth.JWTAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',  # Legacy support
]

# Middleware checks both JWT and session
def process_request(self, request):
    # Skip JWT for excluded paths (including legacy endpoints)
    if self._is_path_excluded(request.path):
        return None

    # Try JWT authentication
    # Fall back to Django's session authentication
```

### Legacy Endpoint Compatibility

Legacy endpoints continue to work with session authentication:

```python
# Excluded paths maintain session-based auth
EXCLUDED_PATHS = [
    '/admin/',           # Django admin
    '/api/legacy/',      # Legacy API endpoints
    '/auth/session/',    # Session-based auth
]
```

## Performance Considerations

### 1. Token Caching

- Blacklisted tokens are cached with automatic TTL
- Session information is cached for quick access
- Rate limiting data is cached to prevent database hits

### 2. Database Optimization

- Minimal database queries during token validation
- Efficient tenant membership queries
- Proper indexing on user-tenant relationships

### 3. Memory Usage

- Encrypted claims reduce token size
- Efficient caching strategies
- Automatic cleanup of expired data

## Monitoring and Analytics

### 1. Security Audit Logging

```python
# Automatic logging of security events
audit_logger.log_authentication_success(user, tenant, session_id)
audit_logger.log_authentication_failure(username, reason)
audit_logger.log_token_refresh(user, session_id)
audit_logger.log_session_revocation(session_id, user_id)
```

### 2. Token Analytics

```python
# Track token usage patterns
def get_session_analytics(user_id, days=30):
    return {
        'total_sessions': session_count,
        'active_sessions': active_count,
        'total_refreshes': refresh_count,
        'average_session_duration': avg_duration
    }
```

## Troubleshooting

### Common Issues

1. **Token Validation Failures**
   - Check JWT_SECRET_KEY configuration
   - Verify token expiry settings
   - Check for blacklisted tokens

2. **Tenant Access Issues**
   - Verify user-tenant membership
   - Check tenant slug in login request
   - Validate tenant permissions

3. **Rate Limiting Issues**
   - Check rate limit configurations
   - Verify cache backend settings
   - Monitor failed authentication attempts

### Debug Tools

```python
from utils.token_utils import TokenDebugUtils

# Debug token structure and claims
debug_info = TokenDebugUtils.decode_token_debug(token)
formatted_info = TokenDebugUtils.format_token_info(debug_info)
print(formatted_info)
```

## Best Practices

### 1. Security

- Use strong, unique JWT_SECRET_KEY
- Enable encryption for sensitive claims
- Implement proper rate limiting
- Monitor authentication patterns
- Regular security audits

### 2. Performance

- Use efficient caching strategies
- Minimize database queries
- Implement proper indexing
- Monitor token refresh patterns

### 3. Scalability

- Use Redis for distributed caching
- Implement horizontal scaling
- Monitor session management
- Plan for multi-region deployment

### 4. Maintenance

- Regular secret key rotation
- Monitor token expiry patterns
- Clean up expired sessions
- Update security configurations

## Configuration Reference

### Required Settings

```python
# JWT Configuration
JWT_SECRET_KEY = 'your-secret-key'
JWT_ENCRYPTION_KEY = 'your-encryption-key'
JWT_ISSUER = 'your-app-name'

# Token Lifetimes
JWT_ACCESS_TOKEN_LIFETIME = 900  # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME = 604800  # 7 days

# Rate Limiting
JWT_RATE_LIMIT_REQUESTS = 100
JWT_RATE_LIMIT_WINDOW = 3600

# Security
JWT_ALGORITHM = 'HS256'
JWT_VERIFY_EXPIRATION = True
JWT_VERIFY_SIGNATURE = True
```

### Optional Settings

```python
# Advanced Configuration
JWT_AUDIENCE = 'your-audience'
JWT_LEEWAY = 60  # Clock skew tolerance
JWT_REQUIRE_EXP = True
JWT_REQUIRE_IAT = True

# Cache Configuration
JWT_CACHE_TIMEOUT = 3600
JWT_BLACKLIST_CACHE_TIMEOUT = 86400

# Logging
JWT_AUDIT_LOGGING = True
JWT_DEBUG_MODE = False
```

This implementation provides a robust, secure, and scalable JWT authentication system that integrates seamlessly with the multi-tenant architecture while maintaining backwards compatibility with existing authentication mechanisms."