# User Invitation System

## Overview

The User Invitation System provides a comprehensive solution for inviting users to join tenants with specific roles and permissions. It supports individual invitations, bulk invitations, customizable templates, and complete invitation lifecycle management.

## Core Components

### UserInvitation Model

The primary model for managing user invitations:

```python
class UserInvitation(models.Model):
    tenant = ForeignKey(Tenant)
    email = EmailField()
    role = ForeignKey(Role)
    invited_by = ForeignKey(User)
    token = CharField(max_length=128, unique=True)
    status = CharField(choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('resent', 'Resent'),
    ])
    message = TextField(blank=True)
    expires_at = DateTimeField()
    accepted_at = DateTimeField(null=True)
    email_sent_at = DateTimeField(null=True)
    reminder_sent_at = DateTimeField(null=True)
    reminder_count = IntegerField(default=0)
```

### Key Features

- **Secure Tokens**: Cryptographically secure invitation tokens
- **Expiration Management**: Configurable invitation expiry periods
- **Status Tracking**: Complete invitation lifecycle tracking
- **Reminder System**: Automated and manual reminder capabilities
- **Pre-filled Registration**: User data pre-population for registration

## Invitation Workflow

### 1. Creating Invitations

#### Single Invitation

```python
from backend.models.invitation_models import UserInvitation
from backend.utils.invitation_utils import send_invitation_email

invitation = UserInvitation.objects.create(
    tenant=tenant_instance,
    email='user@example.com',
    role=role_instance,
    invited_by=request.user,
    message='Welcome to our team!',
    first_name='John',
    last_name='Doe',
    department='Engineering'
)

# Send invitation email
if send_invitation_email(invitation):
    invitation.mark_sent()
```

#### API Creation

```python
# POST /api/invitations/
{
    "email": "user@example.com",
    "role": "role_id",
    "message": "Welcome to our team!",
    "first_name": "John",
    "last_name": "Doe",
    "department": "Engineering",
    "job_title": "Software Engineer"
}
```

### 2. Invitation Acceptance

#### Frontend Flow

```javascript
// Accept invitation endpoint
POST /api/invitations/accept/
{
    "token": "invitation_token_here",
    "user_data": {
        "username": "johndoe",
        "password": "secure_password",
        "password_confirm": "secure_password",
        "first_name": "John",
        "last_name": "Doe",
        "gdpr_consent": true
    }
}
```

#### Backend Processing

```python
def accept_invitation(token, user_data=None):
    invitation = UserInvitation.objects.get(token=token)

    if not invitation.is_valid():
        raise ValidationError("Invalid or expired invitation")

    # Check if user exists
    try:
        user = User.objects.get(email=invitation.email)
        # Existing user - just accept invitation
        membership = invitation.accept(user)
    except User.DoesNotExist:
        # New user - create account with invitation
        user_serializer = UserRegistrationSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        membership = invitation.accept(user)

    return user, membership
```

### 3. Invitation Management

#### Resending Invitations

```python
# Resend with new expiry
invitation.resend(new_expiry_days=7)
send_invitation_email(invitation)
invitation.mark_sent()

# API endpoint
POST /api/invitations/{id}/resend/
```

#### Cancelling Invitations

```python
invitation.cancel()

# API endpoint
POST /api/invitations/{id}/cancel/
```

#### Extending Expiry

```python
invitation.extend_expiry(days=7)
```

## Bulk Invitation System

### BulkInvitation Model

For processing large numbers of invitations:

```python
class BulkInvitation(models.Model):
    tenant = ForeignKey(Tenant)
    created_by = ForeignKey(User)
    name = CharField(max_length=200)
    description = TextField()
    default_role = ForeignKey(Role)
    default_message = TextField()
    status = CharField(choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partially_completed', 'Partially Completed'),
    ])
    total_count = IntegerField(default=0)
    success_count = IntegerField(default=0)
    failed_count = IntegerField(default=0)
    invitation_file = FileField(upload_to='bulk_invitations/')
    error_log = JSONField(default=list)
```

