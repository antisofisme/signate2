# User-Tenant Relationship Management

## Overview

The User-Tenant Relationship Management system provides comprehensive multi-tenant user management capabilities, allowing users to belong to multiple tenants with different roles and permissions in each.

## Core Concepts

### Multi-Tenant User Model

The system extends Django's built-in User model with multi-tenant capabilities:

- **Global Users**: Users exist globally across the entire system
- **Tenant Memberships**: Users can be members of multiple tenants
- **Role-Based Access**: Each membership has a specific role within the tenant
- **Primary Tenant**: Users can designate one tenant as their primary

### User Model Extensions

```python
# Key fields added to User model
class User(AbstractUser):
    id = UUIDField(primary_key=True)
    email = EmailField(unique=True)  # Primary identifier
    phone_number = CharField(max_length=20)
    is_email_verified = BooleanField(default=False)
    timezone = CharField(max_length=50, default='UTC')
    language = CharField(max_length=10, default='en')
    failed_login_attempts = IntegerField(default=0)
    account_locked_until = DateTimeField(null=True)
    two_factor_enabled = BooleanField(default=False)
    gdpr_consent = BooleanField(default=False)
```

## User-Tenant Membership Model

### UserTenantMembership

The core relationship model connecting users to tenants:

```python
class UserTenantMembership(models.Model):
    user = ForeignKey(User)
    tenant = ForeignKey(Tenant)
    role = ForeignKey(Role)
    is_primary = BooleanField(default=False)
    is_active = BooleanField(default=True)
    joined_at = DateTimeField(auto_now_add=True)
    invited_by = ForeignKey(User, null=True)
    invitation_accepted_at = DateTimeField(null=True)
    last_accessed_at = DateTimeField(auto_now=True)
    access_count = IntegerField(default=0)
```

### Key Features

- **Unique Constraint**: One membership per user-tenant pair
- **Primary Tenant**: Only one primary tenant per user
- **Activity Tracking**: Access count and last accessed timestamp
- **Invitation History**: Track who invited the user
- **Soft Delete**: Memberships can be deactivated instead of deleted

## User Profiles

### Tenant-Specific Profiles

Each user can have customized profiles for different tenants:

```python
class UserProfile(models.Model):
    user = ForeignKey(User)
    tenant = ForeignKey(Tenant)
    display_name = CharField(max_length=100)
    bio = TextField()
    department = CharField(max_length=100)
    job_title = CharField(max_length=100)
    manager = ForeignKey(User, null=True)
    location = CharField(max_length=100)
    work_hours_start = TimeField()
    work_hours_end = TimeField()
    preferences = JSONField(default=dict)
    custom_fields = JSONField(default=dict)
```

### Profile Features

- **Tenant Isolation**: Separate profile for each tenant
- **Customizable Fields**: JSON fields for tenant-specific data
- **Hierarchical Structure**: Manager relationships within tenants
- **Work Schedule**: Time-based settings per tenant

## User Management Operations

### Creating Users

#### 1. Standard User Creation

```python
from backend.utils.user_utils import create_user_with_tenant

user, membership = create_user_with_tenant(
    email='user@example.com',
    tenant=tenant_instance,
    role=role_instance,
    first_name='John',
    last_name='Doe'
)
```

#### 2. CLI User Creation

```bash
# Interactive mode
python manage.py create_user --interactive

# Non-interactive mode
python manage.py create_user \\
    --email user@example.com \\
    --tenant company-slug \\
    --role member \\
    --verified \\
    --primary-tenant
```

### Adding Users to Tenants

```python
from backend.utils.user_utils import add_user_to_tenant

membership = add_user_to_tenant(
    user=user_instance,
    tenant=tenant_instance,
    role=role_instance,
    invited_by=inviter_user,
    is_primary=True
)
```

### Removing Users from Tenants

```python
from backend.utils.user_utils import remove_user_from_tenant

# Soft delete (recommended)
success = remove_user_from_tenant(
    user=user_instance,
    tenant=tenant_instance,
    soft_delete=True
)

# Hard delete
success = remove_user_from_tenant(
    user=user_instance,
    tenant=tenant_instance,
    soft_delete=False
)
```

### Role Management

```python
from backend.utils.user_utils import change_user_role_in_tenant

updated_membership = change_user_role_in_tenant(
    user=user_instance,
    tenant=tenant_instance,
    new_role=new_role_instance,
    changed_by=admin_user
)
```

### Primary Tenant Management

```python
from backend.utils.user_utils import set_primary_tenant

membership = set_primary_tenant(
    user=user_instance,
    tenant=tenant_instance
)
```

## Security Features

### Account Security

- **Account Locking**: Automatic lockout after failed login attempts
- **Password Policies**: Configurable password requirements
- **Two-Factor Authentication**: Optional 2FA support
- **Session Management**: Track and manage user sessions

### Security Utilities

```python
# Lock account
from backend.utils.user_utils import lock_user_account
lock_user_account(user, duration_minutes=30, reason="Security violation")

# Unlock account
from backend.utils.user_utils import unlock_user_account
unlock_user_account(user)

# Generate temporary password
from backend.utils.user_utils import generate_temporary_password
temp_password = generate_temporary_password(length=12)
```

### GDPR Compliance

