"""
Pytest configuration and shared fixtures for Signate SaaS testing.

This module provides comprehensive testing fixtures for:
- Django test setup and teardown
- Multi-tenant database isolation
- API authentication and permissions
- Test data factories
- Performance monitoring
- Security testing utilities
"""

import os
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

# Set Django settings module for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anthias_django.settings')
os.environ.setdefault('ENVIRONMENT', 'test')

import django
from django.conf import settings
if not settings.configured:
    django.setup()

from anthias_app.models import Asset


# =============================================================================
# Database and Django Setup Fixtures
# =============================================================================

@pytest.fixture(scope='session')
def django_db_setup():
    """Setup test database with proper isolation."""
    # Use in-memory SQLite for faster tests
    settings.DATABASES['default']['NAME'] = ':memory:'
    settings.DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'

    # Disable migrations for faster test setup
    settings.MIGRATION_MODULES = {
        'anthias_app': None,
        'api': None,
        'auth': None,
        'contenttypes': None,
        'sessions': None,
    }

    # Create test database
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])


@pytest.fixture(scope='function')
def django_db_reset(db):
    """Reset database state between tests."""
    # Clear all tables
    Asset.objects.all().delete()
    User.objects.all().delete()

    # Reset auto-increment counters
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='auth_user';")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='assets';")


# =============================================================================
# Multi-Tenant Testing Fixtures
# =============================================================================

@pytest.fixture
def tenant_context():
    """
    Provide isolated tenant context for multi-tenant testing.
    Simulates tenant isolation without actual tenant implementation.
    """
    tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"

    class TenantContext:
        def __init__(self, tenant_id):
            self.tenant_id = tenant_id
            self.schema_name = f"tenant_{tenant_id}"
            self.domain = f"{tenant_id}.signate.local"

        def activate(self):
            """Activate tenant context (mock implementation)."""
            # In real multi-tenant, this would switch database schema
            self._original_db = settings.DATABASES['default']['NAME']
            settings.DATABASES['default']['NAME'] = f":memory:_{self.tenant_id}"

        def deactivate(self):
            """Deactivate tenant context."""
            if hasattr(self, '_original_db'):
                settings.DATABASES['default']['NAME'] = self._original_db

        def __enter__(self):
            self.activate()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.deactivate()

    return TenantContext(tenant_id)


@pytest.fixture
def multi_tenant_setup():
    """Setup multiple tenant contexts for cross-tenant testing."""
    tenants = []
    for i in range(3):
        tenant_id = f"test_tenant_{i}"
        tenant = {
            'id': tenant_id,
            'name': f"Test Tenant {i}",
            'schema': f"tenant_{tenant_id}",
            'domain': f"{tenant_id}.signate.local"
        }
        tenants.append(tenant)

    return tenants


# =============================================================================
# Authentication and User Fixtures
# =============================================================================

@pytest.fixture
def admin_user(db):
    """Create admin user for testing."""
    user = User.objects.create_superuser(
        username='admin',
        email='admin@signate.local',
        password='admin123!@#'
    )
    return user


@pytest.fixture
def regular_user(db):
    """Create regular user for testing."""
    user = User.objects.create_user(
        username='testuser',
        email='test@signate.local',
        password='testpass123!@#'
    )
    return user


@pytest.fixture
def tenant_admin(db, tenant_context):
    """Create tenant admin user."""
    with tenant_context:
        user = User.objects.create_user(
            username=f'tenant_admin_{tenant_context.tenant_id}',
            email=f'admin@{tenant_context.domain}',
            password='tenantadmin123!@#'
        )
        # Add tenant-specific permissions here
        user.is_staff = True
        user.save()
        return user


@pytest.fixture
def api_client():
    """Provide API client for testing."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, regular_user):
    """Provide authenticated API client."""
    token, created = Token.objects.get_or_create(user=regular_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Provide admin authenticated API client."""
    token, created = Token.objects.get_or_create(user=admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


# =============================================================================
# Test Data Factories
# =============================================================================

@pytest.fixture
def asset_factory():
    """Factory for creating test assets."""
    def _create_asset(**kwargs):
        defaults = {
            'name': f'Test Asset {uuid.uuid4().hex[:8]}',
            'uri': 'https://example.com/test.jpg',
            'mimetype': 'image/jpeg',
            'is_enabled': True,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=1),
            'duration': 3600,  # 1 hour in seconds
            'play_order': 1,
        }
        defaults.update(kwargs)
        return Asset.objects.create(**defaults)

    return _create_asset


@pytest.fixture
def bulk_assets(asset_factory):
    """Create multiple test assets."""
    assets = []
    for i in range(10):
        asset = asset_factory(
            name=f'Bulk Asset {i}',
            play_order=i,
            uri=f'https://example.com/asset_{i}.jpg'
        )
        assets.append(asset)
    return assets


# =============================================================================
# Performance and Load Testing Fixtures
# =============================================================================

