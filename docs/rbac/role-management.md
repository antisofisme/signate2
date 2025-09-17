# RBAC Role Management Guide

## Overview

This guide provides comprehensive instructions for managing roles and permissions in the RBAC (Role-Based Access Control) system. It covers role creation, assignment, delegation, and maintenance operations.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Role Management](#role-management)
3. [User Assignment](#user-assignment)
4. [Permission Management](#permission-management)
5. [Delegation](#delegation)
6. [Monitoring and Auditing](#monitoring-and-auditing)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Django admin access or API access
- Appropriate permissions (typically Tenant Admin or Super Admin)
- Understanding of tenant context and role hierarchy

### Initial Setup

Run the management command to set up default roles:

```bash
python manage.py setup_default_roles
```

For tenant-specific setup:

```bash
python manage.py setup_default_roles --tenant-id=<tenant-uuid>
```

## Role Management

### Creating Roles

#### Via Django Admin

1. Navigate to RBAC → Roles
2. Click "Add Role"
3. Fill in required fields:
   - **Name**: Human-readable role name
   - **Level**: Hierarchy level (lower = higher privileges)
   - **Tenant**: Tenant scope (optional for system roles)
   - **Parent Role**: Inherit permissions from parent
   - **Description**: Role purpose and scope

#### Via API

```python
# Create a custom role
import requests

role_data = {
    "name": "Project Manager",
    "description": "Manages projects and team assignments",
    "level": 25,
    "tenant": "tenant-uuid",
    "parent_role": "content-manager-uuid",
    "can_delegate": False
}

response = requests.post(
    "https://api.example.com/rbac/roles/",
    json=role_data,
    headers={"Authorization": "Bearer <token>"}
)
```

#### Programmatic Creation

```python
from rbac.models import Role, Tenant

# Create tenant-specific role
tenant = Tenant.objects.get(slug='acme-corp')
role = Role.objects.create_role(
    name='Customer Success Manager',
    level=30,
    tenant=tenant,
    description='Manages customer relationships and success metrics',
    can_delegate=True,
    max_delegations=1
)
```

### Role Hierarchy

#### Understanding Levels

- **Level 0**: Super Admin (system-wide access)
- **Level 10**: Tenant Admin (tenant administration)
- **Level 20**: Manager roles (departmental management)
- **Level 30**: User roles (operational access)
- **Level 40+**: Viewer roles (read-only access)

#### Best Practices for Hierarchy

1. **Consistent Numbering**: Use increments of 10 for flexibility
2. **Clear Separation**: Distinct privilege levels between roles
3. **Parent-Child Relationships**: Logical inheritance structure
4. **Tenant Scoping**: Separate hierarchies per tenant when needed

### Modifying Roles

#### Updating Role Properties

```python
# Update role permissions and settings
role = Role.objects.get(codename='project_manager')
role.description = 'Updated role description'
role.can_delegate = True
role.max_delegations = 2
role.save()
```

#### Changing Role Hierarchy

```python
# Move role in hierarchy
child_role = Role.objects.get(name='Junior Developer')
new_parent = Role.objects.get(name='Senior Developer')

# Validate hierarchy change
if new_parent.level < child_role.level:
    child_role.parent_role = new_parent
    child_role.save()
```

### Deactivating Roles

```python
# Soft delete - preserves audit trail
role.is_active = False
role.save()

# This automatically deactivates all user assignments
```

## User Assignment

### Assigning Roles to Users

#### Single Assignment

```python
from rbac.models import UserRole
from django.contrib.auth.models import User

# Assign role to user
user = User.objects.get(username='john.doe')
role = Role.objects.get(name='Content Manager')
tenant = Tenant.objects.get(slug='acme-corp')

user_role = UserRole.objects.assign_role(
    user=user,
    role=role,
    tenant=tenant,
    assigned_by=request.user,
    reason='Promotion to content management position'
)
```

#### Bulk Assignment

```python
# Assign role to multiple users
users = User.objects.filter(department='marketing')
role = Role.objects.get(name='Marketing Specialist')

for user in users:
    UserRole.objects.assign_role(
        user=user,
        role=role,
        tenant=tenant,
        assigned_by=request.user,
        expires_at=datetime.now() + timedelta(days=365)
    )
```

#### Temporary Assignments

```python
from datetime import datetime, timedelta

# Assign temporary role (e.g., for project duration)
UserRole.objects.assign_role(
    user=user,
    role=role,
    tenant=tenant,
    assigned_by=request.user,
    expires_at=datetime.now() + timedelta(days=90),
    reason='Temporary project assignment'
)
```

### Revoking Role Assignments

```python
# Revoke specific role from user
UserRole.objects.revoke_role(
    user=user,
    role=role,
    tenant=tenant,
    revoked_by=request.user
)

# Revoke all roles from user in tenant
user_roles = UserRole.objects.filter(
    user=user,
    tenant=tenant,
    is_active=True
)
for user_role in user_roles:
    user_role.is_active = False
    user_role.save()
```

### Primary Role Management

```python
# Set primary role for user in tenant
user_role = UserRole.objects.get(user=user, role=role, tenant=tenant)
user_role.is_primary = True
user_role.save()

# Ensure only one primary role per tenant
UserRole.objects.filter(
    user=user,
    tenant=tenant,
    is_primary=True
).exclude(id=user_role.id).update(is_primary=False)
```

## Permission Management

### Assigning Permissions to Roles

#### Direct Permission Assignment

```python
from rbac.models import Permission, RolePermission

# Grant permission to role
permission = Permission.objects.get(codename='asset_create')
role = Role.objects.get(name='Content Manager')

RolePermission.objects.grant_permission(
    role=role,
    permission=permission,
    granted_by=request.user
)
```

#### Object-Level Permissions

```python
# Grant permission for specific object
asset = Asset.objects.get(id=123)

RolePermission.objects.grant_permission(
    role=role,
    permission=permission,
    granted_by=request.user,
    object_id=asset.id
)
```

#### Bulk Permission Assignment

```python
# Assign multiple permissions to role
permissions = Permission.objects.filter(category='asset')

for permission in permissions:
    RolePermission.objects.grant_permission(
        role=role,
        permission=permission,
        granted_by=request.user
    )
```

### Permission Inheritance

#### Viewing Inherited Permissions

```python
# Get all permissions including inherited
all_permissions = role.get_all_permissions()

# Separate direct vs inherited
direct_permissions = role.permissions.filter(is_active=True)
inherited_permissions = all_permissions - set(direct_permissions)
```

#### Override Inheritance

```python
# Explicitly deny inherited permission
parent_permission = RolePermission.objects.get(
    role=role.parent_role,
    permission=permission
)

# Create explicit denial
RolePermission.objects.create(
    role=role,
    permission=permission,
    is_granted=False,  # Explicit denial
    can_override=False,
    granted_by=request.user
)
```

### Time-Based Permissions

```python
from datetime import datetime, timedelta

# Grant temporary permission
RolePermission.objects.grant_permission(
    role=role,
    permission=permission,
    granted_by=request.user,
    expires_at=datetime.now() + timedelta(hours=24)
)
```

## Delegation

### Role Delegation Process

#### Checking Delegation Eligibility

```python
# Check if user can delegate role
user_role = UserRole.objects.get(user=delegator, role=role, tenant=tenant)
can_delegate = user_role.can_delegate()

# Check delegation limits
remaining_delegations = role.max_delegations - user_role.delegation_level
```

#### Performing Delegation

```python
# Delegate role to another user
delegated_role = UserRole.objects.delegate_role(
    delegator=delegator_user,
    user=delegate_to_user,
    role=role,
    tenant=tenant,
    expires_at=datetime.now() + timedelta(days=30),
    reason='Temporary delegation during vacation'
)
```

#### Managing Delegation Chains

```python
# Track delegation chain
delegation_chain = []
current_assignment = delegated_role

while current_assignment.delegated_by:
    delegation_chain.append({
        'user': current_assignment.delegated_by.username,
        'level': current_assignment.delegation_level,
        'date': current_assignment.assigned_at
    })
    # Find parent delegation
    current_assignment = UserRole.objects.filter(
        user=current_assignment.delegated_by,
        role=current_assignment.role,
        tenant=current_assignment.tenant
    ).first()
```

### Delegation Limits and Controls

#### Setting Delegation Limits

```python
# Update role delegation settings
role.can_delegate = True
role.max_delegations = 3
role.save()
```

#### Monitoring Active Delegations

```python
# Get all active delegations for a role
active_delegations = UserRole.objects.filter(
    role=role,
    delegated_by__isnull=False,
    is_active=True
)

# Count delegation levels
delegation_stats = {}
for delegation in active_delegations:
    level = delegation.delegation_level
    delegation_stats[level] = delegation_stats.get(level, 0) + 1
```

## Monitoring and Auditing

### Audit Log Analysis

#### Viewing Role Changes

```python
from rbac.models import RoleAuditLog

# Get recent role changes
recent_changes = RoleAuditLog.objects.filter(
    timestamp__gte=datetime.now() - timedelta(days=7)
).order_by('-timestamp')

# Filter by action type
role_creations = RoleAuditLog.objects.filter(
    action='role_created',
    timestamp__gte=datetime.now() - timedelta(days=30)
)
```

#### User Activity Tracking

```python
# Track user permission changes
user_changes = RoleAuditLog.objects.filter(
    target_user=user,
    action__in=['user_assigned', 'user_unassigned', 'role_delegated']
)

# Generate user activity report
activity_summary = {
    'user': user.username,
    'total_changes': user_changes.count(),
    'recent_assignments': user_changes.filter(
        action='user_assigned',
        timestamp__gte=datetime.now() - timedelta(days=7)
    ).count(),
    'delegations_given': RoleAuditLog.objects.filter(
        actor=user,
        action='role_delegated'
    ).count()
}
```

### Performance Monitoring

#### Permission Check Performance

```python
# Monitor slow permission checks
import time

def check_permission_with_timing(user, permission, tenant=None):
    start_time = time.time()
    result = user.rbac.user_has_permission(user, permission, tenant)
    duration = time.time() - start_time

    if duration > 0.1:  # Log slow checks
        logger.warning(f'Slow permission check: {duration:.3f}s for {permission}')

    return result
```

#### Role Assignment Statistics

```python
# Generate role usage statistics
role_stats = []
for role in Role.objects.filter(is_active=True):
    stats = {
        'role': role.name,
        'active_users': role.user_assignments.filter(is_active=True).count(),
        'total_permissions': role.permissions.count(),
        'inherited_permissions': len(role.get_all_permissions()) - role.permissions.count(),
        'delegation_count': role.user_assignments.filter(
            delegated_by__isnull=False,
            is_active=True
        ).count()
    }
    role_stats.append(stats)
```

## Best Practices

### Role Design Principles

1. **Principle of Least Privilege**
   - Grant minimum necessary permissions
   - Regular permission reviews
   - Time-limited access when possible

2. **Clear Role Definitions**
   - Descriptive role names
   - Comprehensive descriptions
   - Well-defined responsibilities

3. **Logical Hierarchy**
   - Consistent level numbering
   - Clear inheritance relationships
   - Minimal hierarchy depth

### Security Best Practices

1. **Regular Audits**
   ```python
   # Monthly role assignment review
   def monthly_role_audit():
       # Find users with multiple high-privilege roles
       high_privilege_users = User.objects.filter(
           user_roles__role__level__lt=20,
           user_roles__is_active=True
       ).distinct()

       # Check for orphaned roles
       orphaned_roles = Role.objects.filter(
           user_assignments__isnull=True,
           is_active=True
       )

       # Review long-term temporary assignments
       long_temp_assignments = UserRole.objects.filter(
           expires_at__lt=datetime.now() + timedelta(days=30),
           is_active=True
       )
   ```

2. **Automated Cleanup**
   ```python
   # Daily cleanup of expired assignments
   def cleanup_expired_roles():
       expired_count = UserRole.objects.cleanup_expired()
       return expired_count
   ```

3. **Permission Validation**
   ```python
   # Validate role consistency
   def validate_role_hierarchy():
       issues = []
       for role in Role.objects.filter(parent_role__isnull=False):
           if role.level <= role.parent_role.level:
               issues.append(f"Role {role.name} has invalid hierarchy level")
       return issues
   ```

### Performance Optimization

1. **Permission Caching**
   ```python
   from django.core.cache import cache

   def get_cached_user_permissions(user, tenant):
       cache_key = f"user_permissions_{user.id}_{tenant.id if tenant else 'global'}"
       permissions = cache.get(cache_key)

       if permissions is None:
           permissions = get_user_permissions(user, tenant)
           cache.set(cache_key, permissions, 300)  # 5 minutes

       return permissions
   ```

2. **Query Optimization**
   ```python
   # Efficient role queries with prefetching
   roles_with_permissions = Role.objects.filter(
       is_active=True
   ).prefetch_related(
       'permissions',
       'user_assignments__user',
       'child_roles'
   ).select_related('parent_role', 'tenant')
   ```

## Troubleshooting

### Common Issues

#### Permission Denied Errors

1. **Check User Role Assignment**
   ```python
   # Verify user has required role
   user_roles = UserRole.objects.filter(
       user=user,
       tenant=tenant,
       is_active=True
   )
   print(f"User roles: {[ur.role.name for ur in user_roles]}")
   ```

2. **Verify Permission Assignment**
   ```python
   # Check if role has required permission
   role = user_roles.first().role
   has_permission = role.has_permission('asset_create')
   print(f"Role has permission: {has_permission}")
   ```

#### Cross-Tenant Access Issues

1. **Tenant Context Validation**
   ```python
   # Ensure proper tenant context
   if not request.tenant:
       raise PermissionDenied("Tenant context required")

   # Verify user has access to tenant
   user_has_tenant_access = UserRole.objects.filter(
       user=request.user,
       tenant=request.tenant,
       is_active=True
   ).exists()
   ```

#### Delegation Problems

1. **Check Delegation Eligibility**
   ```python
   # Verify delegation capability
   user_role = UserRole.objects.get(user=user, role=role, tenant=tenant)
   can_delegate = (
       user_role.role.can_delegate and
       user_role.delegation_level < user_role.role.max_delegations and
       user_role.is_valid()
   )
   ```

### Debug Utilities

#### Permission Checker Tool

```python
def debug_permission_check(user, permission_codename, tenant=None, obj=None):
    """Debug utility for permission checking."""

    print(f"Checking permission '{permission_codename}' for user '{user.username}'")
    print(f"Tenant: {tenant.name if tenant else 'Global'}")

    # Check user roles
    user_roles = UserRole.objects.filter(
        user=user,
        tenant=tenant,
        is_active=True
    )
    print(f"Active roles: {[ur.role.name for ur in user_roles]}")

    # Check each role's permissions
    for user_role in user_roles:
        role = user_role.role
        all_permissions = role.get_all_permissions()
        matching_perms = [p for p in all_permissions if p.codename == permission_codename]

        print(f"Role '{role.name}' permissions:")
        for perm in matching_perms:
            print(f"  - {perm.name} ({perm.codename})")

    # Final result
    from rbac.permissions import RBACPermissionMixin
    rbac = RBACPermissionMixin()
    result = rbac.user_has_permission(user, permission_codename, tenant, obj)
    print(f"Final result: {'GRANTED' if result else 'DENIED'}")

    return result
```

#### Role Hierarchy Visualizer

```python
def print_role_hierarchy(tenant=None, indent=0):
    """Print role hierarchy for debugging."""

    root_roles = Role.objects.filter(
        parent_role__isnull=True,
        tenant=tenant,
        is_active=True
    )

    for role in root_roles:
        print("  " * indent + f"├── {role.name} (Level {role.level})")
        print("  " * indent + f"    Users: {role.user_assignments.filter(is_active=True).count()}")
        print("  " * indent + f"    Permissions: {role.permissions.count()}")

        # Print child roles
        child_roles = role.child_roles.filter(is_active=True)
        for child in child_roles:
            print_role_hierarchy_recursive(child, indent + 1)

def print_role_hierarchy_recursive(role, indent):
    print("  " * indent + f"├── {role.name} (Level {role.level})")
    print("  " * indent + f"    Users: {role.user_assignments.filter(is_active=True).count()}")
    print("  " * indent + f"    Permissions: {role.permissions.count()}")

    for child in role.child_roles.filter(is_active=True):
        print_role_hierarchy_recursive(child, indent + 1)
```

This comprehensive guide provides everything needed to effectively manage roles and permissions in the RBAC system. Regular reference to this guide will ensure proper implementation and maintenance of access controls.