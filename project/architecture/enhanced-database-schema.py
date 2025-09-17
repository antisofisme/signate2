# Enhanced Database Schema for Anthias SaaS Platform
# This file contains the complete database schema design for multi-tenant architecture

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator


def generate_asset_id():
    """Generate unique asset ID"""
    return uuid.uuid4().hex


class Tenant(models.Model):
    """Multi-tenant organization model"""
    tenant_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Organization name")
    subdomain = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique subdomain for tenant access"
    )
    custom_domain = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Optional custom domain"
    )

    # Plan and limits
    plan_type = models.CharField(
        max_length=50,
        default='basic',
        choices=[
            ('basic', 'Basic Plan'),
            ('professional', 'Professional Plan'),
            ('enterprise', 'Enterprise Plan'),
            ('legacy', 'Legacy Migration')
        ]
    )
    max_assets = models.IntegerField(default=100, help_text="Maximum assets allowed")
    max_devices = models.IntegerField(default=5, help_text="Maximum devices allowed")
    max_users = models.IntegerField(default=10, help_text="Maximum users allowed")
    storage_quota_gb = models.IntegerField(default=10, help_text="Storage quota in GB")

    # Status and metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    settings = models.JSONField(default=dict, help_text="Tenant-specific settings")

    # Contact information
    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=20, null=True, blank=True)

    # Billing information
    billing_address = models.JSONField(default=dict)
    tax_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'tenants'
        indexes = [
            models.Index(fields=['subdomain']),
            models.Index(fields=['is_active']),
            models.Index(fields=['plan_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.subdomain})"

    @property
    def current_asset_count(self):
        return self.asset_set.count()

    @property
    def current_user_count(self):
        return self.tenantuser_set.count()

    @property
    def storage_used_gb(self):
        # Calculate total storage used by assets
        total_size = self.asset_set.aggregate(
            total=models.Sum('file_size')
        )['total'] or 0
        return total_size / (1024 * 1024 * 1024)  # Convert to GB


class TenantUser(models.Model):
    """User membership in tenants with roles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    role = models.CharField(
        max_length=50,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Administrator'),
            ('editor', 'Editor'),
            ('viewer', 'Viewer'),
            ('device_manager', 'Device Manager')
        ],
        default='viewer'
    )

    # Fine-grained permissions
    permissions = models.JSONField(
        default=dict,
        help_text="Custom permissions override"
    )

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Invitation tracking
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_users'
    )
    invitation_accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tenant_users'
        unique_together = ['user', 'tenant']
        indexes = [
            models.Index(fields=['tenant', 'role']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name} ({self.role})"

    def has_permission(self, permission):
        """Check if user has specific permission"""
        # Role-based permissions
        role_permissions = {
            'owner': ['*'],  # All permissions
            'admin': [
                'assets.*', 'users.manage', 'settings.manage',
                'qr_content.*', 'devices.*'
            ],
            'editor': ['assets.*', 'qr_content.*'],
            'viewer': ['assets.view', 'qr_content.view'],
            'device_manager': ['devices.*', 'assets.view']
        }

        base_permissions = role_permissions.get(self.role, [])

        # Check wildcard permissions
        if '*' in base_permissions:
            return True

        # Check specific permission
        if permission in base_permissions:
            return True

        # Check category wildcard (e.g., 'assets.*')
        category = permission.split('.')[0] + '.*'
        if category in base_permissions:
            return True

        # Check custom permissions
        custom_permissions = self.permissions.get('permissions', [])
        return permission in custom_permissions


class Asset(models.Model):
    """Enhanced Asset model with multi-tenant support"""
    # Primary identification
    asset_id = models.TextField(
        primary_key=True,
        default=generate_asset_id,
        editable=False
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,  # For backwards compatibility
        help_text="Tenant owner (null for legacy assets)"
    )

    # Basic asset information
    name = models.TextField(blank=True, null=True)
    uri = models.TextField(blank=True, null=True)
    md5 = models.TextField(blank=True, null=True)

    # Scheduling
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    duration = models.BigIntegerField(blank=True, null=True)

    # Content metadata
    mimetype = models.TextField(blank=True, null=True)
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    resolution = models.CharField(max_length=20, blank=True, null=True)  # e.g., "1920x1080"

    # Playback settings
    is_enabled = models.BooleanField(default=False)
    is_processing = models.BooleanField(default=False)
    nocache = models.BooleanField(default=False)
    play_order = models.IntegerField(default=0)
    skip_asset_check = models.BooleanField(default=False)

    # SaaS enhancements
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assets'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_assets'
    )

    # Sharing and collaboration
    is_shared = models.BooleanField(default=False)
    share_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique code for sharing via QR/barcode"
    )
    share_expires_at = models.DateTimeField(null=True, blank=True)

    # Organization and metadata
    tags = models.JSONField(default=list, help_text="Asset tags for organization")
    metadata = models.JSONField(default=dict, help_text="Custom metadata")
    description = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Analytics
    view_count = models.IntegerField(default=0)
    last_played = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'assets'
        indexes = [
            models.Index(fields=['tenant', 'is_enabled']),
            models.Index(fields=['tenant', 'play_order']),
            models.Index(fields=['share_code']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['mimetype']),
            models.Index(fields=['tags'], name='asset_tags_gin_idx'),
        ]

    def __str__(self):
        return self.name or f"Asset {self.asset_id}"

    def is_active(self):
        """Check if asset is currently active"""
        if self.is_enabled and self.start_date and self.end_date:
            current_time = timezone.now()
            return self.start_date < current_time < self.end_date
        return False

    def can_be_shared(self):
        """Check if asset can be shared"""
        return self.is_enabled and not self.is_processing

    def generate_share_code(self):
        """Generate unique share code"""
        import secrets
        while True:
            code = secrets.token_urlsafe(8)
            if not Asset.objects.filter(share_code=code).exists():
                self.share_code = code
                break


class Device(models.Model):
    """Device management for tenants"""
    device_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    # Device information
    name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=17, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    # Device status
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    # Configuration
    settings = models.JSONField(default=dict)
    assigned_playlist = models.JSONField(default=list)  # List of asset IDs

    # Hardware info
    hardware_info = models.JSONField(default=dict)
    software_version = models.CharField(max_length=50, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devices'
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['mac_address']),
            models.Index(fields=['is_online']),
        ]

    def __str__(self):
        return f"{self.name} ({self.mac_address})"


class Subscription(models.Model):
    """Subscription management"""
    subscription_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE)

    # Plan information
    plan_name = models.CharField(max_length=100)
    plan_features = models.JSONField(default=dict)

    # Billing cycle
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
            ('lifetime', 'Lifetime')
        ],
        default='monthly'
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('trialing', 'Trialing'),
            ('active', 'Active'),
            ('past_due', 'Past Due'),
            ('canceled', 'Canceled'),
            ('unpaid', 'Unpaid')
        ],
        default='trialing'
    )

    # Financial information
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    # Period tracking
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)

    # Payment provider integration
    payment_provider = models.CharField(max_length=50, default='midtrans')
    external_subscription_id = models.CharField(max_length=255, blank=True)
    external_customer_id = models.CharField(max_length=255, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'subscriptions'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['current_period_end']),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.plan_name} ({self.status})"

    @property
    def is_trial(self):
        return self.status == 'trialing'

    @property
    def days_until_renewal(self):
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return delta.days
        return None


class QRContent(models.Model):
    """QR Code and Barcode content sharing"""
    qr_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    # Codes
    qr_code = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # Content information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(blank=True, null=True)

    # Access control
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    requires_authentication = models.BooleanField(default=False)
    allowed_domains = models.JSONField(default=list)  # Domain whitelist

    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    max_access_count = models.IntegerField(null=True, blank=True)

    # Analytics
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_log = models.JSONField(default=list)  # Track access details

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Created by
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'qr_contents'
        indexes = [
            models.Index(fields=['qr_code']),
            models.Index(fields=['barcode']),
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.qr_code}"

    def is_accessible(self):
        """Check if QR content is currently accessible"""
        if not self.is_active:
            return False

        if self.expires_at and timezone.now() > self.expires_at:
            return False

        if self.max_access_count and self.access_count >= self.max_access_count:
            return False

        return True

    def log_access(self, request_data):
        """Log access attempt"""
        self.access_count += 1
        self.last_accessed = timezone.now()

        # Add to access log (keep last 100 entries)
        access_entry = {
            'timestamp': timezone.now().isoformat(),
            'ip_address': request_data.get('ip_address'),
            'user_agent': request_data.get('user_agent'),
            'referer': request_data.get('referer')
        }

        self.access_log.append(access_entry)
        if len(self.access_log) > 100:
            self.access_log = self.access_log[-100:]

        self.save()


class APIKey(models.Model):
    """API keys for programmatic access"""
    key_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    # Key information
    name = models.CharField(max_length=255)
    key_hash = models.CharField(max_length=255)  # Hashed API key
    prefix = models.CharField(max_length=10)  # First few chars for identification

    # Permissions and scope
    permissions = models.JSONField(default=list)
    ip_whitelist = models.JSONField(default=list)
    rate_limit = models.IntegerField(default=1000)  # Requests per hour

    # Status
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.BigIntegerField(default=0)

    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'api_keys'
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['key_hash']),
        ]

    def __str__(self):
        return f"{self.name} ({self.prefix}...)"


class AuditLog(models.Model):
    """Audit logging for all tenant activities"""
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # Action details
    action = models.CharField(max_length=100)  # e.g., 'asset.create', 'user.invite'
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255)

    # Change details
    old_values = models.JSONField(default=dict)
    new_values = models.JSONField(default=dict)

    # Request context
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]


# Migration helpers for backwards compatibility
class LegacyAssetMapping(models.Model):
    """Temporary model for migration tracking"""
    original_asset_id = models.TextField()
    new_asset = models.OneToOneField(Asset, on_delete=models.CASCADE)
    migration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'legacy_asset_mappings'