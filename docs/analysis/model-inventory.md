# Anthias Django Models Inventory

## Overview
Current Anthias backend uses a minimal single-model approach focused on asset management. This analysis documents the existing model structure and identifies multi-tenancy enhancement requirements.

## Current Models

### 1. Asset Model (`anthias_app/models.py`)

```python
class Asset(models.Model):
    # Primary Key - UUID-based identifier
    asset_id = models.TextField(
        primary_key=True,
        default=generate_asset_id,
        editable=False
    )

    # Asset Metadata
    name = models.TextField(blank=True, null=True)
    uri = models.TextField(blank=True, null=True)
    md5 = models.TextField(blank=True, null=True)
    mimetype = models.TextField(blank=True, null=True)

    # Scheduling Fields
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    duration = models.BigIntegerField(blank=True, null=True)

    # Control Fields
    is_enabled = models.BooleanField(default=False)
    is_processing = models.BooleanField(default=False)
    nocache = models.BooleanField(default=False)
    skip_asset_check = models.BooleanField(default=False)

    # Playlist Management
    play_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'assets'

    def is_active(self):
        """Check if asset is currently active based on schedule"""
        if self.is_enabled and self.start_date and self.end_date:
            current_time = timezone.now()
            return self.start_date < current_time < self.end_date
        return False
```

### Model Analysis

#### Strengths
- **UUID Primary Keys**: Good for distributed systems
- **Flexible URI Storage**: Supports various asset types
- **Scheduling Logic**: Built-in time-based activation
- **Processing States**: Tracks asset processing status
- **Playlist Ordering**: Supports content sequencing

#### Limitations for SaaS
- **No Tenant Isolation**: All assets in single table
- **No User Ownership**: Missing user/organization relationships
- **No Permission System**: No access control mechanisms
- **No Audit Trail**: Missing creation/modification tracking
- **Limited Metadata**: Basic asset information only

## Missing Models for SaaS Implementation

### 1. Tenant/Organization Model
```python
class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=255, unique=True, null=True)

    # Subscription Info
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES)
    is_active = models.BooleanField(default=True)

    # Limits
    max_assets = models.IntegerField(default=100)
    max_users = models.IntegerField(default=5)
    max_storage_gb = models.IntegerField(default=10)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2. User Management Model
```python
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='users'
    )

    # Profile Info
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    # Permissions
    is_org_admin = models.BooleanField(default=False)
    permissions = models.JSONField(default=dict)

    # Activity
    last_login_ip = models.GenericIPAddressField(null=True)
    is_email_verified = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 3. Enhanced Asset Model
```python
class Asset(models.Model):
    # Primary Key
    asset_id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Tenant Isolation
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='assets'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assets'
    )

    # Asset Metadata (existing fields)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    uri = models.TextField()
    md5 = models.CharField(max_length=32, blank=True)
    mimetype = models.CharField(max_length=100)
    file_size = models.BigIntegerField(default=0)

    # Enhanced Scheduling
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(default=timedelta(seconds=10))
    timezone = models.CharField(max_length=50, default='UTC')

    # Control Fields
    is_enabled = models.BooleanField(default=False)
    is_processing = models.BooleanField(default=False)
    processing_status = models.CharField(max_length=50, default='pending')

    # Playlist & Categorization
    play_order = models.IntegerField(default=0)
    tags = models.JSONField(default=list)
    category = models.CharField(max_length=100, blank=True)

    # Audit Trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(null=True)

    class Meta:
        db_table = 'assets'
        indexes = [
            models.Index(fields=['organization', 'is_enabled']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_asset_name_per_org'
            )
        ]
```

