# QR/Barcode Content Sharing System Design
# Complete implementation of QR code and barcode sharing functionality

import qrcode
import barcode
from barcode.writer import ImageWriter
import io
import base64
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from PIL import Image, ImageDraw, ImageFont
import secrets
import hashlib


# QR Code Generator Service
class QRCodeGenerator:
    """Service for generating QR codes with various formats and customizations"""

    def __init__(self):
        self.default_settings = {
            'version': 1,
            'error_correction': qrcode.constants.ERROR_CORRECT_L,
            'box_size': 10,
            'border': 4,
            'fill_color': 'black',
            'back_color': 'white'
        }

    def generate_qr_code(self, data: str, **kwargs) -> Dict[str, Any]:
        """Generate QR code with customizable settings"""
        settings = {**self.default_settings, **kwargs}

        qr = qrcode.QRCode(
            version=settings['version'],
            error_correction=settings['error_correction'],
            box_size=settings['box_size'],
            border=settings['border'],
        )

        qr.add_data(data)
        qr.make(fit=True)

        # Create QR code image
        img = qr.make_image(
            fill_color=settings['fill_color'],
            back_color=settings['back_color']
        )

        # Convert to base64 for web display
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return {
            'image_base64': f"data:image/png;base64,{img_str}",
            'image_data': buffer.getvalue(),
            'format': 'PNG',
            'size': img.size
        }

    def generate_custom_qr_code(self, data: str, logo_path: Optional[str] = None,
                               custom_colors: Dict = None) -> Dict[str, Any]:
        """Generate QR code with logo and custom styling"""
        colors = custom_colors or {}

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for logo
            box_size=10,
            border=4,
        )

        qr.add_data(data)
        qr.make(fit=True)

        # Create QR code image
        qr_img = qr.make_image(
            fill_color=colors.get('fill_color', 'black'),
            back_color=colors.get('back_color', 'white')
        ).convert('RGB')

        # Add logo if provided
        if logo_path:
            qr_img = self._add_logo_to_qr(qr_img, logo_path)

        # Convert to base64
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return {
            'image_base64': f"data:image/png;base64,{img_str}",
            'image_data': buffer.getvalue(),
            'format': 'PNG',
            'size': qr_img.size
        }

    def _add_logo_to_qr(self, qr_img: Image.Image, logo_path: str) -> Image.Image:
        """Add logo to center of QR code"""
        try:
            logo = Image.open(logo_path)

            # Calculate logo size (should be about 10% of QR code)
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 5

            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # Create a white background for logo
            logo_bg = Image.new('RGB', (logo_size + 20, logo_size + 20), 'white')
            logo_bg.paste(logo, (10, 10))

            # Calculate position to center logo
            pos = ((qr_width - logo_size - 20) // 2, (qr_height - logo_size - 20) // 2)

            # Paste logo onto QR code
            qr_img.paste(logo_bg, pos)

            return qr_img

        except Exception:
            # Return original QR code if logo fails
            return qr_img


# Barcode Generator Service
class BarcodeGenerator:
    """Service for generating various barcode formats"""

    SUPPORTED_FORMATS = {
        'code128': barcode.Code128,
        'code39': barcode.Code39,
        'ean13': barcode.EAN13,
        'ean8': barcode.EAN8,
        'upc': barcode.UPCA
    }

    def generate_barcode(self, data: str, format_type: str = 'code128') -> Dict[str, Any]:
        """Generate barcode in specified format"""
        if format_type not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported barcode format: {format_type}")

        barcode_class = self.SUPPORTED_FORMATS[format_type]

        try:
            # Create barcode
            code = barcode_class(data, writer=ImageWriter())

            # Generate image
            buffer = io.BytesIO()
            code.write(buffer)

            # Convert to base64
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return {
                'image_base64': f"data:image/png;base64,{img_str}",
                'image_data': buffer.getvalue(),
                'format': 'PNG',
                'barcode_type': format_type,
                'data': data
            }

        except Exception as e:
            raise ValueError(f"Failed to generate barcode: {str(e)}")

    def generate_custom_barcode(self, data: str, format_type: str = 'code128',
                               options: Dict = None) -> Dict[str, Any]:
        """Generate barcode with custom options"""
        options = options or {}

        barcode_class = self.SUPPORTED_FORMATS.get(format_type, barcode.Code128)

        # Custom writer options
        writer_options = {
            'module_width': options.get('module_width', 0.2),
            'module_height': options.get('module_height', 15.0),
            'quiet_zone': options.get('quiet_zone', 6.5),
            'font_size': options.get('font_size', 10),
            'text_distance': options.get('text_distance', 5.0),
            'background': options.get('background', 'white'),
            'foreground': options.get('foreground', 'black'),
        }

        try:
            writer = ImageWriter()
            writer.set_options(writer_options)

            code = barcode_class(data, writer=writer)
            buffer = io.BytesIO()
            code.write(buffer)

            img_str = base64.b64encode(buffer.getvalue()).decode()

            return {
                'image_base64': f"data:image/png;base64,{img_str}",
                'image_data': buffer.getvalue(),
                'format': 'PNG',
                'barcode_type': format_type,
                'data': data,
                'options': writer_options
            }

        except Exception as e:
            raise ValueError(f"Failed to generate custom barcode: {str(e)}")


# Content Sharing Service
class ContentSharingService:
    """Service for managing content sharing via QR/barcode"""

    def __init__(self, tenant: 'Tenant'):
        self.tenant = tenant
        self.qr_generator = QRCodeGenerator()
        self.barcode_generator = BarcodeGenerator()

    def create_shareable_content(self, asset: 'Asset', sharing_config: Dict) -> 'QRContent':
        """Create shareable content with QR/barcode"""
        from models import QRContent

        # Generate unique codes
        qr_code = self._generate_unique_qr_code()
        barcode_code = None

        if sharing_config.get('include_barcode', False):
            barcode_code = self._generate_unique_barcode()

        # Create sharing URL
        share_url = self._build_share_url(qr_code)

        # Generate QR code image
        qr_image_data = self.qr_generator.generate_qr_code(
            share_url,
            **sharing_config.get('qr_options', {})
        )

        # Generate barcode image if requested
        barcode_image_data = None
        if barcode_code:
            barcode_image_data = self.barcode_generator.generate_barcode(
                barcode_code,
                sharing_config.get('barcode_format', 'code128')
            )

        # Create QR content record
        qr_content = QRContent.objects.create(
            tenant=self.tenant,
            asset=asset,
            qr_code=qr_code,
            barcode=barcode_code,
            title=sharing_config.get('title', asset.name),
            description=sharing_config.get('description', ''),
            is_public=sharing_config.get('is_public', True),
            requires_authentication=sharing_config.get('requires_authentication', False),
            expires_at=sharing_config.get('expires_at'),
            max_access_count=sharing_config.get('max_access_count'),
            allowed_domains=sharing_config.get('allowed_domains', [])
        )

        # Store generated images (in production, store in file system or CDN)
        self._store_generated_images(qr_content, qr_image_data, barcode_image_data)

        return qr_content

    def access_shared_content(self, qr_code: str, request_data: Dict) -> Dict[str, Any]:
        """Handle access to shared content via QR code"""
        from models import QRContent

        try:
            qr_content = QRContent.objects.select_related('asset', 'tenant').get(
                qr_code=qr_code,
                is_active=True
            )
        except QRContent.DoesNotExist:
            raise ValueError("QR code not found or inactive")

        # Check accessibility
        if not qr_content.is_accessible():
            reasons = []
            if qr_content.expires_at and timezone.now() > qr_content.expires_at:
                reasons.append("expired")
            if qr_content.max_access_count and qr_content.access_count >= qr_content.max_access_count:
                reasons.append("access_limit_reached")

            raise ValueError(f"Content not accessible: {', '.join(reasons)}")

        # Check domain restrictions
        if qr_content.allowed_domains:
            referer = request_data.get('referer', '')
            if not any(domain in referer for domain in qr_content.allowed_domains):
                raise ValueError("Access denied: domain not allowed")

        # Check authentication requirement
        if qr_content.requires_authentication and not request_data.get('authenticated', False):
            raise ValueError("Authentication required")

        # Log access
        qr_content.log_access(request_data)

        # Prepare response data
        response_data = {
            'qr_content': {
                'title': qr_content.title,
                'description': qr_content.description,
                'access_count': qr_content.access_count
            },
            'asset': {
                'name': qr_content.asset.name,
                'uri': qr_content.asset.uri,
                'mimetype': qr_content.asset.mimetype,
                'duration': qr_content.asset.duration
            },
            'access_info': {
                'accessed_at': timezone.now(),
                'expires_at': qr_content.expires_at,
                'remaining_access': (
                    qr_content.max_access_count - qr_content.access_count
                    if qr_content.max_access_count else None
                )
            }
        }

        return response_data

    def get_sharing_analytics(self, qr_content_id: str) -> Dict[str, Any]:
        """Get analytics for shared content"""
        from models import QRContent

        qr_content = QRContent.objects.get(
            qr_id=qr_content_id,
            tenant=self.tenant
        )

        # Analyze access patterns
        access_log = qr_content.access_log

        # Group by date
        daily_access = {}
        for access in access_log:
            date = access['timestamp'][:10]  # YYYY-MM-DD
            daily_access[date] = daily_access.get(date, 0) + 1

        # Geographic analysis (basic IP-based)
        ip_countries = {}
        for access in access_log:
            ip = access.get('ip_address', 'unknown')
            # In production, use GeoIP service
            country = self._get_country_from_ip(ip)
            ip_countries[country] = ip_countries.get(country, 0) + 1

        # Device/browser analysis
        user_agents = {}
        for access in access_log:
            ua = access.get('user_agent', 'unknown')
            device_type = self._parse_user_agent(ua)
            user_agents[device_type] = user_agents.get(device_type, 0) + 1

        return {
            'qr_code': qr_content.qr_code,
            'total_access': qr_content.access_count,
            'created_at': qr_content.created_at,
            'last_accessed': qr_content.last_accessed,
            'daily_access': daily_access,
            'geographic_distribution': ip_countries,
            'device_distribution': user_agents,
            'is_accessible': qr_content.is_accessible(),
            'expires_at': qr_content.expires_at
        }

    def _generate_unique_qr_code(self) -> str:
        """Generate unique QR code"""
        from models import QRContent

        while True:
            code = f"QR{secrets.token_hex(8).upper()}"
            if not QRContent.objects.filter(qr_code=code).exists():
                return code

    def _generate_unique_barcode(self) -> str:
        """Generate unique barcode"""
        from models import QRContent

        while True:
            # Generate 12-digit barcode for EAN-13 compatibility
            code = f"{secrets.randbelow(999999999999):012d}"
            if not QRContent.objects.filter(barcode=code).exists():
                return code

    def _build_share_url(self, qr_code: str) -> str:
        """Build complete sharing URL"""
        base_url = getattr(settings, 'BASE_SHARE_URL', 'https://share.anthias.com')
        return f"{base_url}/shared/{qr_code}"

    def _store_generated_images(self, qr_content: 'QRContent',
                               qr_image_data: Dict, barcode_image_data: Dict = None):
        """Store generated QR/barcode images"""
        # In production, store in file system, S3, or CDN
        # For now, we'll store in cache for demonstration

        cache_key_qr = f"qr_image_{qr_content.qr_code}"
        cache.set(cache_key_qr, qr_image_data, timeout=86400 * 30)  # 30 days

        if barcode_image_data:
            cache_key_barcode = f"barcode_image_{qr_content.barcode}"
            cache.set(cache_key_barcode, barcode_image_data, timeout=86400 * 30)

    def _get_country_from_ip(self, ip: str) -> str:
        """Get country from IP address (placeholder)"""
        # In production, integrate with GeoIP service like MaxMind
        return "Unknown"

    def _parse_user_agent(self, user_agent: str) -> str:
        """Parse user agent to determine device type"""
        ua = user_agent.lower()
        if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
            return 'Mobile'
        elif 'tablet' in ua or 'ipad' in ua:
            return 'Tablet'
        else:
            return 'Desktop'


# Public Access Views
class PublicQRAccessView(APIView):
    """Public endpoint for QR code access"""
    authentication_classes = []  # No authentication required
    permission_classes = []

    def get(self, request, qr_code):
        """Access shared content via QR code"""
        try:
            # Get request metadata
            request_data = {
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referer': request.META.get('HTTP_REFERER', ''),
                'authenticated': request.user.is_authenticated if hasattr(request, 'user') else False
            }

            # Determine tenant from QR code
            from models import QRContent
            qr_content = QRContent.objects.select_related('tenant').get(qr_code=qr_code)

            sharing_service = ContentSharingService(qr_content.tenant)
            content_data = sharing_service.access_shared_content(qr_code, request_data)

            return Response(content_data, status=status.HTTP_200_OK)

        except QRContent.DoesNotExist:
            return Response(
                {'error': 'QR code not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class QRImageView(APIView):
    """Serve QR code images"""
    authentication_classes = []
    permission_classes = []

    def get(self, request, qr_code):
        """Serve QR code image"""
        # Check cache first
        cache_key = f"qr_image_{qr_code}"
        image_data = cache.get(cache_key)

        if not image_data:
            # Generate on-the-fly if not cached
            try:
                from models import QRContent
                qr_content = QRContent.objects.get(qr_code=qr_code, is_active=True)

                sharing_service = ContentSharingService(qr_content.tenant)
                share_url = sharing_service._build_share_url(qr_code)

                qr_generator = QRCodeGenerator()
                image_data = qr_generator.generate_qr_code(share_url)

                # Cache the generated image
                cache.set(cache_key, image_data, timeout=86400 * 7)  # 7 days

            except QRContent.DoesNotExist:
                return HttpResponse(status=404)

        # Return image
        response = HttpResponse(image_data['image_data'], content_type='image/png')
        response['Cache-Control'] = 'public, max-age=604800'  # 7 days
        return response


class BarcodeImageView(APIView):
    """Serve barcode images"""
    authentication_classes = []
    permission_classes = []

    def get(self, request, barcode):
        """Serve barcode image"""
        cache_key = f"barcode_image_{barcode}"
        image_data = cache.get(cache_key)

        if not image_data:
            # Generate on-the-fly
            try:
                from models import QRContent
                qr_content = QRContent.objects.get(barcode=barcode, is_active=True)

                barcode_generator = BarcodeGenerator()
                image_data = barcode_generator.generate_barcode(barcode)

                cache.set(cache_key, image_data, timeout=86400 * 7)

            except QRContent.DoesNotExist:
                return HttpResponse(status=404)

        response = HttpResponse(image_data['image_data'], content_type='image/png')
        response['Cache-Control'] = 'public, max-age=604800'
        return response


# Sharing Management Views
from rest_framework import viewsets
from rest_framework.decorators import action

class QRContentManagementViewSet(viewsets.ModelViewSet):
    """Management interface for QR/barcode content"""

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            from models import QRContent
            return QRContent.objects.none()

        return QRContent.objects.filter(tenant=tenant).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def create_shareable_content(self, request):
        """Create new shareable content"""
        asset_id = request.data.get('asset_id')
        sharing_config = request.data.get('config', {})

        try:
            from models import Asset
            asset = Asset.objects.get(asset_id=asset_id, tenant=request.tenant)

            sharing_service = ContentSharingService(request.tenant)
            qr_content = sharing_service.create_shareable_content(asset, sharing_config)

            return Response({
                'qr_content_id': str(qr_content.qr_id),
                'qr_code': qr_content.qr_code,
                'barcode': qr_content.barcode,
                'share_url': sharing_service._build_share_url(qr_content.qr_code),
                'qr_image_url': f"/api/v3/public/qr-image/{qr_content.qr_code}/",
                'barcode_image_url': f"/api/v3/public/barcode-image/{qr_content.barcode}/" if qr_content.barcode else None
            }, status=status.HTTP_201_CREATED)

        except Asset.DoesNotExist:
            return Response(
                {'error': 'Asset not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for QR content"""
        qr_content = self.get_object()
        sharing_service = ContentSharingService(request.tenant)
        analytics_data = sharing_service.get_sharing_analytics(str(qr_content.qr_id))

        return Response(analytics_data)

    @action(detail=False, methods=['get'])
    def bulk_analytics(self, request):
        """Get analytics for multiple QR contents"""
        qr_contents = self.get_queryset()
        sharing_service = ContentSharingService(request.tenant)

        analytics_summary = {
            'total_qr_codes': qr_contents.count(),
            'total_access': sum(qr.access_count for qr in qr_contents),
            'active_codes': qr_contents.filter(is_active=True).count(),
            'expired_codes': qr_contents.filter(
                expires_at__lt=timezone.now()
            ).count()
        }

        return Response(analytics_summary)


# URL Configuration
from django.urls import path

def get_qr_sharing_urls():
    """Get URL patterns for QR sharing system"""
    return [
        # Public access URLs
        path('public/qr/<str:qr_code>/', PublicQRAccessView.as_view(), name='public-qr-access'),
        path('public/qr-image/<str:qr_code>/', QRImageView.as_view(), name='qr-image'),
        path('public/barcode-image/<str:barcode>/', BarcodeImageView.as_view(), name='barcode-image'),

        # Management URLs (require authentication)
        path('qr-management/', QRContentManagementViewSet.as_view({
            'get': 'list',
            'post': 'create_shareable_content'
        }), name='qr-management'),

        path('qr-management/<str:pk>/', QRContentManagementViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy'
        }), name='qr-management-detail'),

        path('qr-management/<str:pk>/analytics/', QRContentManagementViewSet.as_view({
            'get': 'analytics'
        }), name='qr-analytics'),

        path('qr-management/bulk/analytics/', QRContentManagementViewSet.as_view({
            'get': 'bulk_analytics'
        }), name='qr-bulk-analytics'),
    ]


# Integration with Asset Model
def add_sharing_methods_to_asset():
    """Add sharing convenience methods to Asset model"""
    from models import Asset

    def create_qr_share(self, sharing_config: Dict = None) -> 'QRContent':
        """Create QR/barcode sharing for this asset"""
        sharing_config = sharing_config or {}
        sharing_service = ContentSharingService(self.tenant)
        return sharing_service.create_shareable_content(self, sharing_config)

    def get_qr_shares(self):
        """Get all QR shares for this asset"""
        return self.qrcontent_set.filter(is_active=True)

    def get_share_analytics(self) -> Dict[str, Any]:
        """Get sharing analytics for this asset"""
        qr_contents = self.get_qr_shares()
        total_access = sum(qr.access_count for qr in qr_contents)

        return {
            'total_qr_codes': qr_contents.count(),
            'total_access': total_access,
            'most_accessed_qr': max(qr_contents, key=lambda x: x.access_count) if qr_contents else None
        }

    # Add methods to Asset model
    Asset.create_qr_share = create_qr_share
    Asset.get_qr_shares = get_qr_shares
    Asset.get_share_analytics = get_share_analytics


# Background Tasks for Analytics
def process_qr_analytics_daily():
    """Background task to process daily QR analytics"""
    from models import QRContent, Tenant
    from django.db.models import Count, Sum

    # Aggregate daily statistics
    daily_stats = QRContent.objects.values('tenant__name').annotate(
        total_qr_codes=Count('qr_id'),
        total_access=Sum('access_count')
    )

    # Store in cache for dashboard
    for stat in daily_stats:
        cache_key = f"daily_qr_stats_{stat['tenant__name']}"
        cache.set(cache_key, stat, timeout=86400)  # 24 hours


# Settings Configuration
QR_SHARING_SETTINGS = {
    'DEFAULT_QR_SIZE': 300,
    'DEFAULT_QR_ERROR_CORRECTION': 'L',
    'DEFAULT_BARCODE_FORMAT': 'code128',
    'MAX_QR_CODES_PER_TENANT': 10000,
    'DEFAULT_QR_EXPIRY_DAYS': 365,
    'ENABLE_QR_ANALYTICS': True,
    'ENABLE_GEOGRAPHIC_TRACKING': True,
    'QR_IMAGE_CACHE_DURATION': 86400 * 7,  # 7 days
}