### CSV File Format

```csv
email,first_name,last_name,role,department,job_title,message
john@example.com,John,Doe,member,Engineering,Developer,Welcome to the team
jane@example.com,Jane,Smith,admin,HR,Manager,
```

### Processing Bulk Invitations

```python
from backend.utils.invitation_utils import process_bulk_invitations

# Create bulk invitation
bulk_invitation = BulkInvitation.objects.create(
    tenant=tenant,
    created_by=request.user,
    name='Q1 2024 New Hires',
    default_role=member_role,
    invitation_file=uploaded_file
)

# Process asynchronously
process_bulk_invitations.delay(bulk_invitation.id)
```

### API Usage

```python
# Create bulk invitation
POST /api/invitations/bulk-invite/
Content-Type: multipart/form-data

{
    "name": "Q1 2024 New Hires",
    "description": "Bulk invitation for new employees",
    "default_role": "role_id",
    "default_message": "Welcome to our company!",
    "invitation_file": file_upload
}
```

## Invitation Templates

### InvitationTemplate Model

Reusable templates for consistent invitations:

```python
class InvitationTemplate(models.Model):
    tenant = ForeignKey(Tenant)
    name = CharField(max_length=200)
    description = TextField()
    subject = CharField(max_length=255)
    message = TextField()
    default_role = ForeignKey(Role, null=True)
    expiry_days = IntegerField(default=7)
    usage_count = IntegerField(default=0)
    is_active = BooleanField(default=True)
```

### Template Variables

Templates support dynamic content through variables:

- `{{tenant_name}}` - Name of the tenant
- `{{inviter_name}}` - Name of the person sending invitation
- `{{role_name}}` - Name of the role being assigned
- `{{expiry_date}}` - Invitation expiry date
- `{{custom_message}}` - Custom message from inviter

### Template Usage

```python
from backend.utils.invitation_utils import create_invitation_from_template

template = InvitationTemplate.objects.get(name='New Employee Welcome')
invitation = create_invitation_from_template(
    template=template,
    email='user@example.com',
    invited_by=request.user,
    custom_message='Looking forward to working with you!'
)
```

## Email System Integration

### Email Templates

#### Default Invitation Email

```html
<!-- templates/emails/invitation.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Invitation to {{ tenant.name }}</title>
</head>
<body>
    <h1>You're Invited to Join {{ tenant.name }}</h1>

    <p>Hi{% if invitation.first_name %} {{ invitation.first_name }}{% endif %},</p>

    <p>{{ inviter.get_full_name }} has invited you to join {{ tenant.name }} as a {{ role.name }}.</p>

    {% if invitation.message %}
    <blockquote>{{ invitation.message }}</blockquote>
    {% endif %}

    <p>
        <a href="{{ invitation_url }}" style="background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Accept Invitation
        </a>
    </p>

    <p><small>This invitation expires on {{ expiry_date|date:"F j, Y" }}.</small></p>

    <p>If you have any questions, please contact {{ support_email }}.</p>
</body>
</html>
```

#### Reminder Email

```html
<!-- templates/emails/invitation_reminder.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Reminder: Invitation to {{ tenant.name }}</title>
</head>
<body>
    <h1>Reminder: You're Invited to Join {{ tenant.name }}</h1>

    <p>This is a friendly reminder that you have a pending invitation to join {{ tenant.name }}.</p>

    <p>Your invitation expires on {{ expiry_date|date:"F j, Y" }}.</p>

    <p>
        <a href="{{ invitation_url }}">Accept Invitation</a>
    </p>
</body>
</html>
```

### Email Configuration

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@yourcompany.com'

# Invitation-specific settings
INVITATION_EXPIRY_DAYS = 7
INVITATION_TOKEN_LENGTH = 64
SITE_NAME = 'Your Platform'
FRONTEND_URL = 'https://yourapp.com'
SUPPORT_EMAIL = 'support@yourcompany.com'
```

## Security Features

### Token Security

- **Cryptographically Secure**: Uses `secrets` module for token generation
- **Unique Tokens**: Database-level uniqueness constraint
- **Expiration**: Automatic expiry with configurable duration
- **Single Use**: Tokens are invalidated after acceptance

### Email Validation

```python
from django.core.validators import EmailValidator

