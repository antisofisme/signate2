# JWT + RBAC Authentication Enhancement
# Complete authentication system with JWT tokens and Role-Based Access Control

import jwt
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from django.core.cache import cache
import hashlib


# JWT Token Management
class JWTTokenManager:
    """Manages JWT token creation, validation, and refresh"""

    @staticmethod
    def generate_tokens(user: User, tenant: Optional['Tenant'] = None) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        now = timezone.now()

        # Access token payload
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'tenant_id': str(tenant.tenant_id) if tenant else None,
            'exp': now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME),
            'iat': now,
            'type': 'access'
        }

        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'tenant_id': str(tenant.tenant_id) if tenant else None,
            'exp': now + timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME),
            'iat': now,
            'type': 'refresh'
        }

        access_token = jwt.encode(
            access_payload,
            settings.JWT_SECRET_KEY,
            algorithm='HS256'
        )

        refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_SECRET_KEY,
            algorithm='HS256'
        )

        # Store refresh token in cache for validation
        cache_key = f"refresh_token_{user.id}_{tenant.tenant_id if tenant else 'none'}"
        cache.set(cache_key, refresh_token, timeout=settings.JWT_REFRESH_TOKEN_LIFETIME * 24 * 3600)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': settings.JWT_ACCESS_TOKEN_LIFETIME * 60
        }

    @staticmethod
    def validate_token(token: str) -> Dict[str, Any]:
        """Validate JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )

            # Check if token is blacklisted
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if cache.get(f"blacklisted_token_{token_hash}"):
                raise AuthenticationFailed('Token has been revoked')

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, str]:
        """Generate new access token using refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )

            if payload.get('type') != 'refresh':
                raise AuthenticationFailed('Invalid token type')

            # Validate refresh token is not revoked
            user_id = payload['user_id']
            tenant_id = payload.get('tenant_id')
            cache_key = f"refresh_token_{user_id}_{tenant_id or 'none'}"

            if cache.get(cache_key) != refresh_token:
                raise AuthenticationFailed('Refresh token is invalid or revoked')

            # Get user and tenant
            user = User.objects.get(id=user_id)
            tenant = None
            if tenant_id:
                from models import Tenant
                tenant = Tenant.objects.get(tenant_id=tenant_id)

            # Generate new tokens
            return JWTTokenManager.generate_tokens(user, tenant)

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Refresh token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid refresh token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')

    @staticmethod
    def revoke_token(token: str):
        """Blacklist a token"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        # Blacklist for remaining token lifetime
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256'],
                options={'verify_exp': False}
            )
            exp = payload.get('exp', 0)
            ttl = max(0, exp - timezone.now().timestamp())
            cache.set(f"blacklisted_token_{token_hash}", True, timeout=int(ttl))
        except:
            pass

    @staticmethod
    def revoke_all_user_tokens(user_id: int, tenant_id: Optional[str] = None):
        """Revoke all tokens for a user in a tenant"""
        cache_key = f"refresh_token_{user_id}_{tenant_id or 'none'}"
        cache.delete(cache_key)


# Enhanced JWT Authentication
class JWTAuthentication(BaseAuthentication):
    """JWT authentication backend with tenant context"""

    def authenticate(self, request):
        """Authenticate user using JWT token"""
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            payload = JWTTokenManager.validate_token(token)

            # Get user
            user = User.objects.get(id=payload['user_id'])

            # Set tenant context
            tenant_id = payload.get('tenant_id')
            if tenant_id:
                from models import Tenant
                tenant = Tenant.objects.get(tenant_id=tenant_id, is_active=True)
                request.tenant = tenant
            else:
                request.tenant = None

            # Store token payload in request for later use
            request.jwt_payload = payload

            return (user, None)

        except (User.DoesNotExist, Exception) as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')

    def authenticate_header(self, request):
        return 'Bearer'


# Role-Based Access Control System
class RBACPermissionChecker:
    """Centralized RBAC permission checking"""

    # Permission hierarchy
    PERMISSION_HIERARCHY = {
        'owner': ['*'],  # All permissions
        'admin': [
            'assets.*', 'users.manage', 'settings.manage',
            'qr_content.*', 'devices.*', 'subscription.view',
            'analytics.view', 'api_keys.manage'
        ],
        'editor': [
            'assets.*', 'qr_content.*', 'devices.view',
            'analytics.view'
        ],
        'viewer': [
            'assets.view', 'qr_content.view', 'devices.view',
            'analytics.view'
        ],
        'device_manager': [
            'devices.*', 'assets.view', 'qr_content.view'
        ]
    }

    @classmethod
    def check_permission(cls, user: User, tenant: 'Tenant', permission: str) -> bool:
        """Check if user has specific permission in tenant"""
        if not tenant:
            return user.is_superuser

        try:
            from models import TenantUser
            tenant_user = TenantUser.objects.get(user=user, tenant=tenant, is_active=True)

            # Check role-based permissions
            role_permissions = cls.PERMISSION_HIERARCHY.get(tenant_user.role, [])

            # Check wildcard permissions
            if '*' in role_permissions:
                return True

            # Check specific permission
            if permission in role_permissions:
                return True

            # Check category wildcard (e.g., 'assets.*')
            category = permission.split('.')[0] + '.*'
            if category in role_permissions:
                return True

            # Check custom permissions
            custom_permissions = tenant_user.permissions.get('permissions', [])
            if permission in custom_permissions:
                return True

            # Check denied permissions (explicit deny)
            denied_permissions = tenant_user.permissions.get('denied', [])
            if permission in denied_permissions:
                return False

            return False

        except:
            return False

    @classmethod
    def get_user_permissions(cls, user: User, tenant: 'Tenant') -> List[str]:
        """Get all permissions for user in tenant"""
        if not tenant:
            return ['*'] if user.is_superuser else []

        try:
            from models import TenantUser
            tenant_user = TenantUser.objects.get(user=user, tenant=tenant, is_active=True)

            permissions = set()

            # Add role-based permissions
            role_permissions = cls.PERMISSION_HIERARCHY.get(tenant_user.role, [])
            permissions.update(role_permissions)

            # Add custom permissions
            custom_permissions = tenant_user.permissions.get('permissions', [])
            permissions.update(custom_permissions)

            # Remove denied permissions
            denied_permissions = tenant_user.permissions.get('denied', [])
            permissions -= set(denied_permissions)

            return list(permissions)

        except:
            return []


# Permission Classes
class TenantPermission(BasePermission):
    """Base tenant permission class"""
    required_permissions = []

    def has_permission(self, request, view):
        """Check if user has required permissions in tenant"""
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, 'tenant', None)
        if not tenant and hasattr(view, 'require_tenant') and view.require_tenant:
            return False

        # Check all required permissions
        for permission in self.required_permissions:
            if not RBACPermissionChecker.check_permission(request.user, tenant, permission):
                return False

        return True


class AssetPermission(TenantPermission):
    """Asset-specific permissions"""

    def get_required_permissions(self, request, view):
        """Get required permissions based on action"""
        action_permissions = {
            'list': ['assets.view'],
            'retrieve': ['assets.view'],
            'create': ['assets.create'],
            'update': ['assets.edit'],
            'partial_update': ['assets.edit'],
            'destroy': ['assets.delete'],
            'bulk_update': ['assets.edit'],
            'generate_share_code': ['assets.share']
        }

        action = getattr(view, 'action', None)
        return action_permissions.get(action, ['assets.view'])

    def has_permission(self, request, view):
        self.required_permissions = self.get_required_permissions(request, view)
        return super().has_permission(request, view)


class QRContentPermission(TenantPermission):
    """QR content permissions"""

    def get_required_permissions(self, request, view):
        action_permissions = {
            'list': ['qr_content.view'],
            'retrieve': ['qr_content.view'],
            'create': ['qr_content.create'],
            'update': ['qr_content.edit'],
            'destroy': ['qr_content.delete'],
            'track_access': []  # Public access
        }

        action = getattr(view, 'action', None)
        return action_permissions.get(action, ['qr_content.view'])

    def has_permission(self, request, view):
        self.required_permissions = self.get_required_permissions(request, view)
        return super().has_permission(request, view)


class TenantManagementPermission(TenantPermission):
    """Tenant management permissions"""
    required_permissions = ['settings.manage']


class SubscriptionPermission(TenantPermission):
    """Subscription management permissions"""

    def get_required_permissions(self, request, view):
        action_permissions = {
            'retrieve': ['subscription.view'],
            'update': ['subscription.manage'],
            'upgrade_plan': ['subscription.manage'],
            'billing_history': ['subscription.view']
        }

        action = getattr(view, 'action', None)
        return action_permissions.get(action, ['subscription.view'])

    def has_permission(self, request, view):
        self.required_permissions = self.get_required_permissions(request, view)
        return super().has_permission(request, view)


# API Key Authentication
class APIKeyAuthentication(BaseAuthentication):
    """API key authentication for programmatic access"""

    def authenticate(self, request):
        """Authenticate using API key"""
        api_key = request.META.get('HTTP_X_API_KEY')

        if not api_key:
            return None

        try:
            from models import APIKey
            import hashlib

            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            api_key_obj = APIKey.objects.select_related('tenant').get(
                key_hash=key_hash,
                is_active=True
            )

            # Check expiration
            if api_key_obj.expires_at and timezone.now() > api_key_obj.expires_at:
                raise AuthenticationFailed('API key has expired')

            # Check IP whitelist
            if api_key_obj.ip_whitelist:
                client_ip = self._get_client_ip(request)
                if client_ip not in api_key_obj.ip_whitelist:
                    raise AuthenticationFailed('IP address not whitelisted')

            # Update usage tracking
            api_key_obj.last_used = timezone.now()
            api_key_obj.usage_count += 1
            api_key_obj.save(update_fields=['last_used', 'usage_count'])

            # Set tenant context
            request.tenant = api_key_obj.tenant
            request.api_key = api_key_obj

            # Create a system user for API access
            api_user = User(
                username=f"api_key_{api_key_obj.key_id}",
                email=f"api_{api_key_obj.key_id}@system.local"
            )
            api_user.id = -1  # Special ID for API users

            return (api_user, api_key_obj)

        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Rate Limiting for API Keys
class APIKeyRateLimitMixin:
    """Rate limiting mixin for API key authentication"""

    def check_api_key_rate_limit(self, request):
        """Check rate limit for API key"""
        api_key = getattr(request, 'api_key', None)
        if not api_key:
            return True

        cache_key = f"api_rate_limit_{api_key.key_id}"
        current_requests = cache.get(cache_key, 0)

        if current_requests >= api_key.rate_limit:
            from rest_framework.exceptions import Throttled
            raise Throttled(detail=f"API key rate limit exceeded: {api_key.rate_limit} requests per hour")

        # Increment counter with 1-hour expiry
        cache.set(cache_key, current_requests + 1, timeout=3600)
        return True


# Permission Decorators
def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(view_func):
        def wrapper(self, request, *args, **kwargs):
            tenant = getattr(request, 'tenant', None)
            if not RBACPermissionChecker.check_permission(request.user, tenant, permission):
                raise PermissionDenied(f"Permission '{permission}' required")
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def require_tenant():
    """Decorator to require tenant context"""
    def decorator(view_func):
        def wrapper(self, request, *args, **kwargs):
            if not getattr(request, 'tenant', None):
                raise PermissionDenied("Tenant context required")
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator


# Auth Views
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class LoginView(APIView):
    """JWT login endpoint"""

    def post(self, request):
        """Authenticate user and return JWT tokens"""
        email = request.data.get('email')
        password = request.data.get('password')
        tenant_subdomain = request.data.get('tenant')

        if not email or not password:
            return Response(
                {'error': 'Email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                raise User.DoesNotExist()
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get tenant if specified
        tenant = None
        if tenant_subdomain:
            try:
                from models import Tenant, TenantUser
                tenant = Tenant.objects.get(subdomain=tenant_subdomain, is_active=True)

                # Verify user belongs to tenant
                if not TenantUser.objects.filter(user=user, tenant=tenant, is_active=True).exists():
                    return Response(
                        {'error': 'User does not belong to this tenant'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Tenant.DoesNotExist:
                return Response(
                    {'error': 'Tenant not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Generate tokens
        tokens = JWTTokenManager.generate_tokens(user, tenant)

        # Get user permissions
        permissions = RBACPermissionChecker.get_user_permissions(user, tenant)

        response_data = {
            **tokens,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'tenant': {
                'id': str(tenant.tenant_id),
                'name': tenant.name,
                'subdomain': tenant.subdomain
            } if tenant else None,
            'permissions': permissions
        }

        return Response(response_data, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """Token refresh endpoint"""

    def post(self, request):
        """Refresh access token"""
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tokens = JWTTokenManager.refresh_access_token(refresh_token)
            return Response(tokens, status=status.HTTP_200_OK)

        except AuthenticationFailed as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """Logout endpoint"""
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        """Logout user and revoke tokens"""
        # Get token from request
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            JWTTokenManager.revoke_token(token)

        # Revoke refresh token
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            JWTTokenManager.revoke_token(refresh_token)

        return Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK
        )


# Django Settings Configuration
JWT_SETTINGS = {
    'JWT_SECRET_KEY': 'your-secret-key-here',  # Should be in environment variables
    'JWT_ACCESS_TOKEN_LIFETIME': 15,  # minutes
    'JWT_REFRESH_TOKEN_LIFETIME': 7,  # days
    'JWT_ALGORITHM': 'HS256',
}

# Add to Django REST Framework settings
REST_FRAMEWORK_AUTH_SETTINGS = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authentication.jwt_auth.JWTAuthentication',
        'authentication.jwt_auth.APIKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Backwards compatibility
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}