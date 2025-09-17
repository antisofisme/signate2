"""
Base API Classes and Mixins

Common functionality and mixins for analytics API endpoints.
Provides tenant isolation, permission checks, and common utilities.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class AnalyticsPagination(PageNumberPagination):
    """Custom pagination for analytics endpoints."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class TenantIsolationMixin:
    """
    Mixin to ensure tenant isolation in analytics queries.
    Automatically filters queries by tenant.
    """

    def get_queryset(self):
        """Filter queryset by tenant."""
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant'):
            return queryset.filter(tenant=self.request.user.tenant)
        return queryset.none()

    def perform_create(self, serializer):
        """Set tenant on creation."""
        if hasattr(self.request.user, 'tenant'):
            serializer.save(tenant=self.request.user.tenant)
        else:
            raise PermissionError("User must belong to a tenant")


class TimeRangeFilterMixin:
    """
    Mixin to add time range filtering to analytics endpoints.
    Supports common time range parameters.
    """

    def filter_by_time_range(self, queryset, time_field='created_at'):
        """Filter queryset by time range parameters."""
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        period = self.request.query_params.get('period')

        # Handle predefined periods
        if period and not (start_date or end_date):
            now = timezone.now()
            if period == '1h':
                start_date = now - timedelta(hours=1)
            elif period == '24h':
                start_date = now - timedelta(hours=24)
            elif period == '7d':
                start_date = now - timedelta(days=7)
            elif period == '30d':
                start_date = now - timedelta(days=30)
            elif period == '90d':
                start_date = now - timedelta(days=90)

        # Apply date filters
        filters = {}
        if start_date:
            filters[f'{time_field}__gte'] = start_date
        if end_date:
            filters[f'{time_field}__lte'] = end_date

        if filters:
            queryset = queryset.filter(**filters)

        return queryset


class AggregationMixin:
    """
    Mixin to add aggregation capabilities to analytics endpoints.
    Provides common aggregation functions.
    """

    @action(detail=False, methods=['get'])
    def aggregations(self, request):
        """Get aggregated statistics."""
        queryset = self.filter_queryset(self.get_queryset())

        # Get aggregation type from query params
        agg_type = request.query_params.get('type', 'count')
        group_by = request.query_params.get('group_by')

        # Basic aggregations
        if agg_type == 'count':
            result = {'count': queryset.count()}
        elif agg_type == 'summary':
            result = self.get_summary_stats(queryset)
        else:
            result = {'error': 'Invalid aggregation type'}

        # Group by field if specified
        if group_by and hasattr(queryset.model, group_by):
            grouped = queryset.values(group_by).annotate(
                count=Count('id')
            ).order_by('-count')
            result['grouped'] = list(grouped)

        return Response(result)

    def get_summary_stats(self, queryset):
        """Get summary statistics for the queryset."""
        return {
            'count': queryset.count(),
            'created_today': queryset.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'created_this_week': queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'created_this_month': queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
        }


class CachingMixin:
    """
    Mixin to add caching capabilities to analytics endpoints.
    Caches expensive queries with configurable TTL.
    """

    cache_timeout = 300  # 5 minutes default

    def get_cache_key(self, *args):
        """Generate cache key for the request."""
        key_parts = [
            self.__class__.__name__,
            str(self.request.user.id),
            str(getattr(self.request.user, 'tenant_id', 'no-tenant'))
        ]
        key_parts.extend(str(arg) for arg in args)
        return ':'.join(key_parts)

    def get_cached_response(self, cache_key, queryset_func, *args, **kwargs):
        """Get cached response or execute query and cache result."""
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)

        # Execute query
        data = queryset_func(*args, **kwargs)

        # Cache the result
        cache.set(cache_key, data, self.cache_timeout)

        return Response(data)


class AnalyticsPermissionMixin:
    """
    Mixin for analytics-specific permissions.
    Handles role-based access control for analytics data.
    """

    def check_analytics_permission(self, request, permission_type='read'):
        """Check if user has analytics permissions."""
        if not request.user.is_authenticated:
            return False

        # Check if user has specific analytics permissions
        permission_map = {
            'read': 'analytics.view_analytics',
            'write': 'analytics.change_analytics',
            'admin': 'analytics.admin_analytics',
        }

        required_permission = permission_map.get(permission_type)
        if required_permission:
            return request.user.has_perm(required_permission)

        return False


class BaseAnalyticsViewSet(
    TenantIsolationMixin,
    TimeRangeFilterMixin,
    AggregationMixin,
    CachingMixin,
    AnalyticsPermissionMixin,
    viewsets.ModelViewSet
):
    """
    Base viewset for analytics endpoints.
    Combines all common mixins and functionality.
    """

    pagination_class = AnalyticsPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve', 'aggregations']:
            permission_required = 'read'
        elif self.action in ['create', 'update', 'partial_update']:
            permission_required = 'write'
        else:
            permission_required = 'admin'

        # Check analytics permissions
        if not self.check_analytics_permission(self.request, permission_required):
            self.permission_denied(
                self.request,
                message=f"Analytics {permission_required} permission required"
            )

        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trend analysis for the data."""
        queryset = self.filter_queryset(self.get_queryset())

        # Apply time range filtering
        queryset = self.filter_by_time_range(queryset)

        # Group by time periods
        period = request.query_params.get('period', 'day')

        if period == 'hour':
            trunc_func = 'hour'
        elif period == 'day':
            trunc_func = 'day'
        elif period == 'week':
            trunc_func = 'week'
        elif period == 'month':
            trunc_func = 'month'
        else:
            trunc_func = 'day'

        # This would need to be implemented per model
        # with appropriate date truncation
        trends = self.calculate_trends(queryset, trunc_func)

        return Response(trends)

    def calculate_trends(self, queryset, trunc_func):
        """Calculate trends - to be implemented by subclasses."""
        return {'message': 'Trends not implemented for this endpoint'}

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export data in various formats."""
        export_format = request.query_params.get('format', 'csv')
        queryset = self.filter_queryset(self.get_queryset())

        # Apply time range filtering
        queryset = self.filter_by_time_range(queryset)

        if export_format == 'csv':
            return self.export_csv(queryset)
        elif export_format == 'json':
            return self.export_json(queryset)
        else:
            return Response(
                {'error': 'Unsupported export format'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def export_csv(self, queryset):
        """Export queryset as CSV."""
        # This would be implemented with proper CSV generation
        return Response({'message': 'CSV export not implemented'})

    def export_json(self, queryset):
        """Export queryset as JSON."""
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create analytics records."""
        if not self.check_analytics_permission(request, 'write'):
            return Response(
                {'error': 'Write permission required'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        if not isinstance(data, list):
            return Response(
                {'error': 'Data must be a list of objects'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_objects = []
        errors = []

        for item in data:
            serializer = self.get_serializer(data=item)
            if serializer.is_valid():
                self.perform_create(serializer)
                created_objects.append(serializer.data)
            else:
                errors.append(serializer.errors)

        return Response({
            'created': len(created_objects),
            'errors': len(errors),
            'objects': created_objects,
            'error_details': errors
        })


class ReadOnlyAnalyticsViewSet(BaseAnalyticsViewSet):
    """
    Read-only base viewset for analytics data that shouldn't be modified.
    """

    http_method_names = ['get', 'head', 'options']

    def create(self, request, *args, **kwargs):
        return Response(
            {'error': 'Create not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {'error': 'Update not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'error': 'Delete not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )