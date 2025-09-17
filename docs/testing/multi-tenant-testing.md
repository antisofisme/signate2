# Multi-Tenant Testing Patterns and Best Practices

## Overview

This document provides comprehensive guidance for testing multi-tenant scenarios in the Signate SaaS platform. It covers patterns, best practices, and specific testing techniques to ensure proper tenant isolation, security, and performance across all tenant operations.

## Multi-Tenant Architecture Testing

### Understanding Tenant Isolation

Multi-tenant applications require rigorous testing to ensure:
- **Data Isolation**: Tenants cannot access each other's data
- **Performance Isolation**: One tenant's load doesn't impact others
- **Security Isolation**: Tenant boundaries are secure and impenetrable
- **Configuration Isolation**: Tenant-specific settings don't interfere

### Tenant Models

#### 1. Shared Database, Shared Schema (Row-Level Security)
```python
# Test tenant filtering at application level
@pytest.mark.tenant
def test_tenant_row_level_security():
    """Test that queries automatically filter by tenant."""
    tenant_a = create_test_tenant('tenant_a')
    tenant_b = create_test_tenant('tenant_b')

    with tenant_context(tenant_a):
        asset_a = Asset.objects.create(name="Asset A", tenant_id=tenant_a.id)

    with tenant_context(tenant_b):
        # Should not see tenant A's assets
        assets = Asset.objects.all()
        assert asset_a not in assets
        assert all(asset.tenant_id == tenant_b.id for asset in assets)
```

#### 2. Shared Database, Separate Schema
```python
# Test schema isolation
@pytest.mark.tenant
def test_schema_isolation():
    """Test that tenants operate in separate database schemas."""
    tenant_a = create_test_tenant('tenant_a', schema='schema_a')
    tenant_b = create_test_tenant('tenant_b', schema='schema_b')

    with schema_context('schema_a'):
        Asset.objects.create(name="Schema A Asset")

    with schema_context('schema_b'):
        # Should not see assets from schema A
        assert Asset.objects.filter(name="Schema A Asset").count() == 0
```

#### 3. Separate Databases
```python
# Test database isolation
@pytest.mark.tenant
def test_database_isolation():
    """Test complete database separation between tenants."""
    tenant_a_db = 'tenant_a_db'
    tenant_b_db = 'tenant_b_db'

    with database_context(tenant_a_db):
        Asset.objects.create(name="DB A Asset")

    with database_context(tenant_b_db):
        # Different database, should not exist
        assert not Asset.objects.filter(name="DB A Asset").exists()
```

## Testing Patterns

### 1. Tenant Context Testing

#### Basic Tenant Context
```python
import pytest
from tests.utils.tenant_test_utils import tenant_test_manager

@pytest.fixture
def tenant_setup():
    """Setup multiple tenants for testing."""
    tenants = []
    for i in range(3):
        tenant = tenant_test_manager.create_test_tenant(
            tenant_id=f"test_tenant_{i}",
            domain=f"tenant{i}.signate.test"
        )
        tenants.append(tenant)

    yield tenants

    # Cleanup
    for tenant in tenants:
        tenant_test_manager.delete_test_tenant(tenant['id'])

@pytest.mark.tenant
def test_tenant_asset_creation(tenant_setup):
    """Test asset creation within tenant context."""
    tenant_a, tenant_b, tenant_c = tenant_setup

    # Create assets in different tenants
    with tenant_test_manager.tenant_context(tenant_a['id']):
        asset_a = Asset.objects.create(name="Tenant A Asset")

    with tenant_test_manager.tenant_context(tenant_b['id']):
        asset_b = Asset.objects.create(name="Tenant B Asset")

        # Verify isolation
        assets_in_b = Asset.objects.all()
        asset_names = [asset.name for asset in assets_in_b]

        assert "Tenant B Asset" in asset_names
        assert "Tenant A Asset" not in asset_names
```

