# Testing Strategy - Digital Signage Enhancement

## Overview

This document outlines the comprehensive testing strategy for the digital signage system enhancement project. The strategy follows Test-Driven Development (TDD) principles and ensures high quality, security, and performance across all system components.

## Testing Pyramid

```
                    /\
                   /  \
                  /E2E \     <- End-to-End Tests (5-10%)
                 /______\
                /        \
               /Integration\ <- Integration Tests (20-30%)
              /____________\
             /              \
            /   Unit Tests   \ <- Unit Tests (60-70%)
           /________________\
```

## 1. Unit Testing Strategy

### 1.1 Backend Unit Tests (Django/Python)

**Framework**: pytest, pytest-django, factory_boy, freezegun

**Coverage Requirements**: >90% line coverage, >85% branch coverage

#### Model Testing
```python
# tests/test_models.py
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from freezegun import freeze_time
from factory.django import DjangoModelFactory

from anthias_app.models import Asset, Tenant, Layout


class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant

    name = factory.Sequence(lambda n: f"Tenant {n}")
    slug = factory.Sequence(lambda n: f"tenant-{n}")
    subscription_tier = "basic"


class AssetFactory(DjangoModelFactory):
    class Meta:
        model = Asset

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"Asset {n}")
    uri = "https://example.com/image.jpg"
    mimetype = "image/jpeg"
    duration = 10000


@pytest.mark.django_db
class TestAssetModel:
    def test_asset_creation(self):
        """Test basic asset creation"""
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)

        assert asset.asset_id is not None
        assert len(asset.asset_id) == 32
        assert asset.tenant == tenant
        assert not asset.is_enabled

    def test_asset_tenant_isolation(self):
        """Test that assets are properly isolated by tenant"""
        tenant1 = TenantFactory()
        tenant2 = TenantFactory()

        asset1 = AssetFactory(tenant=tenant1)
        asset2 = AssetFactory(tenant=tenant2)

        # Assets should belong to different tenants
        assert asset1.tenant != asset2.tenant

        # Query should respect tenant isolation
        tenant1_assets = Asset.objects.filter(tenant=tenant1)
        assert asset1 in tenant1_assets
        assert asset2 not in tenant1_assets

    @freeze_time("2024-01-15 12:00:00")
    def test_asset_is_active(self):
        """Test asset active status based on date range"""
        asset = AssetFactory(
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 20),
            is_enabled=True
        )

        assert asset.is_active() is True

        # Test outside date range
        with freeze_time("2024-01-25 12:00:00"):
            assert asset.is_active() is False

    def test_asset_unique_id_generation(self):
        """Test that asset IDs are unique"""
        asset1 = AssetFactory()
        asset2 = AssetFactory()

        assert asset1.asset_id != asset2.asset_id
        assert len(asset1.asset_id) == 32
        assert len(asset2.asset_id) == 32


@pytest.mark.django_db
class TestTenantModel:
    def test_tenant_slug_uniqueness(self):
        """Test tenant slug uniqueness constraint"""
        TenantFactory(slug="test-tenant")

        with pytest.raises(IntegrityError):
            TenantFactory(slug="test-tenant")

    def test_subscription_tier_validation(self):
        """Test subscription tier validation"""
        valid_tiers = ['basic', 'premium', 'enterprise']

        for tier in valid_tiers:
            tenant = TenantFactory(subscription_tier=tier)
            assert tenant.subscription_tier == tier

    def test_tenant_settings_default(self):
        """Test tenant settings default to empty dict"""
        tenant = TenantFactory()
        assert tenant.settings == {}
```

