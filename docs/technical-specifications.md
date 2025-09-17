# Technical Specifications - Digital Signage Enhancement

## 1. Multi-Tenant Architecture Specification

### 1.1 Tenant Isolation Strategy
**Approach**: Schema-based isolation with row-level security (RLS)

```sql
-- Tenant isolation implementation
CREATE POLICY tenant_isolation ON assets
    FOR ALL TO authenticated
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Tenant context setting
SET app.current_tenant_id = 'tenant-uuid-here';
```

### 1.2 Tenant Discovery Mechanism
**Methods**:
1. Subdomain-based: `tenant.signage.com`
2. Header-based: `X-Tenant-ID`
3. Path-based: `/tenant/{slug}/api/...`

```python
class TenantMiddleware:
    def process_request(self, request):
        tenant = None

        # 1. Try subdomain extraction
        if hasattr(request, 'META') and 'HTTP_HOST' in request.META:
            host = request.META['HTTP_HOST']
            subdomain = host.split('.')[0]
            tenant = Tenant.objects.filter(slug=subdomain).first()

        # 2. Try header extraction
        if not tenant and 'HTTP_X_TENANT_ID' in request.META:
            tenant_id = request.META['HTTP_X_TENANT_ID']
            tenant = Tenant.objects.filter(id=tenant_id).first()

        # 3. Try path extraction
        if not tenant:
            path_parts = request.path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[0] == 'tenant':
                tenant = Tenant.objects.filter(slug=path_parts[1]).first()

        request.tenant = tenant

        # Set database context
        if tenant:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET app.current_tenant_id = %s", [str(tenant.id)]
                )
```

### 1.3 Resource Allocation & Limits
```python
TENANT_LIMITS = {
    'basic': {
        'max_assets': 100,
        'max_storage_mb': 1024,  # 1GB
        'max_devices': 5,
        'max_users': 3,
        'api_rate_limit': '1000/hour'
    },
    'premium': {
        'max_assets': 1000,
        'max_storage_mb': 10240,  # 10GB
        'max_devices': 25,
        'max_users': 15,
        'api_rate_limit': '10000/hour'
    },
    'enterprise': {
        'max_assets': -1,  # Unlimited
        'max_storage_mb': -1,
        'max_devices': -1,
        'max_users': -1,
        'api_rate_limit': '100000/hour'
    }
}
```

## 2. Database Schema Specification

### 2.1 Core Tables
```sql
-- Tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    domain VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT valid_subscription_tier
        CHECK (subscription_tier IN ('basic', 'premium', 'enterprise'))
);

-- Enhanced users table (extends Django's User)
CREATE TABLE tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    UNIQUE(tenant_id, user_id),
    CONSTRAINT valid_role
        CHECK (role IN ('tenant_admin', 'content_manager', 'viewer', 'device_operator'))
);

-- Enhanced assets table
CREATE TABLE assets (
    asset_id VARCHAR(32) PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    uri TEXT,
    md5 TEXT,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    duration BIGINT,
    mimetype TEXT,
    is_enabled BOOLEAN DEFAULT FALSE,
    is_processing BOOLEAN DEFAULT FALSE,
    nocache BOOLEAN DEFAULT FALSE,
    play_order INTEGER DEFAULT 0,
    skip_asset_check BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    file_size BIGINT DEFAULT 0,
    thumbnail_url TEXT,

    -- Enable RLS
    CONSTRAINT assets_tenant_check CHECK (tenant_id IS NOT NULL)
);

-- Layouts table
CREATE TABLE layouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    width INTEGER NOT NULL DEFAULT 1920,
    height INTEGER NOT NULL DEFAULT 1080,
    grid_columns INTEGER DEFAULT 12,
    grid_rows INTEGER DEFAULT 8,
    template_data JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

-- Layout assets relationship
CREATE TABLE layout_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layout_id UUID REFERENCES layouts(id) ON DELETE CASCADE,
    asset_id VARCHAR(32) REFERENCES assets(asset_id) ON DELETE CASCADE,
    grid_x INTEGER NOT NULL,
    grid_y INTEGER NOT NULL,
    grid_width INTEGER NOT NULL DEFAULT 1,
    grid_height INTEGER NOT NULL DEFAULT 1,
    z_index INTEGER DEFAULT 1,
    animation_settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(layout_id, asset_id)
);

-- Devices table
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    location VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_ping TIMESTAMP,
    current_layout_id UUID REFERENCES layouts(id),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- QR Code assets table
CREATE TABLE qr_code_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(32) REFERENCES assets(asset_id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL,  -- url, text, wifi, contact, etc.
    content_data JSONB NOT NULL,
    template_settings JSONB DEFAULT '{}',
    refresh_interval INTEGER DEFAULT 300,
    scan_tracking BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_content_type
        CHECK (content_type IN ('url', 'text', 'wifi', 'contact', 'email', 'sms', 'phone'))
);

-- QR Code scan analytics
CREATE TABLE qr_code_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qr_asset_id UUID REFERENCES qr_code_assets(id) ON DELETE CASCADE,
    scanned_at TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET,
    location_data JSONB,
    device_info JSONB
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE NOT NULL,
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    midtrans_subscription_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_status
        CHECK (status IN ('active', 'past_due', 'canceled', 'unpaid'))
);

-- Payment history
CREATE TABLE payment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE NOT NULL,
    subscription_id UUID REFERENCES subscriptions(id),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',
    midtrans_transaction_id VARCHAR(100),
    midtrans_order_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_payment_status
        CHECK (status IN ('pending', 'paid', 'failed', 'refunded'))
);

-- Plugins table
CREATE TABLE plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    plugin_type VARCHAR(50) NOT NULL,
    entry_point TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    settings_schema JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tenant plugin installations
CREATE TABLE tenant_plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    plugin_id UUID REFERENCES plugins(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    installed_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, plugin_id)
);
```

