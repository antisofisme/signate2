# Enhanced Asset Management System

## Overview

The Enhanced Asset Management System extends Anthias's core asset functionality with advanced features including rich metadata, versioning, sharing capabilities, and automated processing workflows. This system provides enterprise-grade asset management with multi-tenant isolation and role-based access control.

## Key Features

### 📊 Rich Metadata Management
- **Custom Fields**: Flexible metadata with tenant-specific custom fields
- **Technical Metadata**: Automatic extraction of file dimensions, duration, format details
- **Usage Analytics**: Track downloads, views, shares, and access patterns
- **Categorization**: Hierarchical categorization with tags and keywords
- **Rights Management**: Copyright information, licensing, and attribution tracking

### 🔄 Version Control
- **Asset Versioning**: Complete revision history with branching support
- **Change Tracking**: Detailed change descriptions and diff analysis
- **Version Publishing**: Control which versions are publicly available
- **Rollback Support**: Easy restoration to previous versions
- **Storage Optimization**: Efficient storage with deduplication

### 🔗 Advanced Sharing
- **Public/Private Links**: Granular sharing controls with expiration
- **Password Protection**: Secure sharing with password requirements
- **Download Limits**: Control access with download quotas
- **QR Code Generation**: Mobile-friendly sharing options
- **Social Integration**: One-click sharing to social platforms
- **Embed Codes**: Rich embed options for websites and applications

### 🔄 Background Processing
- **Thumbnail Generation**: Automatic preview generation for all file types
- **Metadata Extraction**: Comprehensive file analysis and indexing
- **Virus Scanning**: Integrated security scanning with ClamAV
- **Format Conversion**: Automatic format optimization and conversion
- **Compression**: Intelligent file size optimization

### 📋 Approval Workflows
- **Configurable Workflows**: Custom approval chains per content type
- **Automated Rules**: Smart auto-approval based on conditions
- **Moderation System**: Content flagging and review processes
- **Escalation Support**: Automatic escalation for overdue approvals
- **Audit Trail**: Complete history of all approval actions

## Architecture

### Database Models

#### Enhanced Asset Models
```python
# Core metadata enhancement
AssetMetadata          # Rich metadata with custom fields
AssetVersion          # Version control and revision history
AssetTag              # Flexible tagging system
AssetTagging          # Many-to-many tag relationships
AssetRelationship     # Asset dependencies and relationships

# Sharing and collaboration
ShareLink             # Public/private sharing with permissions
AssetComment          # Collaborative comments and annotations
AssetAnalytics        # Detailed usage analytics

# Processing and workflows
ProcessingJob         # Background processing tasks
```

#### Workflow Models
```python
WorkflowTemplate      # Configurable approval workflow templates
WorkflowInstance      # Active workflow instances
WorkflowAssignment    # User assignments for approval steps
WorkflowApproval      # Approval actions and decisions
ContentModerationRule # Automated content moderation rules
ModerationFlag        # Content flagged for review
```

### API Endpoints

#### Asset Management
```
GET    /api/v3/assets/                    # List assets with advanced filtering
POST   /api/v3/assets/upload/             # Enhanced file upload
GET    /api/v3/assets/{id}/               # Detailed asset information
POST   /api/v3/assets/{id}/upload_version/ # Upload new version
GET    /api/v3/assets/{id}/download/      # Download with analytics
POST   /api/v3/assets/{id}/share/         # Create share links
GET    /api/v3/assets/{id}/qr_code/       # Generate QR code
GET    /api/v3/assets/{id}/analytics/     # Detailed analytics
GET    /api/v3/assets/{id}/comments/      # Comments and annotations
```

#### Metadata Management
```
GET    /api/v3/metadata/{id}/             # Asset metadata
PUT    /api/v3/metadata/{id}/             # Update metadata
POST   /api/v3/metadata/{id}/bulk_update/ # Bulk custom fields update
```

#### Sharing and Collaboration
```
GET    /api/v3/shares/                    # List user's share links
POST   /api/v3/shares/                    # Create share link
GET    /api/v3/shares/{uuid}/             # Access shared content
POST   /api/v3/shares/{uuid}/regenerate/  # Regenerate share UUID
GET    /share/{uuid}/                     # Public share access (no auth)
```

#### Processing and Workflows
```
GET    /api/v3/processing/{id}/status/    # Processing job status
POST   /api/v3/workflows/                 # Create workflow
GET    /api/v3/workflows/{id}/            # Workflow details
POST   /api/v3/workflows/{id}/approve/    # Submit approval
```