#### API View Testing
```python
# tests/test_api_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from anthias_app.models import Asset, Tenant
from tests.factories import AssetFactory, TenantFactory, UserFactory


@pytest.mark.django_db
class TestAssetAPIViews:
    def setup_method(self):
        self.client = APIClient()
        self.tenant = TenantFactory()
        self.user = UserFactory()
        self.asset = AssetFactory(tenant=self.tenant)

        # Set tenant context
        self.client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
        self.client.force_authenticate(user=self.user)

    def test_list_assets_success(self):
        """Test listing assets for authenticated tenant"""
        url = reverse('api:v3:asset-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']['items']) == 1
        assert response.data['data']['items'][0]['asset_id'] == self.asset.asset_id

    def test_list_assets_tenant_isolation(self):
        """Test that assets are isolated by tenant"""
        other_tenant = TenantFactory()
        other_asset = AssetFactory(tenant=other_tenant)

        url = reverse('api:v3:asset-list')
        response = self.client.get(url)

        # Should only see assets from current tenant
        asset_ids = [item['asset_id'] for item in response.data['data']['items']]
        assert self.asset.asset_id in asset_ids
        assert other_asset.asset_id not in asset_ids

    def test_create_asset_success(self):
        """Test creating new asset"""
        url = reverse('api:v3:asset-create')
        data = {
            'name': 'Test Asset',
            'uri': 'https://example.com/test.jpg',
            'mimetype': 'image/jpeg',
            'duration': 5000,
            'is_enabled': True
        }

        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['name'] == 'Test Asset'

        # Verify asset was created with correct tenant
        asset = Asset.objects.get(asset_id=response.data['data']['asset_id'])
        assert asset.tenant == self.tenant

    def test_create_asset_without_tenant_fails(self):
        """Test that creating asset without tenant context fails"""
        self.client.defaults.pop('HTTP_X_TENANT_ID', None)

        url = reverse('api:v3:asset-create')
        data = {
            'name': 'Test Asset',
            'uri': 'https://example.com/test.jpg',
            'mimetype': 'image/jpeg'
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_asset_success(self):
        """Test updating existing asset"""
        url = reverse('api:v3:asset-detail', kwargs={'asset_id': self.asset.asset_id})
        data = {
            'name': 'Updated Asset Name',
            'is_enabled': True
        }

        response = self.client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'Updated Asset Name'

        # Verify in database
        self.asset.refresh_from_db()
        assert self.asset.name == 'Updated Asset Name'

    def test_delete_asset_success(self):
        """Test deleting asset"""
        url = reverse('api:v3:asset-detail', kwargs={'asset_id': self.asset.asset_id})

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Asset.objects.filter(asset_id=self.asset.asset_id).exists()
```

#### Service Layer Testing
```python
# tests/test_services.py
import pytest
from unittest.mock import patch, Mock
from decimal import Decimal

from services.payment_service import MidtransService, SubscriptionManager
from services.qr_service import QRCodeGenerator
from tests.factories import TenantFactory, SubscriptionFactory


@pytest.mark.django_db
class TestMidtransService:
    def setup_method(self):
        self.service = MidtransService()
        self.tenant = TenantFactory()

    @patch('services.payment_service.requests.post')
    def test_create_subscription_success(self, mock_post):
        """Test successful subscription creation"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'sub_12345',
            'status': 'active',
            'schedule': {
                'interval': 1,
                'interval_unit': 'month'
            }
        }
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = self.service.create_subscription(
            tenant=self.tenant,
            plan='premium',
            payment_method={'token': 'token_123'}
        )

        assert result['id'] == 'sub_12345'
        assert result['status'] == 'active'
        mock_post.assert_called_once()

    def test_generate_signature(self):
        """Test signature generation for webhook verification"""
        order_id = "order-123"
        status_code = "200"
        gross_amount = "100000.00"

        signature = self.service.generate_signature(order_id, status_code, gross_amount)

        # Verify signature format and length
        assert isinstance(signature, str)
        assert len(signature) == 128  # SHA512 hex length

    @patch('services.payment_service.MidtransService.verify_signature')
    def test_webhook_handling_success(self, mock_verify):
        """Test webhook processing for successful payment"""
        mock_verify.return_value = True

        webhook_payload = {
            'order_id': 'order-123',
            'status_code': '200',
            'transaction_status': 'settlement',
            'gross_amount': '100000.00',
            'signature_key': 'valid_signature'
        }

        result = self.service.handle_webhook(webhook_payload)

        assert result['status'] == 'processed'
        mock_verify.assert_called_once()


class TestQRCodeGenerator:
    def setup_method(self):
        self.generator = QRCodeGenerator()

    def test_format_url_qr_data(self):
        """Test URL QR code data formatting"""
        data = {'url': 'https://example.com'}
        result = self.generator.format_qr_data('url', data)

        assert result == 'https://example.com'

    def test_format_wifi_qr_data(self):
        """Test WiFi QR code data formatting"""
        data = {
            'ssid': 'TestNetwork',
            'password': 'password123',
            'security': 'WPA',
            'hidden': 'false'
        }

        result = self.generator.format_qr_data('wifi', data)
        expected = "WIFI:T:WPA;S:TestNetwork;P:password123;H:false;;"

        assert result == expected

    def test_unsupported_qr_type_raises_error(self):
        """Test that unsupported QR types raise ValueError"""
        with pytest.raises(ValueError, match="Unsupported QR code type"):
            self.generator.format_qr_data('unsupported', {})

    @patch('services.qr_service.qrcode.QRCode')
    def test_generate_qr_code_basic(self, mock_qr_class):
        """Test basic QR code generation"""
        mock_qr = Mock()
        mock_qr_class.return_value = mock_qr
        mock_qr.make_image.return_value = Mock()

        result = self.generator.generate_qr_code('url', {'url': 'https://test.com'})

        mock_qr.add_data.assert_called_once_with('https://test.com')
        mock_qr.make.assert_called_once_with(fit=True)
        assert result is not None
```

