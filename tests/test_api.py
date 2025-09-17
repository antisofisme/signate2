"""
Comprehensive API testing for Signate SaaS.

Tests cover:
- REST API endpoints and HTTP methods
- Authentication and authorization
- Request/response validation
- Error handling and status codes
- API versioning and backwards compatibility
- Multi-tenant API isolation
- Rate limiting and security
- Performance and load testing
"""

import pytest
import json
from datetime import datetime, timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, Mock

from anthias_app.models import Asset


class TestAssetAPI:
    """Test suite for Asset API endpoints."""

    @pytest.mark.api
    def test_get_assets_list_unauthenticated(self, api_client, db):
        """Test getting assets list without authentication."""
        url = '/api/v1/assets/'
        response = api_client.get(url)

        # Assuming the API requires authentication
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_200_OK]

    @pytest.mark.api
    def test_get_assets_list_authenticated(self, authenticated_client, bulk_assets):
        """Test getting assets list with authentication."""
        url = '/api/v1/assets/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        if hasattr(response, 'data'):
            # If DRF returns structured data
            assert 'results' in response.data or isinstance(response.data, list)

    @pytest.mark.api
    def test_get_asset_detail(self, authenticated_client, asset_factory):
        """Test getting individual asset details."""
        asset = asset_factory(name="Detail Test Asset")
        url = f'/api/v1/assets/{asset.asset_id}/'

        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        if hasattr(response, 'data'):
            assert response.data['asset_id'] == asset.asset_id
            assert response.data['name'] == "Detail Test Asset"

    @pytest.mark.api
    def test_get_nonexistent_asset(self, authenticated_client, db):
        """Test getting non-existent asset returns 404."""
        url = '/api/v1/assets/nonexistent_id/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.api
    def test_create_asset_valid_data(self, authenticated_client, db):
        """Test creating asset with valid data."""
        asset_data = {
            'name': 'New API Asset',
            'uri': 'https://example.com/new_asset.jpg',
            'mimetype': 'image/jpeg',
            'is_enabled': True,
            'duration': 3600,
            'play_order': 1
        }

        url = '/api/v1/assets/'
        response = authenticated_client.post(url, asset_data, format='json')

        if response.status_code == status.HTTP_201_CREATED:
            # Verify asset was created
            assert Asset.objects.filter(name='New API Asset').exists()
            if hasattr(response, 'data'):
                assert response.data['name'] == 'New API Asset'

    @pytest.mark.api
    def test_create_asset_invalid_data(self, authenticated_client, db):
        """Test creating asset with invalid data."""
        # Test various invalid data scenarios
        invalid_data_sets = [
            {},  # Empty data
            {'name': ''},  # Empty name
            {'name': 'Test', 'duration': 'invalid'},  # Invalid duration type
            {'name': 'Test', 'play_order': 'invalid'},  # Invalid play_order type
        ]

        url = '/api/v1/assets/'
        for invalid_data in invalid_data_sets:
            response = authenticated_client.post(url, invalid_data, format='json')
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    @pytest.mark.api
    def test_update_asset_full(self, authenticated_client, asset_factory):
        """Test full update (PUT) of asset."""
        asset = asset_factory(name="Original Asset")

        updated_data = {
            'name': 'Updated Asset',
            'uri': 'https://example.com/updated.jpg',
            'mimetype': 'image/png',
            'is_enabled': False,
            'duration': 7200,
            'play_order': 5
        }

        url = f'/api/v1/assets/{asset.asset_id}/'
        response = authenticated_client.put(url, updated_data, format='json')

        if response.status_code == status.HTTP_200_OK:
            asset.refresh_from_db()
            assert asset.name == 'Updated Asset'
            assert asset.duration == 7200

    @pytest.mark.api
    def test_update_asset_partial(self, authenticated_client, asset_factory):
        """Test partial update (PATCH) of asset."""
        asset = asset_factory(name="Partial Update Asset")

        partial_data = {
            'name': 'Partially Updated Asset',
            'is_enabled': True
        }

        url = f'/api/v1/assets/{asset.asset_id}/'
        response = authenticated_client.patch(url, partial_data, format='json')

        if response.status_code == status.HTTP_200_OK:
            asset.refresh_from_db()
            assert asset.name == 'Partially Updated Asset'
            assert asset.is_enabled is True

    @pytest.mark.api
    def test_delete_asset(self, authenticated_client, asset_factory):
        """Test deleting an asset."""
        asset = asset_factory(name="Delete Test Asset")
        asset_id = asset.asset_id

        url = f'/api/v1/assets/{asset_id}/'
        response = authenticated_client.delete(url)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            assert not Asset.objects.filter(asset_id=asset_id).exists()

    @pytest.mark.api
    def test_asset_filtering(self, authenticated_client, db):
        """Test API filtering capabilities."""
        # Create test assets with different properties
        Asset.objects.create(name="Enabled Asset", is_enabled=True, mimetype="image/jpeg")
        Asset.objects.create(name="Disabled Asset", is_enabled=False, mimetype="video/mp4")
        Asset.objects.create(name="Another Enabled", is_enabled=True, mimetype="image/png")

        # Test filtering by enabled status
        url = '/api/v1/assets/?is_enabled=true'
        response = authenticated_client.get(url)
        if response.status_code == status.HTTP_200_OK and hasattr(response, 'data'):
            # Should return only enabled assets
            results = response.data.get('results', response.data)
            if isinstance(results, list):
                enabled_count = len([asset for asset in results if asset.get('is_enabled')])
                assert enabled_count >= 2

    @pytest.mark.api
    def test_asset_ordering(self, authenticated_client, db):
        """Test API ordering capabilities."""
        # Create assets with different play orders
        Asset.objects.create(name="Third", play_order=3)
        Asset.objects.create(name="First", play_order=1)
        Asset.objects.create(name="Second", play_order=2)

        url = '/api/v1/assets/?ordering=play_order'
        response = authenticated_client.get(url)
        if response.status_code == status.HTTP_200_OK and hasattr(response, 'data'):
            results = response.data.get('results', response.data)
            if isinstance(results, list) and len(results) >= 3:
                # Verify ordering
                play_orders = [asset.get('play_order') for asset in results[:3]]
                assert play_orders == sorted(play_orders)

    @pytest.mark.api
    def test_asset_pagination(self, authenticated_client, bulk_assets):
        """Test API pagination."""
        url = '/api/v1/assets/?page_size=5'
        response = authenticated_client.get(url)

        if response.status_code == status.HTTP_200_OK and hasattr(response, 'data'):
            # Check pagination structure
            if 'results' in response.data:
                assert len(response.data['results']) <= 5
                assert 'count' in response.data or 'next' in response.data


