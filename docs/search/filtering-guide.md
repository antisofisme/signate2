# Advanced Filtering & Metadata Guide

## Overview

This guide covers the comprehensive filtering system and metadata management capabilities of the search platform, including faceted search, custom metadata fields, and hierarchical tagging.

## Filtering System

### Filter Types

#### 1. File Type Filtering

Filter assets by file type or category:

```python
# Exact file types
filters = {
    'file_type': ['pdf', 'doc', 'docx', 'txt']
}

# File categories
filters = {
    'file_type': ['images', 'documents', 'videos']
}
```

**Supported Categories:**
- `images`: jpg, jpeg, png, gif, bmp, svg, webp
- `videos`: mp4, avi, mov, wmv, flv, webm, mkv
- `audio`: mp3, wav, flac, aac, ogg, wma
- `documents`: pdf, doc, docx, txt, rtf, odt
- `spreadsheets`: xls, xlsx, csv, ods
- `presentations`: ppt, pptx, odp

#### 2. File Size Filtering

Filter by file size ranges:

```python
# Byte ranges
filters = {
    'file_size': {
        'min': 1024,        # 1 KB minimum
        'max': 10485760     # 10 MB maximum
    }
}

# Predefined size categories
filters = {
    'file_size': 'medium'  # Options: small, medium, large, huge
}
```

**Size Categories:**
- `small`: < 1 MB
- `medium`: 1 MB - 10 MB
- `large`: 10 MB - 100 MB
- `huge`: > 100 MB

#### 3. Date Range Filtering

Filter by creation or modification dates:

```python
# Absolute date ranges
filters = {
    'date_range': {
        'start': '2024-01-01',
        'end': '2024-12-31'
    }
}

# Predefined date ranges
filters = {
    'date_range': 'last_30_days'
}

# Separate creation/modification dates
filters = {
    'created_date': 'this_week',
    'modified_date': {'start': '2024-06-01'}
}
```

**Predefined Ranges:**
- `today`: Today only
- `yesterday`: Previous day
- `this_week`: Current week
- `last_week`: Previous week
- `this_month`: Current month
- `last_month`: Previous month
- `this_year`: Current year
- `last_7_days`: Past 7 days
- `last_30_days`: Past 30 days
- `last_90_days`: Past 90 days

#### 4. Tag-Based Filtering

Filter by tags with hierarchical support:

```python
# Simple tag filtering
filters = {
    'tags': ['important', 'urgent', 'project-alpha']
}

# Hierarchical tags
filters = {
    'tags': ['projects.alpha.milestone-1']
}

# Tag IDs for exact matching
filters = {
    'tags': [123, 456, 789]
}
```

#### 5. Metadata Filtering

Filter by custom metadata fields:

```python
# Exact matches
filters = {
    'metadata': {
        'department': 'finance',
        'status': 'approved',
        'priority': 'high'
    }
}

# Range filtering for numeric metadata
filters = {
    'metadata': {
        'budget': {
            'min': 1000,
            'max': 50000
        },
        'duration': {
            'min': 30  # minimum value only
        }
    }
}

# Multiple values (OR condition)
filters = {
    'metadata': {
        'category': ['budget', 'forecast', 'report']
    }
}

# Pattern matching
filters = {
    'metadata': {
        'title': {
            'pattern': '.*quarterly.*',
            'case_sensitive': False
        }
    }
}
```

#### 6. User Filtering

Filter by the user who uploaded the asset:

```python
# By user ID
filters = {
    'user': 123
}

# By username
filters = {
    'user': 'john.doe'
}

# Multiple users
filters = {
    'user': [123, 456, 'jane.smith']
}
```

#### 7. Custom Advanced Filtering

Build complex filters with the Advanced Filter Builder:

```python
from backend.search.filters import AdvancedFilterBuilder

builder = AdvancedFilterBuilder()
q_object = builder \
    .add_filter('name', 'contains', 'report') \
    .add_range_filter('file_size', min_value=1024, max_value=1048576) \
    .add_in_filter('file_type', ['pdf', 'doc']) \
    .build()

# Apply to queryset
filtered_assets = Asset.objects.filter(q_object)
```

### Filter Operations

#### Combining Filters

Filters are combined using AND logic by default:

```python
filters = {
    'file_type': ['pdf'],           # AND
    'date_range': 'last_30_days',   # AND
    'tags': ['important']           # AND
}
```

