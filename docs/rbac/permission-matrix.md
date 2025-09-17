# RBAC Permission Matrix

## Overview

This document defines the complete permission matrix for the Role-Based Access Control (RBAC) system in our multi-tenant SaaS platform. The matrix specifies what actions each role can perform across different resource categories.

## Role Hierarchy

```
Super Admin (Level 0)
    ├── Tenant Admin (Level 10)
        ├── Content Manager (Level 20)
            └── Viewer (Level 40)
```

## Permission Categories

1. **Asset Management** - Content, files, and digital assets
2. **User Management** - User accounts and profiles
3. **Tenant Settings** - Tenant configuration and preferences
4. **Billing** - Payment, subscriptions, and invoicing
5. **System Configuration** - Platform-wide settings

## Permission Actions

- **Create** - Add new resources
- **Read** - View and access resources
- **Update** - Modify existing resources
- **Delete** - Remove resources
- **Manage** - Full control including delegation

## Complete Permission Matrix

| Role | Asset Management | User Management | Tenant Settings | Billing | System Config |
|------|------------------|-----------------|-----------------|---------|---------------|
| **Super Admin** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **Tenant Admin** | ✅ Full | 🔒 Tenant Only | 🔒 Tenant Only | 🔒 Tenant Only | ❌ None |
| **Content Manager** | ✅ Create/Edit | ❌ None | ❌ None | ❌ None | ❌ None |
| **Viewer** | 📖 Read Only | ❌ None | ❌ None | ❌ None | ❌ None |

### Detailed Permissions

#### Super Admin (Level 0)
- **Scope**: System-wide
- **Asset Management**: Create, Read, Update, Delete, Manage
- **User Management**: Create, Read, Update, Delete, Manage
- **Tenant Settings**: Create, Read, Update, Delete, Manage
- **Billing**: Create, Read, Update, Delete, Manage
- **System Configuration**: Create, Read, Update, Delete, Admin
- **Special Privileges**:
  - Cross-tenant access
  - System configuration
  - User and role delegation
  - Audit log access
  - Platform administration

#### Tenant Admin (Level 10)
- **Scope**: Single tenant
- **Asset Management**: Create, Read, Update, Delete, Manage
- **User Management**: Create, Read, Update, Delete (tenant users only)
- **Tenant Settings**: Read, Update (own tenant only)
- **Billing**: Create, Read, Update, Delete (tenant billing only)
- **System Configuration**: None
- **Special Privileges**:
  - Tenant user management
  - Role assignment within tenant
  - Billing management
  - Tenant configuration

#### Content Manager (Level 20)
- **Scope**: Single tenant, content focus
- **Asset Management**: Create, Read, Update, Delete
- **User Management**: None
- **Tenant Settings**: None
- **Billing**: None
- **System Configuration**: None
- **Special Privileges**:
  - Full content management
  - Asset publishing
  - Content workflow management

#### Viewer (Level 40)
- **Scope**: Single tenant, read-only
- **Asset Management**: Read only
- **User Management**: None
- **Tenant Settings**: None
- **Billing**: None
- **System Configuration**: None
- **Special Privileges**:
  - Browse content
  - Download assets (if permitted)
  - View reports

## Permission Inheritance

Roles inherit permissions from their parent roles with the following rules:

1. **Hierarchical Inheritance**: Child roles inherit all permissions from parent roles
2. **Override Capability**: Parent roles can override inherited permissions
3. **Restriction Principle**: Child roles cannot grant permissions not available to parent
4. **Tenant Scoping**: Permissions are automatically scoped to the role's tenant context

### Inheritance Examples

```
Tenant Admin → Content Manager
├── asset_create ✅ (inherited)
├── asset_read ✅ (inherited)
├── asset_update ✅ (inherited)
├── asset_delete ✅ (inherited)
├── user_manage ❌ (restricted by child role)
└── tenant_update ❌ (restricted by child role)

Content Manager → Viewer
├── asset_read ✅ (inherited)
├── asset_create ❌ (restricted by child role)
├── asset_update ❌ (restricted by child role)
└── asset_delete ❌ (restricted by child role)
```

## Resource-Level Permissions

### Object-Level Security

Some permissions can be granted at the object level for fine-grained control:

- **Asset Permissions**: Specific assets or asset categories
- **User Permissions**: Specific user accounts or user groups
- **Tenant Permissions**: Specific tenant features or sections

### Examples