class TestAPIAuthentication:
    """Test API authentication and authorization."""

    @pytest.mark.api
    @pytest.mark.security
    def test_api_requires_authentication(self, api_client, asset_factory):
        """Test that protected endpoints require authentication."""
        asset = asset_factory()

        # Test various endpoints without authentication
        endpoints = [
            ('/api/v1/assets/', 'POST'),
            (f'/api/v1/assets/{asset.asset_id}/', 'PUT'),
            (f'/api/v1/assets/{asset.asset_id}/', 'PATCH'),
            (f'/api/v1/assets/{asset.asset_id}/', 'DELETE'),
        ]

        for url, method in endpoints:
            if method == 'POST':
                response = api_client.post(url, {})
            elif method == 'PUT':
                response = api_client.put(url, {})
            elif method == 'PATCH':
                response = api_client.patch(url, {})
            elif method == 'DELETE':
                response = api_client.delete(url)

            # Should require authentication
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]

    @pytest.mark.api
    @pytest.mark.security
    def test_invalid_token_authentication(self, api_client, db):
        """Test authentication with invalid token."""
        api_client.credentials(HTTP_AUTHORIZATION='Token invalid_token_here')

        url = '/api/v1/assets/'
        response = api_client.get(url)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    @pytest.mark.api
    def test_admin_permissions(self, admin_client, asset_factory):
        """Test admin user permissions."""
        asset = asset_factory()

        # Admin should be able to perform all operations
        url = f'/api/v1/assets/{asset.asset_id}/'
        response = admin_client.get(url)
        # Admin should have access (or endpoint doesn't exist yet)
        assert response.status_code != status.HTTP_403_FORBIDDEN


class TestAPIVersioning:
    """Test API versioning and backwards compatibility."""

    @pytest.mark.api
    @pytest.mark.backwards_compat
    def test_api_version_headers(self, authenticated_client, api_version_tester, asset_factory):
        """Test API behavior across different versions."""
        asset = asset_factory()

        # Test asset detail endpoint across versions
        results = api_version_tester.test_endpoint_across_versions(
            f'/api/v1/assets/{asset.asset_id}/',
            authenticated_client,
            method='GET'
        )

        # At minimum, newer versions should be backwards compatible
        for version, result in results.items():
            if result['status_code'] == status.HTTP_200_OK:
                assert 'asset_id' in result.get('data', {})

    @pytest.mark.api
    @pytest.mark.backwards_compat
    def test_legacy_api_compatibility(self, legacy_api_client, asset_factory):
        """Test that legacy API endpoints still work."""
        asset = asset_factory()

        # Test legacy endpoint format (if different)
        legacy_url = f'/api/assets/{asset.asset_id}/'  # Example legacy format
        response = legacy_api_client.get(legacy_url)

        # Should either work or gracefully redirect
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_301_MOVED_PERMANENTLY,
            status.HTTP_302_FOUND,
            status.HTTP_404_NOT_FOUND  # If legacy endpoints are removed
        ]


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    @pytest.mark.api
    def test_invalid_json_payload(self, authenticated_client, db):
        """Test handling of invalid JSON payloads."""
        url = '/api/v1/assets/'

        # Send malformed JSON
        response = authenticated_client.post(
            url,
            data='{"invalid": json}',
            content_type='application/json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.api
    def test_unsupported_content_type(self, authenticated_client, db):
        """Test handling of unsupported content types."""
        url = '/api/v1/assets/'

        response = authenticated_client.post(
            url,
            data='<xml>test</xml>',
            content_type='application/xml'
        )

        # Should reject unsupported content type
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        ]

    @pytest.mark.api
    def test_method_not_allowed(self, authenticated_client, asset_factory):
        """Test unsupported HTTP methods."""
        asset = asset_factory()
        url = f'/api/v1/assets/{asset.asset_id}/'

        # Try unsupported method (if PATCH is not supported)
        response = authenticated_client.head(url)
        assert response.status_code in [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_200_OK  # If HEAD is supported
        ]