### 2.2 Indexes for Performance
```sql
-- Critical indexes for multi-tenant queries
CREATE INDEX idx_assets_tenant_enabled ON assets(tenant_id, is_enabled);
CREATE INDEX idx_assets_tenant_play_order ON assets(tenant_id, play_order);
CREATE INDEX idx_layouts_tenant_active ON layouts(tenant_id, is_active);
CREATE INDEX idx_devices_tenant_active ON devices(tenant_id, is_active);
CREATE INDEX idx_tenant_users_tenant_role ON tenant_users(tenant_id, role);
CREATE INDEX idx_qr_scans_asset_date ON qr_code_scans(qr_asset_id, scanned_at);
CREATE INDEX idx_payment_history_tenant_status ON payment_history(tenant_id, status);

-- Composite indexes for common queries
CREATE INDEX idx_assets_tenant_dates ON assets(tenant_id, start_date, end_date);
CREATE INDEX idx_layout_assets_layout_zindex ON layout_assets(layout_id, z_index);
```

## 3. API Specification

### 3.1 Authentication & Authorization
```python
# JWT Token Structure
{
    "user_id": 123,
    "tenant_id": "uuid",
    "role": "content_manager",
    "permissions": ["assets.view", "assets.add", "layouts.view"],
    "exp": 1640995200,
    "iat": 1640908800
}

# Permission Checking Decorator
def require_permission(permission):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")

            user_permissions = get_user_permissions(request.user, request.tenant)
            if permission not in user_permissions and '*' not in user_permissions:
                raise PermissionDenied(f"Permission {permission} required")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 3.2 API Endpoints Structure
```python
# API v3 URL Structure
urlpatterns = [
    # Authentication
    path('auth/login/', LoginView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
    path('auth/refresh/', TokenRefreshView.as_view()),

    # Tenant Management
    path('tenants/', TenantListCreateView.as_view()),
    path('tenants/<uuid:tenant_id>/', TenantDetailView.as_view()),
    path('tenants/current/', CurrentTenantView.as_view()),

    # User Management
    path('users/', UserListCreateView.as_view()),
    path('users/<int:user_id>/', UserDetailView.as_view()),
    path('users/<int:user_id>/permissions/', UserPermissionsView.as_view()),

    # Asset Management
    path('assets/', AssetListCreateView.as_view()),
    path('assets/<str:asset_id>/', AssetDetailView.as_view()),
    path('assets/<str:asset_id>/analytics/', AssetAnalyticsView.as_view()),
    path('assets/bulk/', AssetBulkOperationsView.as_view()),

    # Layout Management
    path('layouts/', LayoutListCreateView.as_view()),
    path('layouts/<uuid:layout_id>/', LayoutDetailView.as_view()),
    path('layouts/<uuid:layout_id>/preview/', LayoutPreviewView.as_view()),
    path('layouts/<uuid:layout_id>/assets/', LayoutAssetView.as_view()),

    # QR Code Management
    path('qr-codes/', QRCodeListCreateView.as_view()),
    path('qr-codes/<uuid:qr_id>/', QRCodeDetailView.as_view()),
    path('qr-codes/<uuid:qr_id>/analytics/', QRCodeAnalyticsView.as_view()),

    # Device Management
    path('devices/', DeviceListCreateView.as_view()),
    path('devices/<uuid:device_id>/', DeviceDetailView.as_view()),
    path('devices/<uuid:device_id>/sync/', DeviceSyncView.as_view()),

    # Billing & Subscriptions
    path('billing/subscription/', SubscriptionView.as_view()),
    path('billing/invoices/', InvoiceListView.as_view()),
    path('billing/payment-methods/', PaymentMethodView.as_view()),
    path('billing/webhooks/midtrans/', MidtransWebhookView.as_view()),

    # Plugin Management
    path('plugins/', PluginListView.as_view()),
    path('plugins/<uuid:plugin_id>/', PluginDetailView.as_view()),
    path('plugins/<uuid:plugin_id>/install/', PluginInstallView.as_view()),
    path('plugins/<uuid:plugin_id>/configure/', PluginConfigureView.as_view()),

    # Analytics & Reporting
    path('analytics/dashboard/', DashboardAnalyticsView.as_view()),
    path('analytics/assets/', AssetAnalyticsView.as_view()),
    path('analytics/devices/', DeviceAnalyticsView.as_view()),
]
```

### 3.3 Response Format Standards
```python
# Standard Success Response
{
    "success": true,
    "data": {
        // Response data
    },
    "meta": {
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "v3",
        "tenant_id": "uuid"
    }
}

# Standard Error Response
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field_name": ["Error message"]
        }
    },
    "meta": {
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "v3"
    }
}