#### Custom Filter Logic

For more complex logic, use custom filters:

```python
filters = {
    'custom': {
        'field': 'name',
        'operation': 'contains',
        'value': 'financial'
    }
}
```

**Supported Operations:**
- `equals`: Exact match
- `contains`: Substring match (case-insensitive)
- `starts_with`: Prefix match
- `ends_with`: Suffix match
- `greater_than`: Numeric comparison
- `less_than`: Numeric comparison
- `in`: Value in list
- `not_equals`: Exclusion

## Faceted Search

### Understanding Facets

Facets provide dynamic filter options based on current search results:

```python
from backend.search.filters import SearchFilterManager

filter_manager = SearchFilterManager()
facets = filter_manager.get_facets(queryset, applied_filters)
```

### Facet Types

#### 1. File Type Facets

```json
{
    "file_types": [
        {
            "value": "pdf",
            "count": 245,
            "label": "PDF Documents"
        },
        {
            "value": "doc",
            "count": 123,
            "label": "Word Documents"
        }
    ]
}
```

#### 2. Size Range Facets

```json
{
    "file_sizes": [
        {
            "label": "Small (< 1MB)",
            "value": {"min": 0, "max": 1048576},
            "count": 89
        },
        {
            "label": "Medium (1MB - 10MB)",
            "value": {"min": 1048576, "max": 10485760},
            "count": 156
        }
    ]
}
```

#### 3. Date Range Facets

```json
{
    "date_ranges": [
        {
            "label": "Today",
            "value": "today",
            "count": 23
        },
        {
            "label": "Last 7 days",
            "value": "last_7_days",
            "count": 145
        }
    ]
}
```

#### 4. Tag Facets

```json
{
    "tags": [
        {
            "value": "important",
            "count": 89
        },
        {
            "value": "urgent",
            "count": 56
        }
    ]
}
```

#### 5. User Facets

```json
{
    "users": [
        {
            "value": "john.doe",
            "count": 34
        },
        {
            "value": "jane.smith",
            "count": 28
        }
    ]
}
```

#### 6. Metadata Facets

```json
{
    "metadata": [
        {
            "field": "department",
            "values": [
                {"value": "finance", "count": 67},
                {"value": "hr", "count": 45}
            ]
        },
        {
            "field": "status",
            "values": [
                {"value": "active", "count": 234},
                {"value": "archived", "count": 89}
            ]
        }
    ]
}
```

### Using Facets in UI

```javascript
// Example React component
function SearchFacets({ facets, onFilterChange }) {
    return (
        <div className="search-facets">
            {/* File Type Facets */}
            <div className="facet-group">
                <h3>File Types</h3>
                {facets.file_types?.map(facet => (
                    <label key={facet.value}>
                        <input
                            type="checkbox"
                            onChange={() => onFilterChange('file_type', facet.value)}
                        />
                        {facet.label} ({facet.count})
                    </label>
                ))}
            </div>

            {/* Tag Facets */}
            <div className="facet-group">
                <h3>Tags</h3>
                {facets.tags?.map(facet => (
                    <label key={facet.value}>
                        <input
                            type="checkbox"
                            onChange={() => onFilterChange('tags', facet.value)}
                        />
                        {facet.value} ({facet.count})
                    </label>
                ))}
            </div>
        </div>
    );
}
```

## Metadata Management

### Metadata Templates

Define structured metadata schemas for different asset types:

```python
from backend.models.metadata_models import MetadataTemplate

# Create template for financial documents
template = MetadataTemplate.objects.create(
    tenant=tenant,
    name='Financial Documents',
    description='Template for budget and financial reports',
    asset_types=['pdf', 'xlsx', 'doc'],
    schema={
        'fields': [
            {
                'name': 'budget_amount',
                'type': 'number',
                'label': 'Budget Amount',
                'required': True,
                'validation': {
                    'min': 0,
                    'max': 1000000
                },
                'help_text': 'Total budget amount in USD'
            },
            {
                'name': 'department',
                'type': 'select',
                'label': 'Department',
                'required': True,
                'options': ['finance', 'hr', 'it', 'marketing'],
                'help_text': 'Responsible department'
            },
            {
                'name': 'approval_date',
                'type': 'date',
                'label': 'Approval Date',
                'required': False,
                'help_text': 'Date when budget was approved'
            },
            {
                'name': 'confidential',
                'type': 'boolean',
                'label': 'Confidential',
                'default': False,
                'help_text': 'Mark as confidential document'
            },
            {
                'name': 'tags',
                'type': 'multiselect',
                'label': 'Document Tags',
                'options': ['quarterly', 'annual', 'forecast', 'actual'],
                'required': False
            }
        ]
    }
)
```

