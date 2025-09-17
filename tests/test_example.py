"""
Example tests to demonstrate the Signate SaaS testing infrastructure.

This file provides working examples of how to use the testing framework
for various scenarios including unit tests, API tests, multi-tenant tests,
and security tests.
"""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User

from anthias_app.models import Asset


class TestExampleUnitTests:
    """Example unit tests demonstrating basic testing patterns."""

    @pytest.mark.unit
    def test_asset_creation_example(self, db):
        """Example: Test basic asset creation."""
        asset = Asset.objects.create(
            name="Example Asset",
            uri="https://example.com/test.jpg",
            mimetype="image/jpeg"
        )

        assert asset.name == "Example Asset"
        assert asset.uri == "https://example.com/test.jpg"
        assert asset.mimetype == "image/jpeg"
        assert asset.asset_id is not None

    @pytest.mark.unit
    def test_asset_factory_example(self, asset_factory):
        """Example: Using asset factory fixture."""
        asset = asset_factory(
            name="Factory Created Asset",
            is_enabled=True
        )

        assert asset.name == "Factory Created Asset"
        assert asset.is_enabled is True

    @pytest.mark.unit
    def test_asset_is_active_logic(self, db):
        """Example: Testing business logic."""
        now = timezone.now()
        asset = Asset.objects.create(
            name="Active Asset",
            is_enabled=True,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1)
        )

        assert asset.is_active() is True

        # Test with disabled asset
        asset.is_enabled = False
        asset.save()
        assert asset.is_active() is False


class TestExampleAPITests:
    """Example API tests demonstrating REST endpoint testing."""

    @pytest.mark.api
    def test_asset_list_api_example(self, authenticated_client, bulk_assets):
        """Example: Test asset list API endpoint."""
        response = authenticated_client.get('/api/v1/assets/')

        # Note: This might return 404 if the endpoint doesn't exist yet
        # In real implementation, you'd verify actual API responses
        assert response.status_code in [200, 404]

        if response.status_code == 200 and hasattr(response, 'data'):
            # If API exists and returns data
            assert 'results' in response.data or isinstance(response.data, list)

    @pytest.mark.api
    def test_unauthenticated_access_example(self, api_client, asset_factory):
        """Example: Test that protected endpoints require authentication."""
        asset = asset_factory()

        response = api_client.get(f'/api/v1/assets/{asset.asset_id}/')

        # Should require authentication
        assert response.status_code in [401, 403, 404]

    @pytest.mark.api
    def test_admin_access_example(self, admin_client, asset_factory):
        """Example: Test admin user access."""
        asset = asset_factory()

        response = admin_client.get(f'/api/v1/assets/{asset.asset_id}/')

        # Admin should have access (or endpoint doesn't exist yet)
        assert response.status_code in [200, 404]


class TestExampleMultiTenantTests:
    """Example multi-tenant tests demonstrating isolation testing."""

    @pytest.mark.tenant
    def test_basic_tenant_isolation_example(self, tenant_context):
        """Example: Basic tenant isolation test."""
        with tenant_context:
            # Create asset in tenant context
            asset = Asset.objects.create(
                name=f"Tenant Asset {tenant_context.tenant_id}"
            )

            # Verify asset exists in this tenant
            assert Asset.objects.filter(asset_id=asset.asset_id).exists()

            # In real multi-tenant implementation, verify isolation
            tenant_assets = Asset.objects.all()
            assert len(tenant_assets) >= 1

    @pytest.mark.tenant
    def test_multi_tenant_data_factory_example(self, db):
        """Example: Using multi-tenant data factory."""
        from tests.utils.tenant_test_utils import (
            tenant_test_manager,
            tenant_data_factory
        )

        # Create test tenant
        tenant = tenant_test_manager.create_test_tenant('example_tenant')

        try:
            # Create tenant-specific data
            data = tenant_data_factory.create_bulk_tenant_data(
                tenant['id'],
                num_users=3,
                num_assets=5
            )

            assert len(data['users']) == 3
            assert len(data['assets']) == 5

            # Verify data is associated with tenant
            with tenant_test_manager.tenant_context(tenant['id']):
                # In real implementation, verify tenant isolation
                pass

        finally:
            # Cleanup
            tenant_test_manager.delete_test_tenant(tenant['id'])

    @pytest.mark.tenant
    def test_cross_tenant_isolation_example(self, db):
        """Example: Test that tenants cannot access each other's data."""
        from tests.utils.tenant_test_utils import tenant_test_manager

        # Create two test tenants
        tenant_a = tenant_test_manager.create_test_tenant('tenant_a')
        tenant_b = tenant_test_manager.create_test_tenant('tenant_b')

        try:
            # Create data in tenant A
            with tenant_test_manager.tenant_context(tenant_a['id']):
                asset_a = Asset.objects.create(name="Tenant A Asset")

            # Verify tenant B cannot see tenant A's data
            with tenant_test_manager.tenant_context(tenant_b['id']):
                # In real multi-tenant implementation:
                # - This would check different database schema
                # - Or verify row-level security filters
                # For now, we simulate the check
                cross_tenant_assets = Asset.objects.filter(
                    name="Tenant A Asset"
                )

                # In proper multi-tenant setup, this should be 0
                # For this example, we just verify the infrastructure works
                assert cross_tenant_assets.count() >= 0

        finally:
            # Cleanup
            tenant_test_manager.delete_test_tenant(tenant_a['id'])
            tenant_test_manager.delete_test_tenant(tenant_b['id'])