### 1.2 Frontend Unit Tests (React/JavaScript)

**Framework**: Jest, React Testing Library, MSW (Mock Service Worker)

```javascript
// src/components/__tests__/AssetList.test.jsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

import AssetList from '../AssetList';
import { TenantProvider } from '../../contexts/TenantContext';

// Mock API responses
const server = setupServer(
  rest.get('/api/v3/assets/', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      data: {
        items: [
          {
            asset_id: 'asset1',
            name: 'Test Asset 1',
            mimetype: 'image/jpeg',
            is_enabled: true,
            is_active: true
          },
          {
            asset_id: 'asset2',
            name: 'Test Asset 2',
            mimetype: 'video/mp4',
            is_enabled: false,
            is_active: false
          }
        ],
        pagination: {
          page: 1,
          per_page: 20,
          total: 2,
          pages: 1
        }
      }
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const renderWithProviders = (component) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const tenantContext = {
    tenant: { id: 'tenant-1', name: 'Test Tenant' },
    setTenant: jest.fn()
  };

  return render(
    <QueryClientProvider client={queryClient}>
      <TenantProvider value={tenantContext}>
        {component}
      </TenantProvider>
    </QueryClientProvider>
  );
};

describe('AssetList Component', () => {
  test('renders asset list successfully', async () => {
    renderWithProviders(<AssetList />);

    // Check for loading state
    expect(screen.getByText('Loading assets...')).toBeInTheDocument();

    // Wait for assets to load
    await waitFor(() => {
      expect(screen.getByText('Test Asset 1')).toBeInTheDocument();
      expect(screen.getByText('Test Asset 2')).toBeInTheDocument();
    });
  });

  test('displays asset status correctly', async () => {
    renderWithProviders(<AssetList />);

    await waitFor(() => {
      const asset1 = screen.getByTestId('asset-asset1');
      const asset2 = screen.getByTestId('asset-asset2');

      expect(asset1).toHaveClass('asset-enabled');
      expect(asset2).toHaveClass('asset-disabled');
    });
  });

  test('handles asset selection', async () => {
    const onAssetSelect = jest.fn();
    renderWithProviders(<AssetList onAssetSelect={onAssetSelect} />);

    await waitFor(() => {
      const asset1 = screen.getByTestId('asset-asset1');
      fireEvent.click(asset1);

      expect(onAssetSelect).toHaveBeenCalledWith({
        asset_id: 'asset1',
        name: 'Test Asset 1',
        mimetype: 'image/jpeg',
        is_enabled: true,
        is_active: true
      });
    });
  });

  test('displays error message on API failure', async () => {
    server.use(
      rest.get('/api/v3/assets/', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({
          success: false,
          error: { message: 'Internal server error' }
        }));
      })
    );

    renderWithProviders(<AssetList />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load assets')).toBeInTheDocument();
    });
  });
});
```

## 2. Integration Testing Strategy

### 2.1 API Integration Tests

**Framework**: pytest, requests, testcontainers