### Field Types

#### Basic Types

- **text**: Free-form text input
- **number**: Numeric values with validation
- **date**: Date picker
- **datetime**: Date and time picker
- **boolean**: Checkbox for true/false values
- **url**: URL validation
- **email**: Email address validation

#### Selection Types

- **select**: Single choice from predefined options
- **multiselect**: Multiple choices from predefined options
- **tags**: Tag selection with autocomplete

#### Advanced Types

- **json**: Structured JSON data
- **file**: File reference or upload

### Validation Rules

```python
{
    'name': 'price',
    'type': 'number',
    'validation': {
        'min': 0,
        'max': 999999.99,
        'decimal_places': 2
    }
}

{
    'name': 'title',
    'type': 'text',
    'validation': {
        'min_length': 5,
        'max_length': 200,
        'pattern': '^[A-Za-z0-9\\s]+$'
    }
}

{
    'name': 'email',
    'type': 'email',
    'validation': {
        'required': True,
        'unique': True
    }
}
```

### Custom Metadata Fields

Add metadata to assets programmatically:

```python
from backend.models.metadata_models import AssetMetadata

# Add custom metadata
AssetMetadata.objects.create(
    asset=asset,
    key='budget_amount',
    value='50000',
    data_type='number',
    is_searchable=True,
    is_public=True
)

# Add multiple metadata fields
metadata_fields = [
    {'key': 'department', 'value': 'finance', 'data_type': 'text'},
    {'key': 'approval_date', 'value': '2024-03-15', 'data_type': 'date'},
    {'key': 'confidential', 'value': 'false', 'data_type': 'boolean'}
]

for field in metadata_fields:
    AssetMetadata.objects.create(asset=asset, **field)
```

### Bulk Metadata Operations

```python
# Bulk update metadata
from django.db import transaction

@transaction.atomic
def bulk_update_metadata(asset_ids, metadata_updates):
    for asset_id in asset_ids:
        asset = Asset.objects.get(id=asset_id)
        for key, value in metadata_updates.items():
            AssetMetadata.objects.update_or_create(
                asset=asset,
                key=key,
                defaults={'value': value}
            )
```

## Hierarchical Tagging

### Tag Categories

Create hierarchical tag structures:

```python
from backend.models.metadata_models import TagCategory, Tag

# Root category
projects = TagCategory.objects.create(
    tenant=tenant,
    name='Projects',
    description='Project-related tags',
    color='#007bff'
)

# Subcategory
alpha_project = TagCategory.objects.create(
    tenant=tenant,
    name='Alpha Project',
    description='Alpha project milestones',
    parent=projects,
    color='#28a745'
)

# Sub-subcategory
milestones = TagCategory.objects.create(
    tenant=tenant,
    name='Milestones',
    parent=alpha_project,
    color='#ffc107'
)
```

### Hierarchical Tags

```python
# Create tags with hierarchy
milestone_1 = Tag.objects.create(
    tenant=tenant,
    name='milestone-1',
    category=milestones,
    description='First project milestone'
)
# Automatically sets hierarchy: "Projects.Alpha Project.Milestones.milestone-1"

# Search with hierarchy
search_results = search_engine.search(
    query="",
    filters={
        'tags': ['Projects.Alpha Project']  # Matches all child tags
    }
)
```

### Tag Usage Analytics

```python
# Get popular tags
popular_tags = Tag.objects.filter(
    tenant=tenant
).order_by('-usage_count')[:20]

# Increment tag usage
tag.increment_usage()

# Get tag hierarchy path
hierarchy_path = tag.get_hierarchy_path()
```

## Auto-Tagging

### Creating Auto-Tag Rules

