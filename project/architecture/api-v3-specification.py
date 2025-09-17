# API v3 Enhancement Specification
# Complete specification for new SaaS-enabled API endpoints with backwards compatibility

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from typing import Optional

# Enhanced serializers for v3 API
from rest_framework import serializers


class TenantAssetSerializerV3(serializers.ModelSerializer):
    """Enhanced asset serializer with tenant context"""
    is_active = serializers.SerializerMethodField()
    share_url = serializers.SerializerMethodField()
    qr_codes = serializers.SerializerMethodField()
    analytics = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Asset
        fields = [
            'asset_id', 'name', 'uri', 'start_date', 'end_date', 'duration',
            'mimetype', 'file_size', 'resolution', 'is_enabled', 'nocache',
            'play_order', 'skip_asset_check', 'is_active', 'is_processing',
            'is_shared', 'share_code', 'share_expires_at', 'tags', 'metadata',
            'description', 'created_at', 'updated_at', 'view_count',
            'last_played', 'share_url', 'qr_codes', 'analytics', 'created_by_name'
        ]
        read_only_fields = ['asset_id', 'created_at', 'updated_at', 'view_count']

    def get_is_active(self, obj):
        return obj.is_active()

    def get_share_url(self, obj):
        if obj.share_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/shared/{obj.share_code}')
        return None

    def get_qr_codes(self, obj):
        qr_contents = obj.qrcontent_set.filter(is_active=True)
        return [{
            'qr_code': qr.qr_code,
            'barcode': qr.barcode,
            'title': qr.title,
            'access_count': qr.access_count
        } for qr in qr_contents]

    def get_analytics(self, obj):
        return {
            'total_views': obj.view_count,
            'last_played': obj.last_played,
            'share_access_count': sum(qr.access_count for qr in obj.qrcontent_set.all())
        }


class CreateAssetSerializerV3(serializers.ModelSerializer):
    """Enhanced asset creation with tenant-aware validation"""
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    metadata = serializers.JSONField(required=False)

    class Meta:
        model = Asset
        fields = [
            'name', 'uri', 'start_date', 'end_date', 'duration', 'mimetype',
            'is_enabled', 'nocache', 'play_order', 'skip_asset_check',
            'is_shared', 'tags', 'metadata', 'description'
        ]

    def validate(self, data):
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None)

        if tenant:
            # Check tenant limits
            current_assets = tenant.current_asset_count
            if current_assets >= tenant.max_assets:
                raise serializers.ValidationError(
                    f"Asset limit reached. Current plan allows {tenant.max_assets} assets."
                )

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['tenant'] = getattr(request, 'tenant', None)
        validated_data['created_by'] = request.user if request else None

        if validated_data.get('is_shared'):
            asset = Asset(**validated_data)
            asset.generate_share_code()
            asset.save()
        else:
            asset = Asset.objects.create(**validated_data)

        return asset


class QRContentSerializerV3(serializers.ModelSerializer):
    """QR/Barcode content serializer"""
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    access_analytics = serializers.SerializerMethodField()

    class Meta:
        model = QRContent
        fields = [
            'qr_id', 'qr_code', 'barcode', 'title', 'description',
            'thumbnail_url', 'is_active', 'is_public', 'requires_authentication',
            'expires_at', 'max_access_count', 'access_count', 'last_accessed',
            'created_at', 'asset_name', 'access_analytics'
        ]
        read_only_fields = ['qr_id', 'qr_code', 'barcode', 'access_count', 'last_accessed']

    def get_access_analytics(self, obj):
        # Analyze access patterns
        recent_access = [
            log for log in obj.access_log[-10:]  # Last 10 accesses
        ]
        return {
            'total_access': obj.access_count,
            'recent_access': recent_access,
            'is_accessible': obj.is_accessible(),
            'days_until_expiry': (
                (obj.expires_at - timezone.now()).days
                if obj.expires_at else None
            )
        }


class TenantSerializer(serializers.ModelSerializer):
    """Tenant management serializer"""
    current_usage = serializers.SerializerMethodField()
    subscription_info = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'tenant_id', 'name', 'subdomain', 'custom_domain', 'plan_type',
            'max_assets', 'max_devices', 'max_users', 'storage_quota_gb',
            'is_active', 'created_at', 'settings', 'contact_email',
            'current_usage', 'subscription_info'
        ]
        read_only_fields = ['tenant_id', 'created_at']

    def get_current_usage(self, obj):
        return {
            'assets': obj.current_asset_count,
            'users': obj.current_user_count,
            'storage_gb': obj.storage_used_gb,
            'devices': obj.device_set.filter(is_active=True).count()
        }

    def get_subscription_info(self, obj):
        try:
            subscription = obj.subscription
            return {
                'plan_name': subscription.plan_name,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'is_trial': subscription.is_trial,
                'days_until_renewal': subscription.days_until_renewal
            }
        except Subscription.DoesNotExist:
            return None