## Usage Guide

### Setting Up Asset Upload

```python
from project.backend.serializers.asset_serializers import AssetUploadSerializer

# Enhanced upload with metadata
upload_data = {
    'file': uploaded_file,
    'title': 'Marketing Video Q1 2024',
    'description': 'Quarterly marketing campaign video',
    'category': 'marketing',
    'tags': ['q1', '2024', 'campaign'],
    'custom_fields': {
        'department': 'Marketing',
        'budget_code': 'MKT-2024-Q1',
        'target_audience': 'B2B Enterprise'
    },
    'generate_thumbnail': True,
    'extract_metadata': True,
    'virus_scan': True
}

serializer = AssetUploadSerializer(data=upload_data, context={'request': request})
if serializer.is_valid():
    asset = serializer.save()
```

### Creating Share Links

```python
from project.backend.utils.content_sharing import ContentSharingService

# Create advanced share link
share_config = {
    'share_type': 'protected',  # public, private, protected
    'password': 'secure123',
    'allow_download': True,
    'allow_preview': True,
    'allow_comments': True,
    'expires_in_hours': 168,  # 1 week
    'max_downloads': 50,
    'title': 'Q1 Marketing Campaign Preview',
    'description': 'Preview of our Q1 campaign materials'
}

share_data = ContentSharingService.create_share_link(
    asset, request.user, share_config
)

# Returns: share_link, qr_code, social_links, embed_code, short_url
```

### Setting Up Approval Workflows

```python
from project.backend.workflows.approval_workflows import WorkflowTemplate

# Create workflow template
template = WorkflowTemplate.objects.create(
    name='Marketing Content Approval',
    description='Approval workflow for marketing materials',
    content_type=ContentType.objects.get_for_model(Asset),
    steps=[
        {
            'id': 'manager_review',
            'name': 'Manager Review',
            'approvers': {
                'type': 'roles',
                'roles': ['Marketing Manager']
            },
            'requires_all': False
        },
        {
            'id': 'legal_review',
            'name': 'Legal Review',
            'approvers': {
                'type': 'roles',
                'roles': ['Legal Team']
            },
            'requires_all': True
        }
    ],
    auto_approve_conditions={
        'file_size_limit': 10 * 1024 * 1024,  # 10MB
        'trusted_uploaders': [1, 2, 3],
        'safe_mime_types': ['image/jpeg', 'image/png']
    }
)
```

### Background Processing

```python
from project.backend.tasks.asset_processing import process_asset_upload

# Queue processing for uploaded asset
processing_options = {
    'extract_metadata': True,
    'generate_thumbnail': True,
    'virus_scan': True,
    'create_workflow': True
}

# Asynchronous processing
task = process_asset_upload.delay(asset.asset_id, processing_options)

# Check status
result = task.get()  # Blocks until complete
# Or check async: task.ready(), task.result
```

## Configuration

### Settings Configuration

```python
# settings.py

# Asset processing settings
ASSET_PROCESSING = {
    'THUMBNAIL_SIZES': {
        'small': (150, 150),
        'medium': (300, 300),
        'large': (600, 600)
    },
    'MAX_FILE_SIZE': 100 * 1024 * 1024,  # 100MB
    'ALLOWED_MIME_TYPES': [
        'image/jpeg', 'image/png', 'image/gif',
        'video/mp4', 'video/avi', 'video/mov',
        'audio/mp3', 'audio/wav', 'audio/ogg',
        'application/pdf', 'text/plain'
    ],
    'VIRUS_SCAN_ENABLED': True,
    'AUTO_GENERATE_THUMBNAILS': True
}

# Sharing settings
CONTENT_SHARING = {
    'DEFAULT_EXPIRY_HOURS': 168,  # 1 week
    'MAX_DOWNLOAD_LIMIT': 1000,
    'ENABLE_SOCIAL_SHARING': True,
    'QR_CODE_SIZE': (200, 200),
    'SHORT_URL_LENGTH': 8
}

# Workflow settings
APPROVAL_WORKFLOWS = {
    'AUTO_CREATE_WORKFLOWS': True,
    'DEFAULT_TIMEOUT_HOURS': 72,
    'ESCALATION_ENABLED': True,
    'EMAIL_NOTIFICATIONS': True
}

# Celery settings for background processing
CELERY_TASK_ROUTES = {
    'project.backend.tasks.asset_processing.*': {'queue': 'asset_processing'},
}
```