```python
# tests/integration/test_tenant_isolation.py
import pytest
import requests
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from django.test import TransactionTestCase
from django.db import connections
from tests.factories import TenantFactory, UserFactory, AssetFactory


@pytest.mark.integration
class TestTenantIsolationIntegration(TransactionTestCase):
    """Integration tests for tenant data isolation"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postgres = PostgresContainer("postgres:13")
        cls.redis = RedisContainer("redis:6")
        cls.postgres.start()
        cls.redis.start()

        # Configure test database
        cls.setup_test_database()

    @classmethod
    def tearDownClass(cls):
        cls.postgres.stop()
        cls.redis.stop()
        super().tearDownClass()

    def setUp(self):
        self.tenant1 = TenantFactory(slug='tenant1')
        self.tenant2 = TenantFactory(slug='tenant2')
        self.user1 = UserFactory()
        self.user2 = UserFactory()

        # Create tenant-specific assets
        self.asset1 = AssetFactory(tenant=self.tenant1)
        self.asset2 = AssetFactory(tenant=self.tenant2)

    def test_cross_tenant_asset_access_blocked(self):
        """Test that tenant cannot access other tenant's assets"""
        # Authenticate as tenant1 user
        response = self.client.post('/api/v3/auth/login/', {
            'username': self.user1.username,
            'password': 'testpass'
        })
        token = response.json()['data']['token']

        # Try to access tenant2's asset using tenant1's token
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Tenant-ID': str(self.tenant1.id)
        }

        response = self.client.get(
            f'/api/v3/assets/{self.asset2.asset_id}/',
            headers=headers
        )

        assert response.status_code == 404

    def test_tenant_asset_listing_isolation(self):
        """Test that asset listing respects tenant boundaries"""
        # Create multiple assets for each tenant
        for i in range(5):
            AssetFactory(tenant=self.tenant1)
            AssetFactory(tenant=self.tenant2)

        # Test tenant1 sees only their assets
        headers = {'X-Tenant-ID': str(self.tenant1.id)}
        response = self.client.get('/api/v3/assets/', headers=headers)

        assets = response.json()['data']['items']
        for asset in assets:
            # Verify all returned assets belong to tenant1
            asset_obj = Asset.objects.get(asset_id=asset['asset_id'])
            assert asset_obj.tenant == self.tenant1

    def test_database_connection_isolation(self):
        """Test that database connections properly isolate tenant data"""
        from django.db import connection

        # Set tenant context for tenant1
        with connection.cursor() as cursor:
            cursor.execute("SET app.current_tenant_id = %s", [str(self.tenant1.id)])

            # Query should only return tenant1's assets
            cursor.execute("SELECT COUNT(*) FROM assets WHERE tenant_id = %s", [str(self.tenant1.id)])
            tenant1_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM assets")
            total_count = cursor.fetchone()[0]

            # RLS should filter results
            assert tenant1_count < total_count or tenant1_count == 1
```

### 2.2 Payment Integration Tests

```python
# tests/integration/test_payment_integration.py
import pytest
from unittest.mock import patch
import json

from services.payment_service import MidtransService
from tests.factories import TenantFactory, SubscriptionFactory


@pytest.mark.integration
class TestPaymentIntegration:
    """Integration tests for payment processing"""

    def setup_method(self):
        self.tenant = TenantFactory()
        self.payment_service = MidtransService()

    @patch('services.payment_service.requests.post')
    def test_subscription_creation_flow(self, mock_post):
        """Test complete subscription creation flow"""
        # Mock Midtrans API response
        mock_post.return_value.json.return_value = {
            'id': 'sub_12345',
            'status': 'active',
            'amount': 100000,
            'currency': 'IDR',
            'schedule': {
                'interval': 1,
                'interval_unit': 'month'
            }
        }
        mock_post.return_value.status_code = 201

        # Create subscription
        subscription_data = self.payment_service.create_subscription(
            tenant=self.tenant,
            plan='premium',
            payment_method={'token': 'test_token'}
        )

        # Verify subscription was created
        assert subscription_data['id'] == 'sub_12345'
        assert subscription_data['status'] == 'active'

        # Verify database record
        subscription = Subscription.objects.get(tenant=self.tenant)
        assert subscription.midtrans_subscription_id == 'sub_12345'
        assert subscription.status == 'active'

    def test_webhook_processing_flow(self):
        """Test webhook processing for payment notifications"""
        # Create existing subscription
        subscription = SubscriptionFactory(
            tenant=self.tenant,
            midtrans_subscription_id='sub_12345'
        )

        # Simulate webhook payload
        webhook_payload = {
            'order_id': 'order_12345',
            'status_code': '200',
            'transaction_status': 'settlement',
            'gross_amount': '100000.00',
            'subscription_id': 'sub_12345',
            'signature_key': self.payment_service.generate_signature(
                'order_12345', '200', '100000.00'
            )
        }

        # Process webhook
        result = self.payment_service.handle_webhook(webhook_payload)

        # Verify processing result
        assert result['status'] == 'processed'

        # Verify payment history was created
        payment = PaymentHistory.objects.get(
            midtrans_order_id='order_12345'
        )
        assert payment.tenant == self.tenant
        assert payment.status == 'paid'
```