@pytest.fixture
def performance_monitor():
    """Monitor test performance and resource usage."""
    import time
    import psutil
    import threading

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.peak_memory = 0
            self.monitoring = False
            self._monitor_thread = None

        def start(self):
            self.start_time = time.time()
            self.monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_resources)
            self._monitor_thread.start()

        def stop(self):
            self.end_time = time.time()
            self.monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join()

        def _monitor_resources(self):
            process = psutil.Process()
            while self.monitoring:
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                self.peak_memory = max(self.peak_memory, memory_usage)
                time.sleep(0.1)

        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

        def assert_performance(self, max_duration=5.0, max_memory_mb=100):
            """Assert performance constraints."""
            if self.duration and self.duration > max_duration:
                pytest.fail(f"Test took {self.duration:.2f}s, expected < {max_duration}s")
            if self.peak_memory > max_memory_mb:
                pytest.fail(f"Peak memory {self.peak_memory:.2f}MB, expected < {max_memory_mb}MB")

    return PerformanceMonitor()


# =============================================================================
# Security Testing Fixtures
# =============================================================================

@pytest.fixture
def security_scanner():
    """Provide security testing utilities."""
    class SecurityScanner:
        @staticmethod
        def sql_injection_payloads():
            """Common SQL injection payloads."""
            return [
                "'; DROP TABLE assets; --",
                "' OR '1'='1",
                "'; INSERT INTO assets (name) VALUES ('injected'); --",
                "' UNION SELECT * FROM auth_user --",
                "'; UPDATE assets SET is_enabled=1 WHERE '1'='1'; --"
            ]

        @staticmethod
        def xss_payloads():
            """Common XSS payloads."""
            return [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert('XSS');//",
                "<svg onload=alert('XSS')>"
            ]

        @staticmethod
        def command_injection_payloads():
            """Common command injection payloads."""
            return [
                "; ls -la",
                "| cat /etc/passwd",
                "&& whoami",
                "$(uname -a)",
                "`id`"
            ]

        @staticmethod
        def path_traversal_payloads():
            """Common path traversal payloads."""
            return [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "....//....//....//etc//passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
            ]

    return SecurityScanner()


# =============================================================================
# Backwards Compatibility Fixtures
# =============================================================================

@pytest.fixture
def legacy_api_client():
    """API client for testing legacy endpoints."""
    client = APIClient()
    # Set legacy API version headers
    client.default_format = 'json'
    client.credentials(HTTP_API_VERSION='1.0')
    return client


@pytest.fixture
def api_version_tester():
    """Test multiple API versions for backwards compatibility."""
    class APIVersionTester:
        def __init__(self):
            self.versions = ['1.0', '2.0', '3.0']

        def test_endpoint_across_versions(self, endpoint, client, method='GET', data=None):
            """Test endpoint across different API versions."""
            results = {}
            for version in self.versions:
                client.credentials(HTTP_API_VERSION=version)
                if method.upper() == 'GET':
                    response = client.get(endpoint)
                elif method.upper() == 'POST':
                    response = client.post(endpoint, data=data)
                elif method.upper() == 'PUT':
                    response = client.put(endpoint, data=data)
                elif method.upper() == 'DELETE':
                    response = client.delete(endpoint)

                results[version] = {
                    'status_code': response.status_code,
                    'data': response.data if hasattr(response, 'data') else None
                }
            return results

    return APIVersionTester()


# =============================================================================
# Mock and Patch Fixtures
# =============================================================================

@pytest.fixture
def mock_external_services():
    """Mock external service dependencies."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:

        # Setup default successful responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'status': 'success'}

        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {'id': 123, 'status': 'created'}

        yield {
            'get': mock_get,
            'post': mock_post,
            'put': mock_put,
            'delete': mock_delete
        }


# =============================================================================
# Cleanup and Teardown
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatic cleanup after each test."""
    yield

    # Clear caches
    from django.core.cache import cache
    cache.clear()

    # Reset any global state
    if hasattr(settings, 'TEST_STATE'):
        delattr(settings, 'TEST_STATE')


# =============================================================================
# Test Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Disable migrations for faster tests
    from django.conf import settings
    settings.MIGRATION_MODULES = {
        'anthias_app': None,
        'api': None,
    }

    # Configure logging for tests
    import logging
    logging.disable(logging.CRITICAL)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Mark slow tests
        if 'slow' in item.keywords:
            item.add_marker(pytest.mark.slow)

        # Mark integration tests
        if 'integration' in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark API tests
        if 'api' in item.nodeid or 'test_api' in item.name:
            item.add_marker(pytest.mark.api)


# =============================================================================
# Parametrization Helpers
# =============================================================================

# Common test parameters
ASSET_TYPES = ['image/jpeg', 'image/png', 'video/mp4', 'text/html']
TENANT_SIZES = ['small', 'medium', 'large', 'enterprise']
API_VERSIONS = ['1.0', '2.0', '3.0']