#### Advanced Tenant Context with Data Factory
```python
@pytest.mark.tenant
def test_bulk_tenant_operations(tenant_setup):
    """Test bulk operations within tenant contexts."""
    from tests.utils.tenant_test_utils import tenant_data_factory

    tenant_a, tenant_b, _ = tenant_setup

    # Create bulk data for tenant A
    data_a = tenant_data_factory.create_bulk_tenant_data(
        tenant_a['id'],
        num_users=10,
        num_assets=50
    )

    # Create bulk data for tenant B
    data_b = tenant_data_factory.create_bulk_tenant_data(
        tenant_b['id'],
        num_users=15,
        num_assets=30
    )

    # Verify data isolation
    with tenant_test_manager.tenant_context(tenant_a['id']):
        assert Asset.objects.count() == 50
        assert User.objects.count() == 10

    with tenant_test_manager.tenant_context(tenant_b['id']):
        assert Asset.objects.count() == 30
        assert User.objects.count() == 15
```

### 2. Cross-Tenant Security Testing

#### Data Leakage Prevention
```python
@pytest.mark.tenant
@pytest.mark.security
def test_cross_tenant_data_leakage():
    """Test that tenants cannot access each other's data through various attack vectors."""
    from tests.utils.tenant_test_utils import tenant_isolation_tester

    # Setup tenants with data
    tenant_a = tenant_test_manager.create_test_tenant('security_tenant_a')
    tenant_b = tenant_test_manager.create_test_tenant('security_tenant_b')

    # Create sensitive data in tenant A
    with tenant_test_manager.tenant_context(tenant_a['id']):
        sensitive_asset = Asset.objects.create(
            name="Confidential Asset",
            uri="https://sensitive.example.com/secret.pdf"
        )

    # Attempt various access methods from tenant B
    attack_vectors = [
        'direct_id_access',
        'wildcard_queries',
        'sql_injection',
        'parameter_pollution',
        'cache_poisoning'
    ]

    for vector in attack_vectors:
        with tenant_test_manager.tenant_context(tenant_b['id']):
            # Test specific attack vector
            result = test_attack_vector(vector, sensitive_asset.asset_id)
            assert not result['data_accessible'], f"Data leak via {vector}"
            assert not result['unauthorized_access'], f"Unauthorized access via {vector}"

def test_attack_vector(vector, target_asset_id):
    """Test specific attack vector against tenant isolation."""
    result = {'data_accessible': False, 'unauthorized_access': False}

    try:
        if vector == 'direct_id_access':
            # Try direct access with asset ID
            asset = Asset.objects.filter(asset_id=target_asset_id).first()
            result['data_accessible'] = asset is not None

        elif vector == 'wildcard_queries':
            # Try wildcard/broad queries
            assets = Asset.objects.filter(name__contains='Confidential')
            result['data_accessible'] = len(assets) > 0

        elif vector == 'sql_injection':
            # Test SQL injection attempts
            malicious_queries = [
                f"'; SELECT * FROM assets WHERE asset_id='{target_asset_id}'; --",
                f"' OR asset_id='{target_asset_id}' OR '1'='1",
            ]
            for query in malicious_queries:
                try:
                    assets = Asset.objects.extra(where=[query])
                    result['data_accessible'] = len(assets) > 0
                except:
                    pass  # Query should fail

    except Exception:
        # Exceptions are expected for security violations
        pass

    return result
```

#### Privilege Escalation Testing
```python
@pytest.mark.tenant
@pytest.mark.security
def test_tenant_privilege_escalation():
    """Test that users cannot escalate privileges across tenant boundaries."""
    # Create admin user in tenant A
    tenant_a = tenant_test_manager.create_test_tenant('priv_tenant_a')
    tenant_b = tenant_test_manager.create_test_tenant('priv_tenant_b')

    with tenant_test_manager.tenant_context(tenant_a['id']):
        admin_a = User.objects.create_user(
            username='admin_a',
            email='admin@tenant-a.com',
            is_staff=True,
            is_superuser=True
        )

    # Try to use tenant A admin privileges in tenant B
    with tenant_test_manager.tenant_context(tenant_b['id']):
        # Admin from tenant A should not have privileges in tenant B
        assert not admin_a.has_perm('add_asset')
        assert not admin_a.has_perm('change_asset')
        assert not admin_a.has_perm('delete_asset')

        # Try to perform admin actions
        with pytest.raises(PermissionDenied):
            Asset.objects.create(
                name="Unauthorized Asset",
                created_by=admin_a
            )
```