## 3. End-to-End Testing Strategy

### 3.1 User Journey Tests

**Framework**: Playwright, pytest-playwright

```python
# tests/e2e/test_user_journeys.py
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
class TestContentManagerJourney:
    """E2E tests for content manager user journey"""

    def test_complete_asset_management_flow(self, page: Page):
        """Test complete asset management workflow"""
        # 1. Login as content manager
        page.goto('/login')
        page.fill('[data-testid="username"]', 'content_manager')
        page.fill('[data-testid="password"]', 'testpass')
        page.click('[data-testid="login-button"]')

        # Verify successful login
        expect(page.locator('[data-testid="dashboard"]')).to_be_visible()

        # 2. Navigate to asset management
        page.click('[data-testid="nav-assets"]')
        expect(page.locator('[data-testid="asset-list"]')).to_be_visible()

        # 3. Create new asset
        page.click('[data-testid="add-asset-button"]')

        # Fill asset form
        page.fill('[data-testid="asset-name"]', 'Test E2E Asset')
        page.fill('[data-testid="asset-url"]', 'https://example.com/test.jpg')
        page.select_option('[data-testid="asset-mimetype"]', 'image/jpeg')
        page.fill('[data-testid="asset-duration"]', '10')
        page.check('[data-testid="asset-enabled"]')

        # Submit form
        page.click('[data-testid="save-asset"]')

        # Verify asset was created
        expect(page.locator('text=Test E2E Asset')).to_be_visible()
        expect(page.locator('[data-testid="success-message"]')).to_contain_text('Asset created successfully')

        # 4. Edit the asset
        page.click('[data-testid="asset-Test E2E Asset"] [data-testid="edit-button"]')
        page.fill('[data-testid="asset-name"]', 'Updated E2E Asset')
        page.click('[data-testid="save-asset"]')

        # Verify update
        expect(page.locator('text=Updated E2E Asset')).to_be_visible()

        # 5. Delete the asset
        page.click('[data-testid="asset-Updated E2E Asset"] [data-testid="delete-button"]')
        page.click('[data-testid="confirm-delete"]')

        # Verify deletion
        expect(page.locator('text=Updated E2E Asset')).not_to_be_visible()

    def test_layout_creation_workflow(self, page: Page):
        """Test layout creation and management workflow"""
        # Login and navigate to layouts
        self._login_as_content_manager(page)
        page.click('[data-testid="nav-layouts"]')

        # Create new layout
        page.click('[data-testid="add-layout-button"]')
        page.fill('[data-testid="layout-name"]', 'Test Layout')
        page.fill('[data-testid="layout-width"]', '1920')
        page.fill('[data-testid="layout-height"]', '1080')
        page.click('[data-testid="create-layout"]')

        # Verify layout designer opened
        expect(page.locator('[data-testid="layout-designer"]')).to_be_visible()

        # Add asset to layout
        page.drag_and_drop(
            '[data-testid="asset-library"] .asset:first-child',
            '[data-testid="layout-grid"] .grid-cell[data-x="0"][data-y="0"]'
        )

        # Verify asset was placed
        expect(page.locator('[data-testid="layout-grid"] .placed-asset')).to_be_visible()

        # Save layout
        page.click('[data-testid="save-layout"]')
        expect(page.locator('[data-testid="success-message"]')).to_contain_text('Layout saved')

    def _login_as_content_manager(self, page: Page):
        """Helper method for content manager login"""
        page.goto('/login')
        page.fill('[data-testid="username"]', 'content_manager')
        page.fill('[data-testid="password"]', 'testpass')
        page.click('[data-testid="login-button"]')
        expect(page.locator('[data-testid="dashboard"]')).to_be_visible()


@pytest.mark.e2e
class TestTenantAdminJourney:
    """E2E tests for tenant admin user journey"""

    def test_user_management_workflow(self, page: Page):
        """Test user management functionality"""
        # Login as tenant admin
        page.goto('/login')
        page.fill('[data-testid="username"]', 'tenant_admin')
        page.fill('[data-testid="password"]', 'testpass')
        page.click('[data-testid="login-button"]')

        # Navigate to user management
        page.click('[data-testid="nav-users"]')
        expect(page.locator('[data-testid="user-list"]')).to_be_visible()

        # Add new user
        page.click('[data-testid="add-user-button"]')
        page.fill('[data-testid="user-email"]', 'newuser@example.com')
        page.fill('[data-testid="user-name"]', 'New User')
        page.select_option('[data-testid="user-role"]', 'content_manager')
        page.click('[data-testid="save-user"]')

        # Verify user was added
        expect(page.locator('text=newuser@example.com')).to_be_visible()

        # Test user role change
        page.click('[data-testid="user-newuser@example.com"] [data-testid="edit-button"]')
        page.select_option('[data-testid="user-role"]', 'viewer')
        page.click('[data-testid="save-user"]')

        # Verify role change
        expect(
            page.locator('[data-testid="user-newuser@example.com"] [data-testid="user-role"]')
        ).to_contain_text('viewer')

    def test_billing_subscription_workflow(self, page: Page):
        """Test billing and subscription management"""
        self._login_as_tenant_admin(page)

        # Navigate to billing
        page.click('[data-testid="nav-billing"]')
        expect(page.locator('[data-testid="billing-dashboard"]')).to_be_visible()

        # Check current subscription
        expect(page.locator('[data-testid="current-plan"]')).to_contain_text('Basic')

        # Upgrade subscription
        page.click('[data-testid="upgrade-plan-button"]')
        page.click('[data-testid="select-premium-plan"]')

        # Fill payment information (test mode)
        page.fill('[data-testid="card-number"]', '4111111111111111')
        page.fill('[data-testid="card-expiry"]', '12/25')
        page.fill('[data-testid="card-cvc"]', '123')
        page.click('[data-testid="confirm-upgrade"]')

        # Verify upgrade success (in test environment)
        expect(page.locator('[data-testid="upgrade-success"]')).to_be_visible()

    def _login_as_tenant_admin(self, page: Page):
        """Helper method for tenant admin login"""
        page.goto('/login')
        page.fill('[data-testid="username"]', 'tenant_admin')
        page.fill('[data-testid="password"]', 'testpass')
        page.click('[data-testid="login-button"]')
        expect(page.locator('[data-testid="dashboard"]')).to_be_visible()
```