class SubscriptionSerializer(serializers.ModelSerializer):
    """Subscription management serializer"""
    billing_history = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'subscription_id', 'plan_name', 'billing_cycle', 'status', 'amount',
            'currency', 'current_period_start', 'current_period_end',
            'trial_start', 'trial_end', 'payment_provider', 'created_at',
            'billing_history'
        ]
        read_only_fields = ['subscription_id', 'created_at', 'external_subscription_id']

    def get_billing_history(self, obj):
        # This would integrate with payment provider API
        return []  # Placeholder for billing history


# Enhanced ViewSets for v3 API
class TenantAssetViewSet(viewsets.ModelViewSet):
    """Tenant-aware asset management"""
    serializer_class = TenantAssetSerializerV3
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateAssetSerializerV3
        return TenantAssetSerializerV3

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return Asset.objects.none()

        queryset = Asset.objects.filter(tenant=tenant)

        # Filter by tags
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__overlap=tags)

        # Filter by mimetype
        mimetype = self.request.query_params.get('mimetype')
        if mimetype:
            queryset = queryset.filter(mimetype__icontains=mimetype)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_enabled=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_enabled=False)

        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__overlap=[search])
            )

        return queryset.order_by('-created_at')

    @extend_schema(
        summary="Bulk update assets",
        request=serializers.ListSerializer(child=TenantAssetSerializerV3())
    )
    @action(detail=False, methods=['patch'])
    def bulk_update(self, request):
        """Bulk update multiple assets"""
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant required'}, status=status.HTTP_400_BAD_REQUEST)

        asset_updates = request.data
        updated_assets = []

        for update_data in asset_updates:
            asset_id = update_data.get('asset_id')
            if not asset_id:
                continue

            try:
                asset = Asset.objects.get(asset_id=asset_id, tenant=tenant)
                serializer = TenantAssetSerializerV3(
                    asset, data=update_data, partial=True,
                    context={'request': request}
                )
                if serializer.is_valid():
                    serializer.save(updated_by=request.user)
                    updated_assets.append(serializer.data)
            except Asset.DoesNotExist:
                continue

        return Response({
            'updated_count': len(updated_assets),
            'assets': updated_assets
        })

    @action(detail=True, methods=['post'])
    def generate_share_code(self, request, pk=None):
        """Generate or regenerate share code for asset"""
        asset = self.get_object()
        if not asset.can_be_shared():
            return Response(
                {'error': 'Asset cannot be shared in current state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        asset.generate_share_code()
        asset.is_shared = True
        asset.save()

        return Response({
            'share_code': asset.share_code,
            'share_url': request.build_absolute_uri(f'/shared/{asset.share_code}')
        })

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get detailed analytics for asset"""
        asset = self.get_object()

        # Get QR code analytics
        qr_analytics = []
        for qr in asset.qrcontent_set.all():
            qr_analytics.append({
                'qr_code': qr.qr_code,
                'access_count': qr.access_count,
                'last_accessed': qr.last_accessed,
                'access_log': qr.access_log[-5:]  # Last 5 accesses
            })

        analytics_data = {
            'asset_id': asset.asset_id,
            'total_views': asset.view_count,
            'last_played': asset.last_played,
            'qr_analytics': qr_analytics,
            'sharing_stats': {
                'is_shared': asset.is_shared,
                'share_code': asset.share_code,
                'total_share_access': sum(qr.access_count for qr in asset.qrcontent_set.all())
            }
        }

        return Response(analytics_data)


class QRContentViewSet(viewsets.ModelViewSet):
    """QR/Barcode content management"""
    serializer_class = QRContentSerializerV3
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return QRContent.objects.none()

        return QRContent.objects.filter(tenant=tenant).order_by('-created_at')

    def perform_create(self, serializer):
        import secrets

        tenant = getattr(self.request, 'tenant', None)

        # Generate unique codes
        qr_code = f"QR{secrets.token_hex(8).upper()}"
        while QRContent.objects.filter(qr_code=qr_code).exists():
            qr_code = f"QR{secrets.token_hex(8).upper()}"

        barcode = None
        if self.request.data.get('include_barcode'):
            barcode = f"BC{secrets.token_hex(6).upper()}"
            while QRContent.objects.filter(barcode=barcode).exists():
                barcode = f"BC{secrets.token_hex(6).upper()}"

        serializer.save(
            tenant=tenant,
            qr_code=qr_code,
            barcode=barcode,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def track_access(self, request, pk=None):
        """Track QR code access"""
        qr_content = self.get_object()

        if not qr_content.is_accessible():
            return Response(
                {'error': 'QR content is not accessible'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Log the access
        access_data = {
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'referer': request.META.get('HTTP_REFERER')
        }

        qr_content.log_access(access_data)

        return Response({
            'asset_url': qr_content.asset.uri,
            'access_count': qr_content.access_count
        })


class TenantManagementViewSet(viewsets.ModelViewSet):
    """Tenant management and settings"""
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return getattr(self.request, 'tenant', None)

    @action(detail=False, methods=['get'])
    def usage_stats(self, request):
        """Get current tenant usage statistics"""
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant required'}, status=status.HTTP_400_BAD_REQUEST)

        stats = {
            'assets': {
                'current': tenant.current_asset_count,
                'limit': tenant.max_assets,
                'usage_percentage': (tenant.current_asset_count / tenant.max_assets) * 100
            },
            'users': {
                'current': tenant.current_user_count,
                'limit': tenant.max_users,
                'usage_percentage': (tenant.current_user_count / tenant.max_users) * 100
            },
            'storage': {
                'current_gb': tenant.storage_used_gb,
                'limit_gb': tenant.storage_quota_gb,
                'usage_percentage': (tenant.storage_used_gb / tenant.storage_quota_gb) * 100
            },
            'devices': {
                'current': tenant.device_set.filter(is_active=True).count(),
                'limit': tenant.max_devices
            }
        }

        return Response(stats)

    @action(detail=False, methods=['post'])
    def invite_user(self, request):
        """Invite user to tenant"""
        tenant = getattr(request, 'tenant', None)
        email = request.data.get('email')
        role = request.data.get('role', 'viewer')

        if not email:
            return Response({'error': 'Email required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check user limit
        if tenant.current_user_count >= tenant.max_users:
            return Response(
                {'error': 'User limit reached'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or get user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email}
        )

        # Create tenant user relationship
        tenant_user, created = TenantUser.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={
                'role': role,
                'invited_by': request.user
            }
        )

        if not created:
            return Response(
                {'error': 'User already belongs to this tenant'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Send invitation email

        return Response({
            'message': 'User invited successfully',
            'user_id': user.id,
            'role': role
        })


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Subscription management"""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            return getattr(tenant, 'subscription', None)
        return None

    @action(detail=False, methods=['post'])
    def upgrade_plan(self, request):
        """Upgrade subscription plan"""
        tenant = getattr(request, 'tenant', None)
        new_plan = request.data.get('plan_name')

        if not tenant or not new_plan:
            return Response(
                {'error': 'Tenant and plan_name required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Integrate with payment provider for plan upgrade
        # This is a placeholder implementation

        try:
            subscription = tenant.subscription
            subscription.plan_name = new_plan
            subscription.save()

            return Response({
                'message': 'Plan upgraded successfully',
                'new_plan': new_plan
            })
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def billing_history(self, request):
        """Get billing history from payment provider"""
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant required'}, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Integrate with payment provider API
        # This is a placeholder implementation

        return Response({
            'billing_history': [],
            'message': 'Billing history integration pending'
        })


# URL Configuration for v3 API
from django.urls import path, include
from rest_framework.routers import DefaultRouter

def get_url_patterns_v3():
    router = DefaultRouter()
    router.register(r'assets', TenantAssetViewSet, basename='tenant-assets')
    router.register(r'qr-content', QRContentViewSet, basename='qr-content')
    router.register(r'tenant', TenantManagementViewSet, basename='tenant-management')
    router.register(r'subscription', SubscriptionViewSet, basename='subscription')

    return [
        path('v3/', include(router.urls)),

        # Backwards compatibility proxies
        path('v3/legacy/v1/', include('api.urls.v1')),
        path('v3/legacy/v2/', include('api.urls.v2')),

        # Public access endpoints (no tenant required)
        path('v3/public/qr/<str:qr_code>/', QRContentViewSet.as_view({
            'get': 'track_access'
        }), name='public-qr-access'),

        path('v3/public/shared/<str:share_code>/', TenantAssetViewSet.as_view({
            'get': 'retrieve'
        }), name='public-shared-asset'),
    ]


# Middleware for tenant context
class TenantContextMiddleware:
    """Enhanced tenant middleware with multiple identification methods"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set tenant context for v3 endpoints
        if request.path.startswith('/api/v3/'):
            request.tenant = self.get_tenant_from_request(request)
        else:
            # Backwards compatibility: no tenant context for legacy endpoints
            request.tenant = None

        response = self.get_response(request)
        return response

    def get_tenant_from_request(self, request):
        """Multiple methods to identify tenant"""

        # Method 1: Subdomain-based
        host = request.get_host().split(':')[0]
        if '.' in host and not host.startswith('www'):
            subdomain = host.split('.')[0]
            try:
                return Tenant.objects.get(subdomain=subdomain, is_active=True)
            except Tenant.DoesNotExist:
                pass

        # Method 2: Custom domain
        try:
            return Tenant.objects.get(custom_domain=host, is_active=True)
        except Tenant.DoesNotExist:
            pass

        # Method 3: Header-based (for API clients)
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                return Tenant.objects.get(tenant_id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                pass

        # Method 4: JWT token tenant claim
        if hasattr(request, 'user') and request.user.is_authenticated:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    import jwt
                    from django.conf import settings
                    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
                    tenant_id = payload.get('tenant_id')
                    if tenant_id:
                        return Tenant.objects.get(tenant_id=tenant_id, is_active=True)
                except:
                    pass

        return None