```python
from backend.models.metadata_models import AutoTagRule

# Create rule for financial documents
rule = AutoTagRule.objects.create(
    tenant=tenant,
    name='Financial Document Auto-Tagger',
    description='Automatically tag financial documents',

    # Conditions
    file_type_patterns=['pdf', 'xlsx', 'doc'],
    filename_patterns=['.*budget.*', '.*financial.*', '.*invoice.*'],
    content_patterns=['budget', 'financial', 'expense'],
    metadata_conditions={
        'department': 'finance'
    },

    # Settings
    is_active=True,
    priority=10,
    confidence_threshold=0.8
)

# Add tags to apply
finance_tag = Tag.objects.get(name='finance')
budget_tag = Tag.objects.get(name='budget')
rule.tags_to_add.add(finance_tag, budget_tag)

# Add metadata to apply
rule.metadata_to_add = {
    'category': 'financial',
    'requires_approval': 'true'
}
rule.save()
```

### Pattern Matching

Auto-tag rules support various pattern types:

#### File Type Patterns
```python
file_type_patterns = [
    'pdf',              # Exact match
    'doc.*',           # Regex pattern
    'image/.*'         # MIME type pattern
]
```

#### Filename Patterns
```python
filename_patterns = [
    '.*report.*',       # Contains 'report'
    '^budget_.*',       # Starts with 'budget_'
    '.*_final\\.pdf$'   # Ends with '_final.pdf'
]
```

#### Content Patterns
```python
content_patterns = [
    'quarterly report',     # Exact phrase
    '\\b(budget|financial)\\b',  # Word boundaries
    '\\d{4}-\\d{2}-\\d{2}'  # Date pattern
]
```

### Applying Auto-Tag Rules

```python
# Apply all rules to an asset
def apply_auto_tag_rules(asset):
    rules = AutoTagRule.objects.filter(
        tenant=asset.tenant,
        is_active=True
    ).order_by('-priority')

    applied_rules = []
    for rule in rules:
        if rule.apply_to_asset(asset):
            applied_rules.append(rule.name)

    return applied_rules

# Apply rules during asset upload
@receiver(post_save, sender=Asset)
def auto_tag_asset(sender, instance, created, **kwargs):
    if created:
        apply_auto_tag_rules(instance)
```

## Best Practices

### Filter Performance

1. **Index Strategy**
   - Create indexes on frequently filtered fields
   - Use partial indexes for tenant isolation
   - Consider composite indexes for common filter combinations

2. **Query Optimization**
   - Use appropriate filter types for data
   - Combine filters to reduce result sets
   - Cache facet results for popular queries

3. **UI Considerations**
   - Progressive loading for large facet lists
   - Debounce filter changes
   - Show filter application progress

### Metadata Design

1. **Schema Planning**
   - Design templates for common asset types
   - Keep field names consistent across templates
   - Use validation rules to ensure data quality

2. **Tag Hierarchy**
   - Plan hierarchy levels carefully (max 4-5 levels)
   - Use descriptive category names
   - Implement tag governance policies

3. **Auto-Tagging**
   - Start with high-confidence rules
   - Monitor rule performance and accuracy
   - Regularly review and update patterns

### Security Considerations

1. **Data Access**
   - Respect user permissions in filtering
   - Hide sensitive metadata from unauthorized users
   - Audit metadata access patterns

2. **Input Validation**
   - Validate all filter inputs
   - Sanitize custom metadata values
   - Prevent injection attacks in patterns

## Troubleshooting

### Common Filter Issues

1. **No Results with Filters**
   - Check if filters are too restrictive
   - Verify data exists for filter values
   - Test filters individually

2. **Slow Filter Performance**
   - Review database indexes
   - Check for N+1 query problems
   - Consider query optimization

3. **Incorrect Facet Counts**
   - Verify facet generation logic
   - Check for cache staleness
   - Review tenant isolation

### Metadata Issues

1. **Validation Errors**
   - Check template schema definitions
   - Verify field type compatibility
   - Review validation rules

2. **Auto-Tag Problems**
   - Test pattern matching individually
   - Check rule priorities and conflicts
   - Review confidence thresholds

### Debug Tools

```python
# Debug filter application
from django.db import connection
from django.conf import settings

settings.DEBUG = True
# Run filtered query
filtered_assets = filter_manager.apply_filters(queryset, filters)
print(connection.queries[-1]['sql'])

# Test auto-tag rules
rule = AutoTagRule.objects.get(id=1)
print(f"Rule matches asset: {rule.matches_asset(asset)}")

# Validate metadata template
errors = template.validate_metadata(metadata_dict)
print(f"Validation errors: {errors}")
```