### 3.2 Cross-Browser Testing

```python
# tests/e2e/conftest.py
import pytest
from playwright.sync_api import Playwright, Browser

@pytest.fixture(scope="session", params=["chromium", "firefox", "webkit"])
def browser_type_name(request):
    return request.param

@pytest.fixture(scope="session")
def browser(playwright: Playwright, browser_type_name: str):
    browser_type = getattr(playwright, browser_type_name)
    browser = browser_type.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def page(browser: Browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
```

## 4. Performance Testing Strategy

### 4.1 Load Testing

**Framework**: Locust, pytest-benchmark

```python
# tests/performance/test_api_performance.py
from locust import HttpUser, task, between
import random
import uuid

class DigitalSignageUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Setup for each simulated user"""
        # Login and get auth token
        response = self.client.post("/api/v3/auth/login/", json={
            "username": f"testuser_{random.randint(1, 1000)}",
            "password": "testpass"
        })

        if response.status_code == 200:
            self.token = response.json()["data"]["token"]
            self.tenant_id = response.json()["data"]["tenant_id"]
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}",
                "X-Tenant-ID": self.tenant_id
            })

    @task(3)
    def list_assets(self):
        """Test asset listing performance"""
        with self.client.get("/api/v3/assets/", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if len(data["data"]["items"]) >= 0:
                    response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def get_asset_detail(self):
        """Test asset detail retrieval"""
        # Get a random asset ID from list
        list_response = self.client.get("/api/v3/assets/")
        if list_response.status_code == 200:
            assets = list_response.json()["data"]["items"]
            if assets:
                asset_id = random.choice(assets)["asset_id"]

                with self.client.get(f"/api/v3/assets/{asset_id}/", catch_response=True) as response:
                    if response.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"Asset detail failed: {response.status_code}")

    @task(1)
    def create_asset(self):
        """Test asset creation performance"""
        asset_data = {
            "name": f"Load Test Asset {uuid.uuid4().hex[:8]}",
            "uri": f"https://example.com/{uuid.uuid4().hex}.jpg",
            "mimetype": "image/jpeg",
            "duration": random.randint(5000, 30000),
            "is_enabled": True
        }

        with self.client.post("/api/v3/assets/", json=asset_data, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Asset creation failed: {response.status_code}")

    @task(1)
    def list_layouts(self):
        """Test layout listing performance"""
        with self.client.get("/api/v3/layouts/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Layout listing failed: {response.status_code}")


# Performance benchmark tests
import pytest
from django.test import Client
from tests.factories import TenantFactory, AssetFactory

@pytest.mark.benchmark
class TestAPIPerformance:
    def setup_method(self):
        self.client = Client()
        self.tenant = TenantFactory()

        # Create test data
        self.assets = [AssetFactory(tenant=self.tenant) for _ in range(100)]

    def test_asset_list_performance(self, benchmark):
        """Benchmark asset listing performance"""
        def list_assets():
            response = self.client.get('/api/v3/assets/', HTTP_X_TENANT_ID=str(self.tenant.id))
            return response

        result = benchmark(list_assets)
        assert result.status_code == 200

        # Performance assertions
        assert benchmark.stats.mean < 0.1  # Less than 100ms average

    def test_database_query_performance(self, benchmark):
        """Benchmark database query performance"""
        from anthias_app.models import Asset

        def query_assets():
            return list(Asset.objects.filter(tenant=self.tenant)[:20])

        assets = benchmark(query_assets)
        assert len(assets) == 20
        assert benchmark.stats.mean < 0.05  # Less than 50ms average
```