### 3. Performance Isolation Testing

#### Resource Usage Monitoring
```python
@pytest.mark.tenant
@pytest.mark.performance
def test_tenant_resource_isolation():
    """Test that one tenant's resource usage doesn't impact others."""
    import threading
    import time
    from tests.utils.tenant_test_utils import tenant_performance_tester

    # Setup tenants
    tenant_heavy = tenant_test_manager.create_test_tenant('heavy_tenant')
    tenant_light = tenant_test_manager.create_test_tenant('light_tenant')

    # Performance tracking
    performance_results = {}

    def heavy_workload():
        """Simulate heavy database operations."""
        with tenant_test_manager.tenant_context(tenant_heavy['id']):
            # Create large number of assets
            for i in range(1000):
                Asset.objects.create(
                    name=f"Heavy Asset {i}",
                    uri=f"https://heavy.example.com/asset_{i}.jpg",
                    duration=3600 * i  # Increasing duration
                )

    def light_workload():
        """Simulate light database operations."""
        results = []
        with tenant_test_manager.tenant_context(tenant_light['id']):
            for i in range(10):
                start_time = time.time()

                # Simple query operation
                Asset.objects.create(name=f"Light Asset {i}")
                asset_count = Asset.objects.count()

                end_time = time.time()
                results.append(end_time - start_time)

        performance_results['light_tenant'] = results

    # Run workloads concurrently
    heavy_thread = threading.Thread(target=heavy_workload)
    light_thread = threading.Thread(target=light_workload)

    heavy_thread.start()
    time.sleep(0.1)  # Start heavy load first
    light_thread.start()

    heavy_thread.join()
    light_thread.join()

    # Verify light tenant performance wasn't significantly impacted
    light_times = performance_results['light_tenant']
    avg_time = sum(light_times) / len(light_times)
    max_time = max(light_times)

    # Performance should remain reasonable despite heavy tenant load
    assert avg_time < 0.1, f"Average operation time too high: {avg_time}s"
    assert max_time < 0.5, f"Max operation time too high: {max_time}s"
```

#### Connection Pool Testing
```python
@pytest.mark.tenant
@pytest.mark.performance
def test_database_connection_isolation():
    """Test that tenants don't exhaust shared connection pools."""
    import concurrent.futures
    from django.db import connections

    def tenant_db_operations(tenant_id, operation_count=50):
        """Perform database operations for a specific tenant."""
        results = []
        with tenant_test_manager.tenant_context(tenant_id):
            for i in range(operation_count):
                try:
                    # Simulate various database operations
                    Asset.objects.create(name=f"Connection Test {i}")
                    Asset.objects.filter(name__contains="Test").count()
                    results.append(True)
                except Exception as e:
                    results.append(False)
        return results

    # Create multiple tenants
    tenants = [
        tenant_test_manager.create_test_tenant(f'conn_tenant_{i}')
        for i in range(10)
    ]

    # Run concurrent operations across all tenants
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(tenant_db_operations, tenant['id'], 20)
            for tenant in tenants
        ]

        results = [future.result() for future in futures]

    # Verify all operations succeeded
    for tenant_results in results:
        success_rate = sum(tenant_results) / len(tenant_results)
        assert success_rate > 0.95, f"Too many failed operations: {success_rate}"

    # Verify connection pool health
    db_connections = connections['default']
    assert db_connections.queries_log is not None
```

### 4. API Multi-Tenant Testing