# Paginated Response
{
    "success": true,
    "data": {
        "items": [...],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 100,
            "pages": 5,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

## 4. Payment Integration Specification

### 4.1 Midtrans Integration
```python
class MidtransService:
    def __init__(self):
        self.client_key = settings.MIDTRANS_CLIENT_KEY
        self.server_key = settings.MIDTRANS_SERVER_KEY
        self.is_production = settings.MIDTRANS_IS_PRODUCTION

    def create_subscription(self, tenant, plan, payment_method):
        """Create subscription with Midtrans"""
        payload = {
            "name": f"Digital Signage - {plan}",
            "amount": self.get_plan_amount(plan),
            "currency": "IDR",
            "payment_type": "credit_card",
            "credit_card": {
                "token_id": payment_method['token']
            },
            "schedule": {
                "interval": 1,
                "interval_unit": "month",
                "max_interval": 12,
                "start_time": datetime.now().isoformat()
            },
            "customer_details": {
                "first_name": tenant.name,
                "email": tenant.email,
                "phone": tenant.phone
            }
        }

        response = self.make_request('/subscriptions', payload)
        return response

    def handle_webhook(self, payload):
        """Handle Midtrans webhook notifications"""
        signature_key = payload.get('signature_key')
        order_id = payload.get('order_id')
        status_code = payload.get('status_code')
        gross_amount = payload.get('gross_amount')

        # Verify signature
        expected_signature = self.generate_signature(
            order_id, status_code, gross_amount
        )

        if signature_key != expected_signature:
            raise ValueError("Invalid signature")

        # Process webhook based on transaction status
        transaction_status = payload.get('transaction_status')

        if transaction_status == 'capture':
            self.handle_successful_payment(payload)
        elif transaction_status == 'settlement':
            self.handle_settlement(payload)
        elif transaction_status in ['cancel', 'deny', 'expire']:
            self.handle_failed_payment(payload)
```

### 4.2 Subscription Management
```python
class SubscriptionManager:
    def __init__(self, tenant):
        self.tenant = tenant

    def upgrade_plan(self, new_plan):
        """Upgrade tenant subscription plan"""
        current_subscription = self.tenant.subscription

        # Calculate prorated amount
        prorated_amount = self.calculate_proration(
            current_subscription, new_plan
        )

        # Create Midtrans transaction for upgrade
        if prorated_amount > 0:
            payment_result = self.process_upgrade_payment(prorated_amount)
            if not payment_result['success']:
                raise PaymentError("Upgrade payment failed")

        # Update subscription
        current_subscription.plan = new_plan
        current_subscription.save()

        # Update tenant limits
        self.update_tenant_limits(new_plan)

    def check_usage_limits(self):
        """Check if tenant is within usage limits"""
        limits = TENANT_LIMITS[self.tenant.subscription.plan]
        usage = self.get_current_usage()

        violations = []
        for limit_type, limit_value in limits.items():
            if limit_value != -1 and usage[limit_type] > limit_value:
                violations.append({
                    'type': limit_type,
                    'current': usage[limit_type],
                    'limit': limit_value
                })

        return violations
```

## 5. QR/Barcode System Specification

### 5.1 QR Code Generation
```python
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image, ImageDraw, ImageFont

class QRCodeGenerator:
    def __init__(self):
        self.default_size = (400, 400)
        self.default_border = 4

    def generate_qr_code(self, content_type, data, template_settings=None):
        """Generate QR code based on content type and template"""
        qr_data = self.format_qr_data(content_type, data)

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=self.default_border,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Apply template if provided
        if template_settings:
            img = self.apply_template(img, template_settings)

        return img

    def format_qr_data(self, content_type, data):
        """Format data based on QR code type"""
        formatters = {
            'url': lambda d: d['url'],
            'wifi': lambda d: f"WIFI:T:{d['security']};S:{d['ssid']};P:{d['password']};H:{d['hidden']};;",
            'contact': lambda d: f"BEGIN:VCARD\nVERSION:3.0\nFN:{d['name']}\nTEL:{d['phone']}\nEMAIL:{d['email']}\nEND:VCARD",
            'text': lambda d: d['text'],
            'sms': lambda d: f"SMSTO:{d['number']}:{d['message']}",
            'email': lambda d: f"mailto:{d['email']}?subject={d['subject']}&body={d['body']}"
        }

        formatter = formatters.get(content_type)
        if not formatter:
            raise ValueError(f"Unsupported QR code type: {content_type}")

        return formatter(data)

    def apply_template(self, qr_img, template_settings):
        """Apply custom template to QR code"""
        template_type = template_settings.get('type', 'basic')

        if template_type == 'branded':
            return self.apply_branded_template(qr_img, template_settings)
        elif template_type == 'custom':
            return self.apply_custom_template(qr_img, template_settings)

        return qr_img

    def apply_branded_template(self, qr_img, settings):
        """Apply branded template with logo and colors"""
        # Resize QR code
        qr_size = settings.get('qr_size', 300)
        qr_img = qr_img.resize((qr_size, qr_size))

        # Create larger canvas
        canvas_size = settings.get('canvas_size', (400, 500))
        canvas = Image.new('RGB', canvas_size, settings.get('bg_color', 'white'))

        # Paste QR code
        qr_position = ((canvas_size[0] - qr_size) // 2, 50)
        canvas.paste(qr_img, qr_position)

        # Add logo if provided
        if 'logo_url' in settings:
            logo = self.load_logo(settings['logo_url'])
            logo_size = settings.get('logo_size', (50, 50))
            logo = logo.resize(logo_size)
            logo_pos = ((canvas_size[0] - logo_size[0]) // 2, 10)
            canvas.paste(logo, logo_pos)

        # Add text
        if 'text' in settings:
            self.add_text_to_image(canvas, settings['text'], settings)

        return canvas
```

### 5.2 Analytics & Tracking
```python
class QRCodeAnalytics:
    def __init__(self, qr_asset):
        self.qr_asset = qr_asset

    def track_scan(self, request):
        """Track QR code scan"""
        scan_data = {
            'qr_asset': self.qr_asset,
            'scanned_at': timezone.now(),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self.get_client_ip(request),
            'device_info': self.parse_user_agent(request.META.get('HTTP_USER_AGENT', '')),
        }

        # Get location data from IP (optional)
        if settings.ENABLE_GEOLOCATION:
            scan_data['location_data'] = self.get_location_from_ip(
                scan_data['ip_address']
            )

        QRCodeScan.objects.create(**scan_data)

    def get_analytics_data(self, date_range=None):
        """Get analytics data for QR code"""
        scans = QRCodeScan.objects.filter(qr_asset=self.qr_asset)

        if date_range:
            scans = scans.filter(
                scanned_at__gte=date_range['start'],
                scanned_at__lte=date_range['end']
            )

        analytics = {
            'total_scans': scans.count(),
            'unique_ips': scans.values('ip_address').distinct().count(),
            'scans_by_day': self.group_scans_by_day(scans),
            'device_breakdown': self.analyze_devices(scans),
            'location_breakdown': self.analyze_locations(scans),
        }

        return analytics
```

This technical specification provides the detailed implementation guidelines for each major component of the digital signage system enhancement. Each section includes concrete code examples, database schemas, and API specifications that development teams can follow during implementation.