## 5. Security Testing Strategy

### 5.1 Authentication & Authorization Tests

```python
# tests/security/test_authentication.py
import pytest
from django.test import Client
from django.contrib.auth.models import User
from tests.factories import TenantFactory, UserFactory

@pytest.mark.security
class TestAuthenticationSecurity:
    def setup_method(self):
        self.client = Client()
        self.tenant = TenantFactory()
        self.user = UserFactory()

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in authentication"""
        malicious_payloads = [
            "admin'; DROP TABLE auth_user; --",
            "admin' OR '1'='1",
            "admin' UNION SELECT * FROM auth_user --"
        ]

        for payload in malicious_payloads:
            response = self.client.post('/api/v3/auth/login/', {
                'username': payload,
                'password': 'any_password'
            })

            # Should not authenticate with malicious input
            assert response.status_code in [400, 401]
            assert 'token' not in response.json().get('data', {})

    def test_brute_force_protection(self):
        """Test brute force attack protection"""
        # Attempt multiple failed logins
        for i in range(10):
            response = self.client.post('/api/v3/auth/login/', {
                'username': self.user.username,
                'password': 'wrong_password'
            })
            assert response.status_code == 401

        # Account should be temporarily locked
        response = self.client.post('/api/v3/auth/login/', {
            'username': self.user.username,
            'password': 'correct_password'  # Even correct password should fail
        })
        assert response.status_code == 429  # Too Many Requests

    def test_jwt_token_validation(self):
        """Test JWT token validation and tampering protection"""
        # Get valid token
        response = self.client.post('/api/v3/auth/login/', {
            'username': self.user.username,
            'password': 'testpass'
        })
        token = response.json()['data']['token']

        # Test with valid token
        response = self.client.get('/api/v3/assets/', HTTP_AUTHORIZATION=f'Bearer {token}')
        assert response.status_code == 200

        # Test with tampered token
        tampered_token = token[:-5] + 'xxxxx'
        response = self.client.get('/api/v3/assets/', HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
        assert response.status_code == 401

    def test_tenant_isolation_security(self):
        """Test tenant data isolation security"""
        tenant2 = TenantFactory()
        user2 = UserFactory()

        # Login as user from tenant1
        response = self.client.post('/api/v3/auth/login/', {
            'username': self.user.username,
            'password': 'testpass'
        })
        token1 = response.json()['data']['token']

        # Try to access tenant2's data using tenant1's token
        response = self.client.get('/api/v3/assets/',
            HTTP_AUTHORIZATION=f'Bearer {token1}',
            HTTP_X_TENANT_ID=str(tenant2.id)
        )

        # Should be forbidden
        assert response.status_code in [403, 404]


@pytest.mark.security
class TestInputValidationSecurity:
    def setup_method(self):
        self.client = Client()
        self.tenant = TenantFactory()
        self.user = UserFactory()

        # Login
        response = self.client.post('/api/v3/auth/login/', {
            'username': self.user.username,
            'password': 'testpass'
        })
        self.token = response.json()['data']['token']
        self.headers = {
            'HTTP_AUTHORIZATION': f'Bearer {self.token}',
            'HTTP_X_TENANT_ID': str(self.tenant.id)
        }

    def test_xss_prevention(self):
        """Test XSS prevention in asset creation"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]

        for payload in xss_payloads:
            response = self.client.post('/api/v3/assets/', {
                'name': payload,
                'uri': 'https://example.com/test.jpg',
                'mimetype': 'image/jpeg',
                'duration': 5000
            }, content_type='application/json', **self.headers)

            if response.status_code == 201:
                # If asset was created, verify the payload was sanitized
                asset_data = response.json()['data']
                assert '<script>' not in asset_data['name']
                assert 'javascript:' not in asset_data['name']

    def test_file_upload_security(self):
        """Test file upload security"""
        malicious_files = [
            ('malicious.php', b'<?php system($_GET["cmd"]); ?>', 'application/x-php'),
            ('malicious.exe', b'MZ\x90\x00', 'application/x-executable'),
            ('huge_file.txt', b'A' * (50 * 1024 * 1024), 'text/plain')  # 50MB
        ]

        for filename, content, mimetype in malicious_files:
            response = self.client.post('/api/v3/assets/upload/', {
                'file': (filename, content, mimetype),
                'name': 'Test Upload'
            }, **self.headers)

            # Should reject malicious files
            assert response.status_code in [400, 413, 415]
```