#### Tenant Context in API Requests
```python
@pytest.mark.tenant
@pytest.mark.api
def test_api_tenant_isolation():
    """Test API endpoints respect tenant boundaries."""
    # Setup tenants and users
    tenant_a = tenant_test_manager.create_test_tenant('api_tenant_a')
    tenant_b = tenant_test_manager.create_test_tenant('api_tenant_b')

    # Create users and assets for each tenant
    with tenant_test_manager.tenant_context(tenant_a['id']):
        user_a = User.objects.create_user('user_a', 'a@tenant-a.com', 'pass')
        asset_a = Asset.objects.create(name="API Asset A")

    with tenant_test_manager.tenant_context(tenant_b['id']):
        user_b = User.objects.create_user('user_b', 'b@tenant-b.com', 'pass')
        asset_b = Asset.objects.create(name="API Asset B")

    # Test API access with tenant context
    from rest_framework.test import APIClient

    client = APIClient()

    # User A should only see tenant A assets
    client.force_authenticate(user=user_a)
    client.defaults['HTTP_X_TENANT_ID'] = tenant_a['id']

    response = client.get('/api/v1/assets/')
    assert response.status_code == 200

    asset_names = [asset['name'] for asset in response.data.get('results', [])]
    assert "API Asset A" in asset_names
    assert "API Asset B" not in asset_names

    # User B should only see tenant B assets
    client.force_authenticate(user=user_b)
    client.defaults['HTTP_X_TENANT_ID'] = tenant_b['id']

    response = client.get('/api/v1/assets/')
    assert response.status_code == 200

    asset_names = [asset['name'] for asset in response.data.get('results', [])]
    assert "API Asset B" in asset_names
    assert "API Asset A" not in asset_names
```

#### Cross-Tenant API Access Prevention
```python
@pytest.mark.tenant
@pytest.mark.api
@pytest.mark.security
def test_prevent_cross_tenant_api_access():
    """Test that users cannot access other tenants' data via API."""
    # Setup
    tenant_a = tenant_test_manager.create_test_tenant('xapi_tenant_a')
    tenant_b = tenant_test_manager.create_test_tenant('xapi_tenant_b')

    with tenant_test_manager.tenant_context(tenant_a['id']):
        user_a = User.objects.create_user('user_a', 'a@test.com', 'pass')
        asset_a = Asset.objects.create(name="Secret Asset A")

    with tenant_test_manager.tenant_context(tenant_b['id']):
        asset_b = Asset.objects.create(name="Secret Asset B")

    # Try to access tenant B's asset with tenant A's user
    client = APIClient()
    client.force_authenticate(user=user_a)
    client.defaults['HTTP_X_TENANT_ID'] = tenant_a['id']

    # Direct asset access
    response = client.get(f'/api/v1/assets/{asset_b.asset_id}/')
    assert response.status_code in [404, 403]  # Should not be accessible

    # Try to manipulate tenant header
    client.defaults['HTTP_X_TENANT_ID'] = tenant_b['id']
    response = client.get(f'/api/v1/assets/{asset_b.asset_id}/')
    assert response.status_code in [404, 403]  # Should still be blocked

    # Try various attack vectors
    attack_headers = [
        {'HTTP_X_TENANT_ID': f"{tenant_a['id']},{tenant_b['id']}"},  # Injection
        {'HTTP_X_TENANT_ID': '*'},  # Wildcard
        {'HTTP_X_TENANT_ID': '../' + tenant_b['id']},  # Path traversal
        {'HTTP_X_TENANT_ID': tenant_b['id'], 'HTTP_X_ORIGINAL_TENANT': tenant_a['id']},
    ]

    for headers in attack_headers:
        client.defaults.update(headers)
        response = client.get(f'/api/v1/assets/{asset_b.asset_id}/')
        assert response.status_code in [400, 403, 404], f"Vulnerable to header attack: {headers}"
```

### 5. Data Migration Testing