- **Consent Tracking**: Record and track GDPR consent
- **Data Retention**: Configurable data retention policies
- **Right to be Forgotten**: User data deletion capabilities

## Activity Tracking

### User Activity Model

```python
class UserActivity(models.Model):
    user = ForeignKey(User)
    tenant = ForeignKey(Tenant)
    action = CharField(max_length=100)
    resource_type = CharField(max_length=50)
    resource_id = CharField(max_length=100)
    details = JSONField(default=dict)
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    session_id = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)
```

### Activity Logging

```python
from backend.utils.user_utils import log_user_activity

activity = log_user_activity(
    user=user_instance,
    action='profile_updated',
    tenant=tenant_instance,
    resource_type='profile',
    resource_id=str(profile.id),
    details={'changes': {'department': 'Engineering'}},
    request=request
)
```

### Activity Analytics

```python
from backend.utils.user_utils import get_user_activity_summary

summary = get_user_activity_summary(
    user=user_instance,
    tenant=tenant_instance,
    days=30
)
```

## Session Management

### User Sessions

```python
class UserSession(models.Model):
    user = ForeignKey(User)
    tenant = ForeignKey(Tenant, null=True)
    session_key = CharField(max_length=40, unique=True)
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    is_active = BooleanField(default=True)
    last_activity = DateTimeField(auto_now=True)
    expired_at = DateTimeField(null=True)
```

### Session Cleanup

```python
from backend.utils.user_utils import cleanup_inactive_sessions

# Clean up sessions inactive for 30 days
cleaned_count = cleanup_inactive_sessions(days=30)
```

## Permission System Integration

### Checking Permissions

```python
# Check if user has permission in tenant
has_permission = user.has_tenant_permission(tenant, 'add_project')

# Get all permissions for user in tenant
from backend.utils.user_utils import get_user_permissions_in_tenant
permissions = get_user_permissions_in_tenant(user, tenant)

# Check specific permission
from backend.utils.user_utils import check_user_permission_in_tenant
can_edit = check_user_permission_in_tenant(user, tenant, 'change_project')
```

## API Endpoints

### User Management APIs

- `GET /api/users/` - List users in current tenant
- `POST /api/users/` - Create new user
- `GET /api/users/{id}/` - Get user details
- `PUT /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Deactivate user
- `POST /api/users/{id}/change-password/` - Change password
- `POST /api/users/switch-tenant/` - Switch current tenant

### Profile Management APIs

- `GET /api/users/{id}/profile/` - Get user profile
- `PUT /api/users/{id}/profile/` - Update user profile

### Activity APIs

- `GET /api/users/{id}/activity/` - Get user activity history
- `GET /api/activities/summary/` - Get activity summary

## Best Practices

### User Management

1. **Always use soft deletes** for user memberships
2. **Validate permissions** before user operations
3. **Log all administrative actions** for audit trails
4. **Use transactions** for multi-step operations
5. **Implement proper error handling** with user-friendly messages

### Security

1. **Enforce strong password policies**
2. **Implement account lockout mechanisms**
3. **Monitor for suspicious activities**
4. **Regularly clean up inactive sessions**
5. **Audit user permission changes**

### Performance

1. **Use select_related/prefetch_related** for membership queries
2. **Index frequently queried fields**
3. **Implement pagination** for large user lists
4. **Cache user permission lookups**
5. **Use database-level constraints** for data integrity

## Common Use Cases

### 1. User Registration with Invitation

```python
# In invitation acceptance view
invitation = UserInvitation.objects.get(token=token)
user, membership = create_user_with_tenant(
    email=invitation.email,
    tenant=invitation.tenant,
    role=invitation.role,
    invited_by=invitation.invited_by
)
invitation.accept(user)
```

### 2. Tenant Switching

```python
# In tenant switch API
request.session['current_tenant_id'] = str(new_tenant.id)
membership = user.user_tenant_memberships.get(tenant=new_tenant)
membership.record_access()
```

### 3. Bulk User Operations

```python
from backend.utils.user_utils import bulk_user_operations

results = bulk_user_operations(
    users=User.objects.filter(is_active=False),
    operation='activate'
)
```

### 4. User Context Retrieval

```python
from backend.utils.user_utils import get_user_tenant_context

context = get_user_tenant_context(user, tenant)
if context:
    role = context['role']
    permissions = context['permissions']
    is_primary = context['is_primary_tenant']
```

## Integration Points

### With RBAC System

- User roles are defined per tenant
- Permissions are checked within tenant context
- Role changes trigger activity logging

### With Authentication System

- JWT tokens include tenant context
- Session management tracks tenant access
- Login/logout activities are logged

### With Audit System

- All user operations are logged
- Activity history is tenant-specific
- Administrative actions are tracked

## Troubleshooting

### Common Issues

1. **User can't access tenant**: Check membership status and role permissions
2. **Primary tenant not set**: Ensure user has at least one active membership
3. **Permission denied**: Verify role has required permissions in tenant
4. **Account locked**: Check failed login attempts and lockout status

### Debugging Queries

```python
# Check user memberships
user.user_tenant_memberships.filter(is_active=True)

# Check user permissions in tenant
membership = user.user_tenant_memberships.get(tenant=tenant)
permissions = membership.role.permissions.all()

# Check recent activities
activities = user.activities.filter(tenant=tenant).order_by('-created_at')[:10]
```