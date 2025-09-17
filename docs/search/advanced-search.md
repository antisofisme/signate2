# Advanced Search & Filtering System

## Overview

The Advanced Search & Filtering System provides comprehensive search capabilities for the multi-tenant asset management platform, including full-text search, faceted filtering, metadata management, and search analytics.

## Architecture

### Core Components

1. **SearchEngine** - Main search interface with full-text capabilities
2. **SearchFilterManager** - Advanced filtering and faceted search
3. **SearchIndexManager** - Index management and optimization
4. **SearchAnalytics** - Performance monitoring and usage analytics
5. **MetadataModels** - Rich metadata and tagging system

### Technology Stack

- **PostgreSQL Full-Text Search** - Native search capabilities
- **Django ORM** - Query building and optimization
- **Celery** - Background indexing tasks
- **Redis Cache** - Performance optimization
- **NLTK** - Natural language processing

## Search Features

### Full-Text Search

```python
from backend.search.search_engine import SearchEngine

search_engine = SearchEngine()
results = search_engine.search(
    query="financial documents",
    tenant_id=tenant.id,
    user=request.user,
    search_type='comprehensive'
)
```

#### Search Types

- **Comprehensive** - Full-text search with ranking and metadata
- **Quick** - Fast icontains search for responsive UI
- **Fuzzy** - Trigram similarity for typo tolerance

#### Boolean Operators

- **AND, OR, NOT** - Combine search terms
- **Phrase Matching** - Use quotes for exact phrases
- **Exclusions** - Use minus (-) to exclude terms

### Advanced Filtering

```python
filters = {
    'file_type': ['pdf', 'doc', 'docx'],
    'date_range': {
        'start': '2024-01-01',
        'end': '2024-12-31'
    },
    'tags': ['important', 'project-alpha'],
    'metadata': {
        'department': 'finance',
        'budget': {'min': 1000, 'max': 10000}
    }
}

results = search_engine.search(
    query="budget analysis",
    filters=filters,
    tenant_id=tenant.id
)
```

#### Filter Types

1. **File Type Filters**
   - Exact types: `['pdf', 'jpg']`
   - Categories: `['images', 'documents']`
   - MIME type patterns

2. **Date Range Filters**
   - Absolute dates: `{'start': '2024-01-01', 'end': '2024-12-31'}`
   - Relative ranges: `'last_30_days'`, `'this_year'`
   - Creation vs modification dates

3. **Size Filters**
   - Byte ranges: `{'min': 1024, 'max': 1048576}`
   - Predefined sizes: `'small'`, `'medium'`, `'large'`

4. **Tag Filters**
   - Tag names: `['important', 'urgent']`
   - Hierarchical tags: `['category.subcategory']`
   - Tag IDs for exact matching

5. **Metadata Filters**
   - Exact matches: `{'status': 'active'}`
   - Range queries: `{'price': {'min': 100, 'max': 500}}`
   - Pattern matching: `{'name': {'pattern': '.*report.*'}}`

6. **User Filters**
   - User IDs: `{'user': 123}`
   - Usernames: `{'user': 'john.doe'}`
   - Multiple users: `{'user': [123, 456]}`

### Faceted Search

Facets provide dynamic filter options based on search results:

```python
# Get facets for current search
facets = filter_manager.get_facets(queryset, applied_filters)

# Example facet structure
{
    'file_types': [
        {'value': 'pdf', 'count': 245, 'label': 'PDF'},
        {'value': 'doc', 'count': 123, 'label': 'DOC'}
    ],
    'tags': [
        {'value': 'important', 'count': 89},
        {'value': 'urgent', 'count': 56}
    ],
    'users': [
        {'value': 'john.doe', 'count': 34}
    ]
}
```

## Metadata Management

### Hierarchical Tagging

```python
# Create tag categories
category = TagCategory.objects.create(
    tenant=tenant,
    name='Projects',
    parent=None
)

subcategory = TagCategory.objects.create(
    tenant=tenant,
    name='Alpha Project',
    parent=category
)

# Create hierarchical tags
tag = Tag.objects.create(
    tenant=tenant,
    name='milestone-1',
    category=subcategory
)
# Automatically sets hierarchy: "Projects.Alpha Project.milestone-1"
```

### Custom Metadata Fields

```python
# Define metadata template
template = MetadataTemplate.objects.create(
    tenant=tenant,
    name='Financial Documents',
    schema={
        'fields': [
            {
                'name': 'budget_amount',
                'type': 'number',
                'required': True,
                'validation': {'min': 0}
            },
            {
                'name': 'department',
                'type': 'select',
                'options': ['finance', 'hr', 'it'],
                'required': True
            },
            {
                'name': 'approval_date',
                'type': 'date',
                'required': False
            }
        ]
    }
)

# Add metadata to asset
AssetMetadata.objects.create(
    asset=asset,
    key='budget_amount',
    value='50000',
    data_type='number'
)
```

### Auto-Tagging Rules

```python
# Create auto-tagging rule
rule = AutoTagRule.objects.create(
    tenant=tenant,
    name='Financial Documents Auto-Tag',
    file_type_patterns=['pdf', 'xls', 'xlsx'],
    filename_patterns=['.*budget.*', '.*financial.*'],
    metadata_to_add={
        'category': 'financial',
        'requires_approval': 'true'
    }
)

# Add tags to apply
rule.tags_to_add.add(finance_tag, budget_tag)

# Apply to asset
if rule.matches_asset(asset):
    rule.apply_to_asset(asset)
```