#### Tenant Data Migration
```python
@pytest.mark.tenant
@pytest.mark.integration
def test_tenant_data_migration():
    """Test data migrations across tenant boundaries."""
    # Create tenant with legacy data structure
    tenant = tenant_test_manager.create_test_tenant('migration_tenant')

    with tenant_test_manager.tenant_context(tenant['id']):
        # Create legacy data
        legacy_assets = []
        for i in range(10):
            asset = Asset.objects.create(
                name=f"Legacy Asset {i}",
                # Old field structure
                old_field="legacy_value"
            )
            legacy_assets.append(asset)

    # Simulate migration
    def migrate_tenant_data(tenant_id):
        with tenant_test_manager.tenant_context(tenant_id):
            # Perform migration operations
            for asset in Asset.objects.all():
                # Migrate old_field to new_field
                if hasattr(asset, 'old_field') and asset.old_field:
                    asset.new_field = asset.old_field
                    asset.save()

    # Run migration
    migrate_tenant_data(tenant['id'])

    # Verify migration results
    with tenant_test_manager.tenant_context(tenant['id']):
        migrated_assets = Asset.objects.all()
        for asset in migrated_assets:
            assert hasattr(asset, 'new_field')
            if asset.name.startswith("Legacy"):
                assert asset.new_field == "legacy_value"
```

#### Schema Version Testing
```python
@pytest.mark.tenant
@pytest.mark.integration
def test_mixed_schema_versions():
    """Test system with tenants on different schema versions."""
    # Tenant A on old schema version
    tenant_old = tenant_test_manager.create_test_tenant(
        'old_schema_tenant',
        config={'schema_version': '1.0'}
    )

    # Tenant B on new schema version
    tenant_new = tenant_test_manager.create_test_tenant(
        'new_schema_tenant',
        config={'schema_version': '2.0'}
    )

    # Test operations on both tenants
    with tenant_test_manager.tenant_context(tenant_old['id']):
        # Old schema operations
        asset_old = Asset.objects.create(name="Old Schema Asset")
        assert asset_old.schema_version == '1.0'

    with tenant_test_manager.tenant_context(tenant_new['id']):
        # New schema operations
        asset_new = Asset.objects.create(
            name="New Schema Asset",
            new_field="new_value"  # Field only in v2.0
        )
        assert asset_new.schema_version == '2.0'
        assert asset_new.new_field == "new_value"

    # Verify both tenants work independently
    assert Asset.objects.filter(schema_version='1.0').count() == 1
    assert Asset.objects.filter(schema_version='2.0').count() == 1
```

## Best Practices

### 1. Test Organization

#### Fixture Organization
```python
# conftest.py - Shared fixtures
@pytest.fixture(scope='session')
def tenant_test_suite():
    """Session-level tenant testing setup."""
    # Initialize tenant testing infrastructure
    yield
    # Cleanup all test tenants

@pytest.fixture(scope='function')
def isolated_tenant():
    """Function-level isolated tenant."""
    tenant = tenant_test_manager.create_test_tenant()
    yield tenant
    tenant_test_manager.delete_test_tenant(tenant['id'])

# test_tenant_specific.py - Tenant-specific tests
@pytest.mark.tenant
class TestTenantAssetManagement:
    """Grouped tenant-specific tests."""

    def test_asset_creation(self, isolated_tenant):
        """Test asset creation in tenant context."""
        pass

    def test_asset_deletion(self, isolated_tenant):
        """Test asset deletion in tenant context."""
        pass
```

#### Test Markers
```python
# pytest.ini
markers =
    tenant: Multi-tenant specific tests
    isolation: Tenant isolation tests
    performance: Tenant performance tests
    security: Tenant security tests
    migration: Tenant migration tests
    api_tenant: API multi-tenant tests

# Usage
@pytest.mark.tenant
@pytest.mark.isolation
def test_data_isolation():
    pass
```

### 2. Test Data Management

#### Realistic Tenant Scenarios
```python
def create_realistic_tenant_data(tenant_id, scenario='small_business'):
    """Create realistic test data for different tenant scenarios."""
    scenarios = {
        'small_business': {
            'users': 5,
            'assets': 20,
            'daily_requests': 100
        },
        'enterprise': {
            'users': 100,
            'assets': 1000,
            'daily_requests': 10000
        },
        'startup': {
            'users': 2,
            'assets': 5,
            'daily_requests': 10
        }
    }

    config = scenarios.get(scenario, scenarios['small_business'])

    with tenant_test_manager.tenant_context(tenant_id):
        # Create users
        users = []
        for i in range(config['users']):
            user = User.objects.create_user(
                username=f"user_{i}_{tenant_id}",
                email=f"user{i}@{tenant_id}.com",
                password="testpass123"
            )
            users.append(user)

        # Create assets
        assets = []
        for i in range(config['assets']):
            asset = Asset.objects.create(
                name=f"Asset {i} for {scenario}",
                uri=f"https://{tenant_id}.example.com/asset_{i}.jpg",
                created_by=users[i % len(users)]
            )
            assets.append(asset)

    return {'users': users, 'assets': assets, 'config': config}
```