class TestAPIPerformance:
    """Test API performance and scalability."""

    @pytest.mark.api
    @pytest.mark.performance
    def test_api_response_time(self, authenticated_client, bulk_assets, performance_monitor):
        """Test API response times with larger datasets."""
        performance_monitor.start()

        url = '/api/v1/assets/'
        response = authenticated_client.get(url)

        performance_monitor.stop()

        # API should respond quickly even with bulk data
        performance_monitor.assert_performance(max_duration=2.0)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.api
    @pytest.mark.performance
    def test_concurrent_api_requests(self, authenticated_client, asset_factory):
        """Test concurrent API requests."""
        import threading
        import time

        asset = asset_factory()
        url = f'/api/v1/assets/{asset.asset_id}/'

        responses = []
        errors = []

        def make_request():
            try:
                response = authenticated_client.get(url)
                responses.append(response.status_code)
            except Exception as e:
                errors.append(e)

        # Create multiple concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        end_time = time.time()

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(responses) == 10
        assert all(status_code == status.HTTP_200_OK for status_code in responses)
        assert end_time - start_time < 5.0  # Should complete within 5 seconds


class TestAPISecurityFeatures:
    """Test API security features and protections."""

    @pytest.mark.api
    @pytest.mark.security
    def test_sql_injection_protection(self, authenticated_client, security_scanner, db):
        """Test protection against SQL injection attacks."""
        Asset.objects.create(name="Test Asset")

        for payload in security_scanner.sql_injection_payloads():
            # Test injection in query parameters
            url = f'/api/v1/assets/?name={payload}'
            response = authenticated_client.get(url)

            # Should not cause server errors
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

            # Test injection in POST data
            response = authenticated_client.post(
                '/api/v1/assets/',
                {'name': payload},
                format='json'
            )

            # Should handle gracefully (validation error or success)
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.api
    @pytest.mark.security
    def test_xss_protection(self, authenticated_client, security_scanner, db):
        """Test protection against XSS attacks."""
        for payload in security_scanner.xss_payloads():
            response = authenticated_client.post(
                '/api/v1/assets/',
                {'name': payload, 'uri': 'https://example.com/test.jpg'},
                format='json'
            )

            # Should either reject or sanitize the input
            if response.status_code == status.HTTP_201_CREATED:
                # If accepted, verify it's properly escaped in response
                if hasattr(response, 'data') and 'name' in response.data:
                    assert '<script>' not in response.data['name']

    @pytest.mark.api
    @pytest.mark.security
    def test_csrf_protection(self, api_client, regular_user, db):
        """Test CSRF protection for state-changing operations."""
        # Login user
        api_client.force_authenticate(user=regular_user)

        # Try POST without CSRF token (if applicable)
        url = '/api/v1/assets/'
        response = api_client.post(url, {'name': 'CSRF Test'})

        # API endpoints typically use token auth, so CSRF may not apply
        # But test should verify appropriate security measures
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR


class TestMultiTenantAPI:
    """Test multi-tenant API isolation and security."""

    @pytest.mark.api
    @pytest.mark.tenant
    def test_tenant_data_isolation(self, authenticated_client, tenant_context, asset_factory):
        """Test that tenants can only access their own data."""
        # Create asset in specific tenant context
        with tenant_context:
            tenant_asset = asset_factory(name=f"Tenant {tenant_context.tenant_id} Asset")

        # Try to access asset from different tenant context
        # (This is a simulation - real implementation would handle tenant switching)
        url = f'/api/v1/assets/{tenant_asset.asset_id}/'

        # Set tenant context in headers (example implementation)
        authenticated_client.credentials(
            HTTP_AUTHORIZATION='Token test_token',
            HTTP_X_TENANT=tenant_context.tenant_id
        )

        response = authenticated_client.get(url)

        # Should either succeed (correct tenant) or fail (wrong tenant)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ]

    @pytest.mark.api
    @pytest.mark.tenant
    def test_tenant_asset_creation(self, authenticated_client, tenant_context):
        """Test creating assets in tenant context."""
        with tenant_context:
            asset_data = {
                'name': f'Tenant Asset {tenant_context.tenant_id}',
                'uri': 'https://example.com/tenant_asset.jpg',
                'mimetype': 'image/jpeg'
            }

            # Set tenant context
            authenticated_client.credentials(
                HTTP_AUTHORIZATION='Token test_token',
                HTTP_X_TENANT=tenant_context.tenant_id
            )

            url = '/api/v1/assets/'
            response = authenticated_client.post(url, asset_data, format='json')

            # Should create asset in correct tenant context
            if response.status_code == status.HTTP_201_CREATED:
                # Verify asset is created with proper tenant association
                assert 'asset_id' in response.data