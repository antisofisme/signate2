# Signate SaaS Testing Infrastructure

## Overview

This testing infrastructure provides comprehensive testing capabilities for the Signate SaaS platform transformation, ensuring code quality, multi-tenant isolation, security, and performance standards.

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install -r project/backend/requirements/requirements.txt
pip install -r project/backend/requirements/requirements.dev.txt

# Additional testing dependencies
pip install pytest pytest-django pytest-cov pytest-xdist pytest-mock
pip install freezegun time-machine psutil memory-profiler
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration            # Integration tests only
pytest -m api                    # API tests only
pytest -m tenant                 # Multi-tenant tests only
pytest -m security               # Security tests only
pytest -m performance            # Performance tests only

# Run with coverage
pytest --cov=anthias_app --cov=api --cov-report=html

# Run specific test file
pytest tests/test_models.py
pytest tests/test_api.py

# Run with detailed output
pytest -v --tb=short

# Run tests in parallel
pytest -n auto
```

## 📁 Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── test_models.py             # Model testing (Asset model)
├── test_api.py                # API endpoint testing
└── utils/
    └── tenant_test_utils.py   # Multi-tenant testing utilities

.github/workflows/
└── test.yml                   # CI/CD testing pipeline

docs/testing/
├── strategy.md                # Comprehensive testing strategy
├── multi-tenant-testing.md   # Multi-tenant testing patterns
└── README.md                  # This file

pytest.ini                     # Pytest configuration
```

## 🧪 Test Categories

### Unit Tests (70% of tests)
Fast, isolated tests for individual components:

```python
@pytest.mark.unit
def test_asset_creation_with_defaults(db):
    """Test creating an asset with default values."""
    asset = Asset.objects.create(name="Test Asset")
    assert asset.asset_id is not None
    assert asset.is_enabled is False
```

### Integration Tests (25% of tests)
Tests for component interactions and database operations:

```python
@pytest.mark.integration
def test_asset_api_integration(authenticated_client, asset_factory):
    """Test asset API endpoint integration."""
    asset = asset_factory(name="Integration Test Asset")
    response = authenticated_client.get(f'/api/v1/assets/{asset.asset_id}/')
    assert response.status_code == 200
```

### Multi-Tenant Tests (Special category)
Tests for tenant isolation and security:

```python
@pytest.mark.tenant
def test_tenant_data_isolation(tenant_context):
    """Test that tenants cannot access each other's data."""
    with tenant_context:
        asset = Asset.objects.create(name="Tenant Asset")
        # Verify isolation...
```

### Security Tests
Tests for security vulnerabilities and protection:

```python
@pytest.mark.security
def test_sql_injection_protection(authenticated_client, security_scanner):
    """Test protection against SQL injection attacks."""
    for payload in security_scanner.sql_injection_payloads():
        # Test injection attempts...
```

### Performance Tests
Tests for performance benchmarks and optimization:

```python
@pytest.mark.performance
def test_api_response_time(authenticated_client, performance_monitor):
    """Test API response times meet SLA requirements."""
    performance_monitor.start()
    # Perform operations...
    performance_monitor.stop()
    performance_monitor.assert_performance(max_duration=0.2)
```

## 🏗️ Key Features

### 1. Comprehensive Fixtures (`conftest.py`)

- **Database Setup**: Isolated test database configuration
- **Multi-Tenant Support**: Tenant context management
- **API Testing**: Authenticated and admin clients
- **Data Factories**: Realistic test data generation
- **Performance Monitoring**: Resource usage tracking
- **Security Testing**: Common attack payload generators

### 2. Multi-Tenant Testing (`tenant_test_utils.py`)

- **TenantTestManager**: Create and manage test tenants
- **TenantDataFactory**: Generate tenant-specific test data
- **TenantIsolationTester**: Verify data isolation
- **TenantPerformanceTester**: Performance across tenants
- **TenantSecurityTester**: Security boundary testing

### 3. CI/CD Pipeline (`.github/workflows/test.yml`)

- **Pre-flight Checks**: Code formatting, security scanning
- **Code Quality**: Linting, type checking, complexity analysis
- **Parallel Testing**: Unit, integration, API, security tests
- **Coverage Analysis**: Combined coverage reporting
- **Performance Testing**: Load and stress testing
- **Deployment Readiness**: Automated quality gates

### 4. Quality Standards

- **90%+ Code Coverage**: Enforced through CI/CD
- **Performance SLAs**: API < 200ms, Database < 50ms
- **Security Testing**: OWASP Top 10 coverage
- **Multi-Tenant Isolation**: Comprehensive boundary testing

## 🔧 Usage Examples

### Basic Test Writing