### 3. Performance Testing

#### Tenant Performance Baselines
```python
@pytest.mark.tenant
@pytest.mark.performance
def test_tenant_performance_baselines():
    """Establish performance baselines for different tenant sizes."""
    scenarios = ['startup', 'small_business', 'enterprise']
    results = {}

    for scenario in scenarios:
        tenant = tenant_test_manager.create_test_tenant(f'{scenario}_perf')
        data = create_realistic_tenant_data(tenant['id'], scenario)

        # Measure operations
        with tenant_test_manager.tenant_context(tenant['id']):
            start_time = time.time()

            # Standard operations
            Asset.objects.all().count()
            Asset.objects.filter(is_enabled=True).order_by('-created_at')[:10]
            User.objects.filter(is_active=True).count()

            end_time = time.time()

        results[scenario] = {
            'duration': end_time - start_time,
            'data_size': data['config']
        }

    # Verify performance scales appropriately
    assert results['startup']['duration'] < 0.1
    assert results['small_business']['duration'] < 0.5
    assert results['enterprise']['duration'] < 2.0
```

### 4. Security Testing

#### Comprehensive Security Test Suite
```python
@pytest.mark.tenant
@pytest.mark.security
class TestTenantSecurity:
    """Comprehensive tenant security testing."""

    def test_authentication_isolation(self):
        """Test authentication is properly isolated between tenants."""
        pass

    def test_authorization_boundaries(self):
        """Test authorization respects tenant boundaries."""
        pass

    def test_data_encryption_per_tenant(self):
        """Test tenant-specific data encryption."""
        pass

    def test_audit_trail_isolation(self):
        """Test audit trails are tenant-specific."""
        pass

    def test_backup_restore_isolation(self):
        """Test backup/restore operations maintain tenant isolation."""
        pass
```

## Common Pitfalls and Solutions

### 1. Test Data Leakage
**Problem**: Tests interfere with each other due to shared data.

**Solution**:
```python
@pytest.fixture(autouse=True)
def cleanup_tenant_data():
    """Automatic cleanup after each test."""
    yield
    # Clean up all test tenants
    tenant_test_manager.cleanup_all_tenants()
```

### 2. Performance Test Inconsistency
**Problem**: Performance tests give inconsistent results.

**Solution**:
```python
@pytest.mark.performance
def test_with_warmup():
    """Include warmup period for consistent results."""
    # Warmup
    for _ in range(10):
        Asset.objects.count()

    # Actual measurement
    start_time = time.time()
    # Test operations
    end_time = time.time()
```

### 3. Security Test False Positives
**Problem**: Security tests trigger false alarms.

**Solution**:
```python
@pytest.mark.security
def test_with_proper_context():
    """Ensure security tests run in proper isolation."""
    with security_test_context():
        # Security test operations
        pass
```

## Conclusion

Multi-tenant testing requires careful attention to isolation, security, and performance. By following these patterns and best practices, you can ensure your Signate SaaS platform maintains proper tenant boundaries while delivering consistent performance and security across all tenants.

### Key Takeaways

1. **Always test in isolation**: Each tenant test should be completely isolated
2. **Verify security boundaries**: Test for data leakage and privilege escalation
3. **Monitor performance impact**: Ensure one tenant doesn't affect others
4. **Test realistic scenarios**: Use realistic data sizes and usage patterns
5. **Automate cleanup**: Always clean up test data to prevent interference

The multi-tenant testing framework provides the foundation for building a secure, performant, and reliable SaaS platform that can scale to serve thousands of tenants while maintaining strict data isolation and security boundaries.