```json
{
  "role": "Content Manager",
  "permission": "asset_update",
  "object_type": "Asset",
  "object_id": 123,
  "granted": true
}
```

## Delegation Rules

### Role Delegation Capabilities

| Role | Can Delegate | Max Delegations | Delegation Scope |
|------|--------------|-----------------|------------------|
| Super Admin | ✅ Yes | 3 levels | System-wide |
| Tenant Admin | ✅ Yes | 2 levels | Tenant only |
| Content Manager | ❌ No | 0 | None |
| Viewer | ❌ No | 0 | None |

### Delegation Constraints

1. **Level Restriction**: Can only delegate to same or lower level roles
2. **Tenant Boundary**: Cannot delegate across tenant boundaries
3. **Permission Subset**: Delegated role cannot exceed delegator's permissions
4. **Time Limits**: Delegations can have expiration times
5. **Audit Trail**: All delegations are logged and tracked

## Tenant Isolation

### Multi-Tenant Security

- **Data Isolation**: Users can only access data within their assigned tenant(s)
- **Role Scoping**: Tenant-specific roles are isolated from other tenants
- **Cross-Tenant Prevention**: Automatic prevention of cross-tenant data access
- **Audit Separation**: Audit logs are tenant-scoped

### System Roles Exception

Super Admin roles have cross-tenant access for:
- Platform administration
- System maintenance
- Global reporting
- Tenant management

## Permission Validation

### Validation Rules

1. **Authentication Required**: All permissions require authenticated user
2. **Active User Check**: User account must be active
3. **Role Validity**: User roles must be active and not expired
4. **Tenant Context**: Permission checks include tenant validation
5. **Object Ownership**: Object-level permissions verify ownership

### Validation Flow

```
Request → Authentication → User Active → Role Valid → Tenant Check → Permission Check → Object Access → Allow/Deny
```

## API Endpoint Protection

### Endpoint Mapping

| Endpoint Pattern | Required Permission | Notes |
|-----------------|-------------------|--------|
| `/api/assets/*` | `asset_*` | Action-based permission |
| `/api/users/*` | `user_*` | Tenant-scoped |
| `/api/tenants/*` | `tenant_*` | Own tenant only |
| `/api/billing/*` | `billing_*` | Tenant billing only |
| `/api/system/*` | `system_*` | Super admin only |

### HTTP Method Mapping

| HTTP Method | Permission Action |
|-------------|------------------|
| GET | read |
| POST | create |
| PUT/PATCH | update |
| DELETE | delete |

## Security Considerations

### Best Practices

1. **Principle of Least Privilege**: Grant minimum necessary permissions
2. **Regular Audits**: Review role assignments and permissions regularly
3. **Time-Limited Roles**: Use expiration dates for temporary access
4. **Delegation Monitoring**: Monitor and limit role delegations
5. **Activity Logging**: Comprehensive audit trail for all actions

### Security Features

- **Permission Caching**: Reduces database queries for permission checks
- **Rate Limiting**: Prevents brute force permission enumeration
- **Anomaly Detection**: Unusual permission usage patterns
- **Secure Headers**: Security headers for API responses
- **Session Management**: Secure session handling with role context

## Migration and Versioning

### Version History

- **v1.0**: Initial RBAC implementation
- **v1.1**: Added object-level permissions
- **v1.2**: Enhanced delegation capabilities
- **v2.0**: Multi-tenant isolation

### Migration Strategy

1. **Backward Compatibility**: Maintain existing permission structure
2. **Gradual Migration**: Phase-in new permissions
3. **Data Preservation**: Preserve existing role assignments
4. **Audit Continuity**: Maintain audit log integrity

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check role assignments and tenant context
2. **Cross-Tenant Access**: Verify tenant isolation rules
3. **Delegation Failures**: Check delegation limits and hierarchy
4. **Performance Issues**: Review permission caching and queries

### Debug Tools

- Permission checker utility
- Role hierarchy visualizer
- Audit log analyzer
- Performance profiler

## API Reference

### Permission Check Endpoints

```
GET /api/rbac/check-permission/
POST /api/rbac/assign-role/
POST /api/rbac/delegate-role/
GET /api/rbac/user-summary/
```

### Response Format

```json
{
  "user": "username",
  "tenant": "tenant-name",
  "permission": "asset_read",
  "granted": true,
  "source": "direct|inherited|delegated",
  "expires_at": "2024-12-31T23:59:59Z"
}
```