### Permissions Setup

```python
# Custom permission class
class TenantAssetPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Tenant isolation
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.profile.tenant

        # Role-based permissions
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return request.user.has_perm('assets.change_asset')

        return request.user.has_perm('assets.view_asset')
```

## Monitoring and Analytics

### Processing Job Monitoring

```python
from project.backend.models.enhanced_asset_models import ProcessingJob

# Monitor processing status
pending_jobs = ProcessingJob.objects.filter(status='pending').count()
failed_jobs = ProcessingJob.objects.filter(status='failed').count()

# Get processing statistics
stats = ProcessingJob.objects.values('job_type', 'status').annotate(
    count=Count('id')
).order_by('job_type', 'status')
```

### Analytics Dashboard

```python
from project.backend.utils.content_sharing import ContentSharingService

# Generate sharing analytics
analytics = ContentSharingService.generate_sharing_analytics(
    share_link, date_range=30
)

# Returns comprehensive metrics:
# - View/download counts
# - Geographic breakdown
# - Device/browser stats
# - Referrer analysis
# - Daily trends
```

### Workflow Metrics

```python
from project.backend.workflows.approval_workflows import WorkflowService

# Get workflow statistics
stats = WorkflowService.get_workflow_statistics(date_range=30)

# Returns:
# - Total workflows by status
# - Average completion time
# - Pending approval counts
# - Bottleneck analysis
```

## Best Practices

### Security Considerations

1. **Virus Scanning**: Always enable virus scanning for uploads
2. **Access Control**: Implement proper tenant isolation
3. **Share Link Security**: Use strong UUIDs and expiration
4. **File Validation**: Validate file types and sizes
5. **Audit Logging**: Track all access and modifications

### Performance Optimization

1. **Async Processing**: Use background tasks for heavy operations
2. **Caching**: Cache metadata and thumbnails
3. **CDN Integration**: Serve static assets from CDN
4. **Database Indexing**: Proper indexing on search fields
5. **Pagination**: Use pagination for large asset lists

### Scalability Guidelines

1. **Storage Strategy**: Use object storage for production
2. **Queue Management**: Monitor Celery queues
3. **Resource Limits**: Set appropriate file size limits
4. **Cleanup Jobs**: Regular cleanup of old data
5. **Monitoring**: Comprehensive system monitoring

## Troubleshooting

### Common Issues

#### Processing Jobs Stuck
```bash
# Check Celery workers
celery -A project worker --loglevel=info

# Monitor queue status
celery -A project inspect active
```

#### Virus Scan Failures
```bash
# Install/update ClamAV
sudo apt-get install clamav clamav-daemon
sudo freshclam
```

#### Thumbnail Generation Issues
```bash
# Install required packages
sudo apt-get install imagemagick ffmpeg
pip install Pillow ffmpeg-python
```

### Debugging Tips

1. **Enable Debug Logging**: Set detailed logging for processing
2. **Check File Permissions**: Ensure proper file system permissions
3. **Monitor Memory Usage**: Track memory consumption during processing
4. **Validate Dependencies**: Check all required system packages
5. **Test Workflows**: Use simple test cases to validate setup

## Migration Guide

### From Basic Anthias Assets

1. **Run Migrations**: Apply new database migrations
2. **Create Metadata**: Backfill metadata for existing assets
3. **Setup Processing**: Configure background processing
4. **Define Workflows**: Create initial workflow templates
5. **Test Integration**: Validate all functionality

### Data Migration Script

```python
# management/commands/migrate_enhanced_assets.py
from django.core.management.base import BaseCommand
from anthias.apps.assets.models import Asset
from project.backend.models.enhanced_asset_models import AssetMetadata

class Command(BaseCommand):
    def handle(self, *args, **options):
        for asset in Asset.objects.all():
            metadata, created = AssetMetadata.objects.get_or_create(
                asset=asset,
                defaults={
                    'title': asset.name,
                    'file_size': getattr(asset.uri, 'size', 0),
                    'processing_status': 'completed'
                }
            )
            if created:
                self.stdout.write(f'Created metadata for {asset.name}')
```

This enhanced asset management system provides a comprehensive foundation for enterprise-grade content management while maintaining compatibility with existing Anthias functionality.