### 4. Subscription & Billing Models
```python
class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE
    )

    # Plan Details
    plan_name = models.CharField(max_length=100)
    plan_price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(max_length=20)  # monthly, yearly

    # Status
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS)
    trial_ends_at = models.DateTimeField(null=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()

    # Payment
    stripe_subscription_id = models.CharField(max_length=255, unique=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UsageMetric(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    metric_type = models.CharField(max_length=50)  # storage, api_calls, assets
    value = models.BigIntegerField()
    date = models.DateField()

    class Meta:
        unique_together = ['organization', 'metric_type', 'date']
```

### 5. Device Management Models
```python
class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='devices'
    )

    # Device Info
    name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=17, unique=True)
    ip_address = models.GenericIPAddressField(null=True)
    location = models.CharField(max_length=255, blank=True)

    # Configuration
    settings = models.JSONField(default=dict)
    assigned_playlist = models.ForeignKey(
        'Playlist',
        on_delete=models.SET_NULL,
        null=True
    )

    # Status
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Playlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    assets = models.ManyToManyField(
        Asset,
        through='PlaylistAsset',
        related_name='playlists'
    )

    # Settings
    is_default = models.BooleanField(default=False)
    shuffle_enabled = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PlaylistAsset(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    order = models.IntegerField()

    class Meta:
        unique_together = ['playlist', 'asset']
        ordering = ['order']
```

## Database Migration Strategy

### Phase 1: Foundation
1. Create Organization model
2. Create enhanced User model
3. Add organization foreign key to existing Asset model
4. Migrate existing data to default organization

### Phase 2: Enhanced Features
1. Add Subscription and billing models
2. Implement Device and Playlist models
3. Add audit trail fields
4. Create proper indexes and constraints

### Phase 3: Optimization
1. Implement database partitioning by organization
2. Add caching layer for frequently accessed data
3. Optimize queries with proper indexing
4. Implement data retention policies

## Data Isolation Strategy

### Row-Level Security (RLS)
```sql
-- PostgreSQL RLS policies
CREATE POLICY organization_isolation ON assets
    FOR ALL TO authenticated_users
    USING (organization_id = current_user_organization());

CREATE POLICY user_asset_access ON assets
    FOR ALL TO authenticated_users
    USING (
        organization_id = current_user_organization() AND
        (created_by_id = current_user_id() OR has_permission('view_all_assets'))
    );
```

### Application-Level Filtering
```python
class OrganizationQuerySet(models.QuerySet):
    def for_organization(self, organization):
        return self.filter(organization=organization)

class AssetManager(models.Manager):
    def get_queryset(self):
        return OrganizationQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.for_organization(user.organization)
```

## Performance Considerations

### Indexing Strategy
- Organization-based indexes for all multi-tenant models
- Composite indexes for common query patterns
- Partial indexes for boolean flags
- Full-text search indexes for content

### Query Optimization
- Always filter by organization first
- Use select_related for foreign key relationships
- Implement prefetch_related for reverse lookups
- Add database-level constraints

### Caching Strategy
- Redis caching for organization settings
- Application-level caching for static data
- Query result caching for expensive operations
- CDN caching for asset content

## Security Considerations

### Data Isolation
- Mandatory organization filtering in all queries
- Database-level RLS policies
- API-level tenant validation
- Audit logging for all data access

### Access Control
- Role-based permissions
- API key authentication for integrations
- Session management with proper expiration
- Rate limiting per organization

## Testing Strategy

### Model Tests
- Unit tests for all model methods
- Integration tests for multi-tenant queries
- Performance tests for large datasets
- Data migration tests

### Security Tests
- Tenant isolation verification
- Permission boundary testing
- SQL injection prevention
- Data leak prevention

## Conclusion

The current single Asset model provides a solid foundation but requires significant enhancement for SaaS implementation. The proposed multi-tenant model structure addresses scalability, security, and feature requirements while maintaining backwards compatibility during migration.

**Key Migration Priorities:**
1. Organization and User models (Foundation)
2. Enhanced Asset model with tenant isolation
3. Subscription and billing integration
4. Device and playlist management
5. Performance optimization and security hardening