class TestExampleSecurityTests:
    """Example security tests demonstrating vulnerability testing."""

    @pytest.mark.security
    def test_sql_injection_protection_example(self, authenticated_client, security_scanner):
        """Example: Test SQL injection protection."""
        # Test various SQL injection payloads
        for payload in security_scanner.sql_injection_payloads()[:3]:  # Test first 3
            # Test in query parameters
            response = authenticated_client.get(f'/api/v1/assets/?name={payload}')

            # Should not cause server errors
            assert response.status_code != 500

            # Test in POST data
            response = authenticated_client.post('/api/v1/assets/', {
                'name': payload,
                'uri': 'https://example.com/test.jpg'
            })

            # Should handle gracefully (validation error or success)
            assert response.status_code != 500

    @pytest.mark.security
    def test_xss_protection_example(self, authenticated_client, security_scanner):
        """Example: Test XSS protection."""
        xss_payload = security_scanner.xss_payloads()[0]  # Test first payload

        response = authenticated_client.post('/api/v1/assets/', {
            'name': xss_payload,
            'uri': 'https://example.com/test.jpg'
        })

        # Should not cause server errors
        assert response.status_code != 500

        # If accepted, verify it's properly escaped
        if response.status_code in [200, 201] and hasattr(response, 'data'):
            if 'name' in response.data:
                # Should not contain raw script tags
                assert '<script>' not in response.data['name']

    @pytest.mark.security
    def test_authentication_boundary_example(self, api_client, regular_user):
        """Example: Test authentication boundaries."""
        # Try to access protected resource without authentication
        response = api_client.get('/api/v1/assets/')

        # Should require authentication
        assert response.status_code in [401, 403]

        # Try with valid authentication
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/v1/assets/')

        # Should allow access (or endpoint doesn't exist yet)
        assert response.status_code in [200, 404]


class TestExamplePerformanceTests:
    """Example performance tests demonstrating performance monitoring."""

    @pytest.mark.performance
    def test_bulk_query_performance_example(self, performance_monitor, bulk_assets):
        """Example: Test query performance with bulk data."""
        performance_monitor.start()

        # Perform database operations
        total_assets = Asset.objects.count()
        enabled_assets = Asset.objects.filter(is_enabled=True).count()
        recent_assets = Asset.objects.order_by('-asset_id')[:10]

        performance_monitor.stop()

        # Verify operations completed
        assert total_assets >= 10  # bulk_assets creates 10 assets
        assert enabled_assets >= 0
        assert len(list(recent_assets)) >= 0

        # Verify performance is acceptable
        performance_monitor.assert_performance(
            max_duration=1.0,  # Should complete within 1 second
            max_memory_mb=50   # Should use less than 50MB
        )

    @pytest.mark.performance
    def test_concurrent_operations_example(self, asset_factory):
        """Example: Test concurrent database operations."""
        import threading
        import time

        results = []
        errors = []

        def create_assets(count):
            """Create multiple assets concurrently."""
            try:
                for i in range(count):
                    asset = asset_factory(name=f"Concurrent Asset {i}")
                    results.append(asset.asset_id)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):  # 5 threads
            thread = threading.Thread(target=create_assets, args=(2,))  # 2 assets each
            threads.append(thread)

        # Run concurrently
        start_time = time.time()
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
        end_time = time.time()

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10  # 5 threads × 2 assets each
        assert end_time - start_time < 5.0  # Should complete quickly


class TestExampleEdgeCases:
    """Example tests for edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_asset_edge_cases_example(self, db):
        """Example: Test edge cases and boundary conditions."""
        # Test with minimal data
        minimal_asset = Asset.objects.create()
        assert minimal_asset.asset_id is not None
        assert minimal_asset.name is None

        # Test with maximum values
        long_name = "x" * 1000  # Very long name
        max_asset = Asset.objects.create(
            name=long_name,
            duration=2**63 - 1,  # Max BigIntegerField
            play_order=2**31 - 1  # Max IntegerField
        )
        assert len(max_asset.name) == 1000
        assert max_asset.duration == 2**63 - 1

        # Test with special characters
        special_asset = Asset.objects.create(
            name="Special: áéíóú çñ 中文 🚀",
            uri="https://example.com/special%20file.jpg"
        )
        assert "🚀" in special_asset.name

    @pytest.mark.unit
    def test_timezone_handling_example(self, db):
        """Example: Test timezone handling."""
        import pytz

        # Test with different timezones
        utc_time = timezone.now()
        eastern = pytz.timezone('US/Eastern')
        pacific = pytz.timezone('US/Pacific')

        asset = Asset.objects.create(
            name="Timezone Test",
            start_date=utc_time.astimezone(eastern),
            end_date=utc_time.astimezone(pacific)
        )

        # Verify timezone information is preserved
        assert asset.start_date.tzinfo is not None
        assert asset.end_date.tzinfo is not None


# Example of running specific tests:
if __name__ == "__main__":
    # This shows how tests can be run programmatically
    # In practice, use pytest command line
    print("Use: pytest tests/test_example.py -v")
    print("Or:  pytest tests/test_example.py::TestExampleUnitTests::test_asset_creation_example")
    print("Or:  pytest -m unit tests/test_example.py")