## Search Indexing

### Index Management

```python
from backend.search.indexing import SearchIndexManager

index_manager = SearchIndexManager()

# Create full index
result = index_manager.create_full_index(
    tenant_id=tenant.id,
    force=True
)

# Optimize index
optimization = index_manager.optimize_index(tenant_id=tenant.id)

# Get index status
status = index_manager.get_index_status(tenant_id=tenant.id)
```

### Background Tasks

```python
# Celery tasks for background processing
from backend.search.indexing import (
    create_search_index_task,
    optimize_search_index_task,
    daily_index_maintenance
)

# Schedule index creation
create_search_index_task.delay(tenant_id=tenant.id)

# Daily maintenance
daily_index_maintenance.delay()
```

### Index Optimization

1. **PostgreSQL Statistics** - Keep table statistics current
2. **Index Cleanup** - Remove old index records
3. **Performance Analysis** - Identify slow queries
4. **Size Management** - Monitor index size growth

## API Endpoints

### Search API

```bash
# Basic search
POST /api/v3/search/
{
    "query": "financial documents",
    "filters": {
        "file_type": ["pdf"],
        "date_range": "last_30_days"
    },
    "page": 1,
    "page_size": 20
}

# Get suggestions
GET /api/v3/search/suggestions/?q=financi&limit=10

# Get facets
POST /api/v3/search/facets/
{
    "query": "documents",
    "filters": {"file_type": ["pdf"]}
}
```

### Saved Searches

```bash
# Create saved search
POST /api/v3/search/saved/
{
    "name": "Monthly Financial Reports",
    "query": "monthly financial report",
    "filters": {"file_type": ["pdf"]},
    "alert_enabled": true
}

# Execute saved search
POST /api/v3/search/saved/{id}/execute/

# Get search history
GET /api/v3/search/history/?limit=20
```

### Search Analytics

```bash
# Get analytics
GET /api/v3/search/analytics/?period=7d

# Get index status
GET /api/v3/search/index/status/

# Trigger index rebuild
POST /api/v3/search/index/rebuild/
{
    "force": true
}
```

## Performance Optimization

### Query Performance

1. **Index Strategy**
   - Full-text search vectors on main content
   - B-tree indexes on filter fields
   - Partial indexes for tenant isolation

2. **Caching Strategy**
   - Facet results cached for 10 minutes
   - Suggestions cached for 5 minutes
   - Analytics cached by time period

3. **Query Optimization**
   - Use appropriate search type for use case
   - Limit result sets with pagination
   - Prefer filters over complex queries

### Scaling Considerations

1. **Database Optimization**
   - PostgreSQL configuration tuning
   - Connection pooling
   - Read replicas for analytics

2. **Application Optimization**
   - Async processing for heavy operations
   - Background indexing
   - Result streaming for large exports

3. **Infrastructure**
   - Elasticsearch integration for large datasets
   - CDN for frequently accessed results
   - Load balancing for search traffic

## Search Analytics

### Performance Monitoring

```python
from backend.utils.search_analytics import SearchAnalytics

analytics = SearchAnalytics()

# Get weekly analytics
data = analytics.get_weekly_analytics(tenant_id)

# Get optimization recommendations
recommendations = analytics.get_search_optimization_recommendations(tenant_id)

# Generate comprehensive report
report = analytics.generate_search_report(tenant_id, period='monthly')
```

### Key Metrics

1. **Performance Metrics**
   - Average search time
   - Query optimization score
   - Slow query percentage
   - Search success rate

2. **Usage Metrics**
   - Total searches per period
   - Unique users
   - Popular search terms
   - Filter usage patterns

3. **Content Metrics**
   - Search result quality
   - Click-through rates
   - Zero-result queries
   - Content coverage

## Troubleshooting

### Common Issues

1. **Slow Search Performance**
   - Check index status
   - Analyze slow query log
   - Review PostgreSQL configuration
   - Consider query simplification

2. **Poor Search Results**
   - Verify index completeness
   - Check search vector configuration
   - Review content quality
   - Consider stemming/language settings

3. **High Memory Usage**
   - Monitor cache usage
   - Review facet generation
   - Check for memory leaks
   - Optimize query patterns

### Debug Tools

```python
# Enable search debugging
import logging
logging.getLogger('backend.search').setLevel(logging.DEBUG)

# Check index status
python manage.py search_index --action status --tenant-id 1

# Rebuild index
python manage.py search_index --action create --tenant-id 1 --force

# Get slow queries
slow_queries = analytics.get_slow_queries(
    tenant_id=1,
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
    min_duration=1.0
)
```

## Best Practices

### Search Implementation

1. **Query Design**
   - Use appropriate search type
   - Combine filters for better performance
   - Cache frequent queries
   - Implement progressive loading

2. **Index Management**
   - Regular index maintenance
   - Monitor index size
   - Update statistics frequently
   - Plan for growth

3. **User Experience**
   - Provide search suggestions
   - Show search progress
   - Implement faceted navigation
   - Save user preferences

### Security Considerations

1. **Tenant Isolation**
   - All searches scoped to tenant
   - Permission-based result filtering
   - Secure API endpoints
   - Audit search activity

2. **Data Protection**
   - Encrypt sensitive metadata
   - Implement field-level security
   - Log access patterns
   - Regular security reviews