def validate_invitation_email(email):
    validator = EmailValidator()
    validator(email)

    # Check if user already exists in tenant
    if User.objects.filter(
        email=email,
        user_tenant_memberships__tenant=tenant,
        user_tenant_memberships__is_active=True
    ).exists():
        raise ValidationError(f"User {email} is already a member")
```

### Rate Limiting

```python
# Implement rate limiting for invitation sending
from django.core.cache import cache

def check_invitation_rate_limit(inviter, email):
    key = f"invite_rate_{inviter.id}_{email}"
    if cache.get(key):
        raise ValidationError("Too many invitations sent to this email")

    cache.set(key, True, timeout=3600)  # 1 hour cooldown
```

## Analytics and Reporting

### Invitation Analytics

```python
from backend.utils.invitation_utils import get_invitation_analytics

analytics = get_invitation_analytics(
    tenant=tenant,
    start_date=start_date,
    end_date=end_date
)

# Returns:
{
    'total_invitations': 150,
    'pending_invitations': 25,
    'accepted_invitations': 100,
    'expired_invitations': 20,
    'cancelled_invitations': 5,
    'acceptance_rate': 80.0,
    'top_inviters': [...],
    'invitations_by_role': [...]
}
```

### API Analytics Endpoint

```python
# GET /api/invitations/analytics/
{
    "start_date": "2024-01-01",
    "end_date": "2024-03-31"
}
```

## Automated Cleanup

### Expired Invitations Cleanup

```python
from backend.utils.invitation_utils import cleanup_expired_invitations

# Run via cron job or task scheduler
cleanup_count = cleanup_expired_invitations()
```

### Celery Task Configuration

```python
# tasks.py
from celery import shared_task
from backend.utils.invitation_utils import cleanup_expired_invitations

@shared_task
def cleanup_expired_invitations_task():
    return cleanup_expired_invitations()

# Periodic task configuration
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-invitations': {
        'task': 'backend.tasks.cleanup_expired_invitations_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

## API Reference

### Invitation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/invitations/` | List invitations |
| POST | `/api/invitations/` | Create invitation |
| GET | `/api/invitations/{id}/` | Get invitation details |
| PUT | `/api/invitations/{id}/` | Update invitation |
| DELETE | `/api/invitations/{id}/` | Cancel invitation |
| POST | `/api/invitations/{id}/resend/` | Resend invitation |
| POST | `/api/invitations/accept/` | Accept invitation |
| POST | `/api/invitations/bulk-invite/` | Create bulk invitation |

### Request/Response Examples

#### Create Invitation

```json
POST /api/invitations/
{
    "email": "user@example.com",
    "role": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Welcome to our team!",
    "first_name": "John",
    "last_name": "Doe",
    "department": "Engineering",
    "job_title": "Software Engineer"
}

Response:
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "email": "user@example.com",
    "status": "pending",
    "role_name": "Member",
    "tenant_name": "Acme Corp",
    "invited_by_name": "Admin User",
    "expires_at": "2024-01-15T12:00:00Z",
    "is_valid": true,
    "created_at": "2024-01-08T12:00:00Z"
}
```

#### Accept Invitation

```json
POST /api/invitations/accept/
{
    "token": "abc123def456ghi789jkl012mno345pqr",
    "user_data": {
        "username": "johndoe",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!",
        "first_name": "John",
        "last_name": "Doe",
        "gdpr_consent": true
    }
}

Response:
{
    "message": "Invitation accepted successfully",
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "email": "user@example.com",
        "username": "johndoe",
        "full_name": "John Doe"
    },
    "membership": {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "tenant_name": "Acme Corp",
        "role_name": "Member",
        "is_primary": true
    }
}
```

## Best Practices

### Invitation Management