```python
import pytest
from anthias_app.models import Asset

@pytest.mark.unit
def test_my_feature(db):
    """Test my new feature."""
    # Test implementation
    pass

@pytest.mark.integration
def test_api_endpoint(authenticated_client):
    """Test API endpoint."""
    response = authenticated_client.get('/api/v1/assets/')
    assert response.status_code == 200
```

### Multi-Tenant Testing

```python
from tests.utils.tenant_test_utils import tenant_test_manager

@pytest.mark.tenant
def test_tenant_feature():
    """Test feature in tenant context."""
    tenant = tenant_test_manager.create_test_tenant('test_tenant')

    with tenant_test_manager.tenant_context(tenant['id']):
        # Test operations within tenant
        asset = Asset.objects.create(name="Tenant Asset")
        assert Asset.objects.count() == 1

    # Cleanup
    tenant_test_manager.delete_test_tenant(tenant['id'])
```

### Performance Testing

```python
@pytest.mark.performance
def test_bulk_operations(performance_monitor, bulk_assets):
    """Test performance with large datasets."""
    performance_monitor.start()

    # Perform bulk operations
    Asset.objects.filter(is_enabled=True).count()

    performance_monitor.stop()
    performance_monitor.assert_performance(
        max_duration=1.0,
        max_memory_mb=50
    )
```

### Security Testing

```python
@pytest.mark.security
def test_input_validation(authenticated_client, security_scanner):
    """Test input validation against attacks."""
    for payload in security_scanner.xss_payloads():
        response = authenticated_client.post('/api/v1/assets/', {
            'name': payload
        })
        # Should handle malicious input safely
        assert response.status_code in [400, 422]
```

## 📊 Coverage Requirements

| Component | Minimum Coverage | Target |
|-----------|------------------|--------|
| Models | 95% | 98% |
| API Views | 90% | 95% |
| Utilities | 85% | 90% |
| Business Logic | 95% | 98% |
| Overall | 90% | 93% |

## 🚨 Quality Gates

Tests must pass these gates before deployment:

1. **All unit tests pass** (100%)
2. **Integration tests pass** (100%)
3. **Code coverage ≥ 90%**
4. **No security vulnerabilities** (critical/high)
5. **Performance benchmarks met**
6. **Linting and formatting checks pass**

## 🔍 Verification

Run the verification script to check infrastructure health:

```bash
python3 scripts/verify_test_setup.py
```

This validates:
- Directory structure
- Test files and configuration
- Pytest markers and fixtures
- CI/CD pipeline setup
- Documentation completeness

## 📚 Documentation

- **[Testing Strategy](strategy.md)**: Comprehensive testing approach
- **[Multi-Tenant Testing](multi-tenant-testing.md)**: Tenant isolation patterns
- **[API Testing Patterns](../api/testing.md)**: API-specific testing guidelines
- **[Security Testing Guide](../security/testing.md)**: Security testing procedures

## 🤝 Contributing

### Adding New Tests

1. Choose appropriate test category (unit/integration/api/tenant/security/performance)
2. Add proper pytest markers
3. Follow naming conventions (`test_feature_scenario`)
4. Include docstrings explaining test purpose
5. Ensure proper cleanup and isolation

### Test Naming Conventions

```python
# Unit tests
def test_model_method_with_valid_input():
def test_utility_function_edge_case():

# Integration tests
def test_api_endpoint_successful_request():
def test_database_transaction_rollback():

# Multi-tenant tests
def test_tenant_data_isolation():
def test_cross_tenant_permission_denial():

# Security tests
def test_protection_against_sql_injection():
def test_authentication_boundary_enforcement():

# Performance tests
def test_api_response_time_under_load():
def test_database_query_performance():
```

### Code Review Checklist

- [ ] Appropriate test markers applied
- [ ] Tests are isolated and don't depend on each other
- [ ] Proper fixtures used for test data
- [ ] Performance tests include assertions
- [ ] Security tests cover attack vectors
- [ ] Multi-tenant tests verify isolation
- [ ] Documentation updated if needed

## 🎯 Next Steps

1. **Extend API Testing**: Add more comprehensive API endpoint coverage
2. **Load Testing**: Implement stress testing for high-traffic scenarios
3. **Browser Testing**: Add Selenium-based E2E tests
4. **Chaos Engineering**: Implement fault injection testing
5. **ML Testing**: Add testing for machine learning components
6. **Monitoring Integration**: Connect tests to monitoring systems

## 📞 Support

For questions about the testing infrastructure:

1. Check existing documentation
2. Review test examples in the codebase
3. Run verification script for troubleshooting
4. Create issue with detailed description

---

**Testing is not about finding bugs; it's about building confidence in our code.**