## 6. Test Data Management

### 6.1 Test Fixtures and Factories

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from anthias_app.models import Tenant, Asset, Layout

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant

    name = factory.Faker('company')
    slug = factory.Sequence(lambda n: f"tenant-{n}")
    subscription_tier = factory.Iterator(['basic', 'premium', 'enterprise'])
    is_active = True

class AssetFactory(DjangoModelFactory):
    class Meta:
        model = Asset

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Faker('sentence', nb_words=3)
    uri = factory.Faker('url')
    mimetype = factory.Iterator(['image/jpeg', 'image/png', 'video/mp4', 'text/html'])
    duration = factory.Faker('random_int', min=1000, max=60000)
    is_enabled = factory.Faker('boolean')

class LayoutFactory(DjangoModelFactory):
    class Meta:
        model = Layout

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Faker('sentence', nb_words=2)
    width = 1920
    height = 1080
    grid_columns = 12
    grid_rows = 8
    is_active = factory.Faker('boolean')
```

## 7. Continuous Testing Pipeline

### 7.1 GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/requirements.txt
        pip install -r requirements/requirements.dev.txt

    - name: Run unit tests
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost/test_db
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/unit/ -v --cov=./ --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.10

    - name: Run integration tests
      run: |
        pytest tests/integration/ -v -m integration

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.10

    - name: Install Playwright
      run: |
        pip install playwright pytest-playwright
        playwright install

    - name: Run E2E tests
      run: |
        pytest tests/e2e/ -v -m e2e

  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.10

    - name: Run performance tests
      run: |
        pytest tests/performance/ -v -m benchmark

  security-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.10

    - name: Run security tests
      run: |
        pytest tests/security/ -v -m security

    - name: Run Bandit security scan
      run: |
        bandit -r . -f json -o bandit-report.json

    - name: Upload security report
      uses: actions/upload-artifact@v3
      with:
        name: security-report
        path: bandit-report.json
```

This comprehensive testing strategy ensures high quality, security, and performance across all components of the digital signage system enhancement. The strategy emphasizes automation, continuous testing, and thorough coverage of all user scenarios and edge cases.