1. **Set appropriate expiry periods** (7-14 days recommended)
2. **Use meaningful invitation messages** to provide context
3. **Monitor acceptance rates** to improve invitation content
4. **Clean up expired invitations** regularly
5. **Implement rate limiting** to prevent spam

### Bulk Invitations

1. **Validate file format** before processing
2. **Use asynchronous processing** for large files
3. **Provide detailed error reports** for failed invitations
4. **Implement progress tracking** for long-running operations
5. **Set reasonable batch sizes** to avoid timeouts

### Security

1. **Use HTTPS** for all invitation URLs
2. **Implement CSRF protection** on acceptance endpoints
3. **Validate email formats** strictly
4. **Monitor for suspicious activity** (mass invitations, etc.)
5. **Log all invitation operations** for audit trails

### User Experience

1. **Provide clear invitation emails** with next steps
2. **Handle edge cases gracefully** (expired tokens, existing users)
3. **Offer invitation resending** capabilities
4. **Pre-fill registration forms** with invitation data
5. **Provide status updates** for bulk operations

## Troubleshooting

### Common Issues

#### 1. Invitation Not Received

```python
# Check invitation status
invitation = UserInvitation.objects.get(email='user@example.com')
print(f"Status: {invitation.status}")
print(f"Email sent: {invitation.email_sent_at}")
print(f"Expires: {invitation.expires_at}")
```

#### 2. Token Invalid Error

```python
# Verify token and status
try:
    invitation = UserInvitation.objects.get(token=token)
    print(f"Valid: {invitation.is_valid()}")
    print(f"Expired: {invitation.is_expired()}")
    print(f"Status: {invitation.status}")
except UserInvitation.DoesNotExist:
    print("Token not found")
```

#### 3. Bulk Processing Stuck

```python
# Check bulk invitation status
bulk_inv = BulkInvitation.objects.get(id=bulk_id)
print(f"Status: {bulk_inv.status}")
print(f"Progress: {bulk_inv.success_count}/{bulk_inv.total_count}")
print(f"Errors: {bulk_inv.error_log}")
```

### Debugging Tools

#### Check Invitation Pipeline

```python
from backend.utils.invitation_utils import send_invitation_email

# Test email sending
invitation = UserInvitation.objects.get(id=invitation_id)
success = send_invitation_email(invitation)
print(f"Email sent: {success}")
```

#### Validate File Format

```python
from backend.utils.invitation_utils import validate_bulk_invitation_file

validation = validate_bulk_invitation_file(uploaded_file)
print(f"Valid: {validation['valid']}")
print(f"Errors: {validation['errors']}")
print(f"Warnings: {validation['warnings']}")
```

## Integration Examples

### With Frontend Framework (React)

```javascript
// InvitationAcceptance.jsx
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';

function InvitationAcceptance() {
    const { token } = useParams();
    const [formData, setFormData] = useState({
        username: '',
        password: '',
        password_confirm: '',
        first_name: '',
        last_name: '',
        gdpr_consent: false
    });

    const handleAccept = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch('/api/invitations/accept/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    token: token,
                    user_data: formData
                })
            });

            if (response.ok) {
                // Handle success
                window.location.href = '/dashboard';
            } else {
                // Handle error
                const error = await response.json();
                console.error('Acceptance failed:', error);
            }
        } catch (error) {
            console.error('Network error:', error);
        }
    };

    return (
        <form onSubmit={handleAccept}>
            {/* Form fields */}
        </form>
    );
}
```

### With Email Templates

```python
# Custom email template context
def send_custom_invitation(invitation, template_name='custom_invitation'):
    context = {
        'invitation': invitation,
        'company_logo': 'https://yoursite.com/logo.png',
        'company_color': '#007cba',
        'welcome_video_url': 'https://yoursite.com/welcome',
        'team_members': invitation.tenant.get_team_members(),
        'benefits': ['Health Insurance', 'Flexible Hours', 'Remote Work'],
    }

    html_message = render_to_string(f'emails/{template_name}.html', context)
    send_mail(
        subject=f'Welcome to {invitation.tenant.name}!',
        message=strip_tags(html_message),
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email]
    )
```