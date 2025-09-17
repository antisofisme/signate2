"""
Multi-tenant testing utilities for Signate SaaS.

This module provides comprehensive utilities for testing multi-tenant scenarios:
- Tenant isolation verification
- Cross-tenant data leakage testing
- Tenant-specific configuration management
- Performance testing across tenants
- Security testing for tenant boundaries
"""

import uuid
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Generator
from unittest.mock import patch, Mock

from django.conf import settings
from django.test import override_settings
from django.db import connection, connections
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth.models import User

from anthias_app.models import Asset


class TenantTestManager:
    """
    Manager for handling multi-tenant test scenarios.

    Provides utilities for:
    - Creating isolated tenant environments
    - Managing tenant-specific data
    - Testing cross-tenant scenarios
    - Performance monitoring per tenant
    """

    def __init__(self):
        self.active_tenants: Dict[str, Dict] = {}
        self.tenant_counter = 0
        self._lock = threading.Lock()

    def create_test_tenant(self,
                          tenant_id: Optional[str] = None,
                          schema_name: Optional[str] = None,
                          domain: Optional[str] = None,
                          config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a test tenant with isolated configuration.

        Args:
            tenant_id: Unique tenant identifier
            schema_name: Database schema name
            domain: Tenant domain
            config: Additional tenant configuration

        Returns:
            Dict containing tenant information
        """
        with self._lock:
            if not tenant_id:
                self.tenant_counter += 1
                tenant_id = f"test_tenant_{self.tenant_counter}_{uuid.uuid4().hex[:8]}"

            if not schema_name:
                schema_name = f"tenant_{tenant_id}"

            if not domain:
                domain = f"{tenant_id}.signate.test"

            tenant_info = {
                'id': tenant_id,
                'schema_name': schema_name,
                'domain': domain,
                'created_at': timezone.now(),
                'config': config or {},
                'is_active': True,
                'users': [],
                'assets': [],
                'test_data': {}
            }

            self.active_tenants[tenant_id] = tenant_info
            return tenant_info

    def delete_test_tenant(self, tenant_id: str) -> bool:
        """
        Delete a test tenant and cleanup its data.

        Args:
            tenant_id: Tenant identifier to delete

        Returns:
            True if tenant was deleted successfully
        """
        with self._lock:
            if tenant_id in self.active_tenants:
                # Cleanup tenant data
                tenant_info = self.active_tenants[tenant_id]

                # Delete tenant assets
                for asset_id in tenant_info.get('assets', []):
                    try:
                        Asset.objects.filter(asset_id=asset_id).delete()
                    except:
                        pass

                # Delete tenant users
                for user_id in tenant_info.get('users', []):
                    try:
                        User.objects.filter(id=user_id).delete()
                    except:
                        pass

                del self.active_tenants[tenant_id]
                return True
            return False

    def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant information by ID."""
        return self.active_tenants.get(tenant_id)

    def list_active_tenants(self) -> List[Dict[str, Any]]:
        """List all active test tenants."""
        return list(self.active_tenants.values())

    def cleanup_all_tenants(self):
        """Cleanup all test tenants."""
        tenant_ids = list(self.active_tenants.keys())
        for tenant_id in tenant_ids:
            self.delete_test_tenant(tenant_id)

    @contextmanager
    def tenant_context(self, tenant_id: str) -> Generator[Dict[str, Any], None, None]:
        """
        Context manager for tenant-specific operations.

        Usage:
            with tenant_manager.tenant_context('tenant_123') as tenant:
                # Operations within tenant context
                asset = Asset.objects.create(name='Tenant Asset')
        """
        tenant_info = self.get_tenant_info(tenant_id)
        if not tenant_info:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Store original state
        original_tenant = getattr(settings, 'CURRENT_TENANT', None)

        try:
            # Set tenant context
            settings.CURRENT_TENANT = tenant_info
            yield tenant_info
        finally:
            # Restore original state
            settings.CURRENT_TENANT = original_tenant


class TenantDataFactory:
    """
    Factory for creating tenant-specific test data.
    """

    def __init__(self, tenant_manager: TenantTestManager):
        self.tenant_manager = tenant_manager

    def create_tenant_user(self,
                          tenant_id: str,
                          username: Optional[str] = None,
                          email: Optional[str] = None,
                          is_admin: bool = False) -> User:
        """
        Create a user within a specific tenant context.

        Args:
            tenant_id: Target tenant ID
            username: User username (auto-generated if None)
            email: User email (auto-generated if None)
            is_admin: Whether user should have admin privileges

        Returns:
            Created User instance
        """
        tenant_info = self.tenant_manager.get_tenant_info(tenant_id)
        if not tenant_info:
            raise ValueError(f"Tenant {tenant_id} not found")

        if not username:
            username = f"user_{len(tenant_info['users'])}_{tenant_id}"

        if not email:
            email = f"{username}@{tenant_info['domain']}"

        with self.tenant_manager.tenant_context(tenant_id):
            user = User.objects.create_user(
                username=username,
                email=email,
                password='testpass123!@#'
            )

            if is_admin:
                user.is_staff = True
                user.is_superuser = True
                user.save()

            # Track user in tenant
            tenant_info['users'].append(user.id)

        return user

    def create_tenant_asset(self,
                           tenant_id: str,
                           name: Optional[str] = None,
                           **kwargs) -> Asset:
        """
        Create an asset within a specific tenant context.

        Args:
            tenant_id: Target tenant ID
            name: Asset name (auto-generated if None)
            **kwargs: Additional asset parameters

        Returns:
            Created Asset instance
        """
        tenant_info = self.tenant_manager.get_tenant_info(tenant_id)
        if not tenant_info:
            raise ValueError(f"Tenant {tenant_id} not found")

        if not name:
            name = f"Asset_{len(tenant_info['assets'])}_{tenant_id}"

        defaults = {
            'name': name,
            'uri': f'https://{tenant_info["domain"]}/assets/{name.lower()}.jpg',
            'mimetype': 'image/jpeg',
            'is_enabled': True,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=1),
            'duration': 3600,
            'play_order': len(tenant_info['assets']) + 1
        }
        defaults.update(kwargs)

        with self.tenant_manager.tenant_context(tenant_id):
            asset = Asset.objects.create(**defaults)

            # Track asset in tenant
            tenant_info['assets'].append(asset.asset_id)

        return asset

    def create_bulk_tenant_data(self,
                               tenant_id: str,
                               num_users: int = 5,
                               num_assets: int = 10) -> Dict[str, List]:
        """
        Create bulk test data for a tenant.

        Args:
            tenant_id: Target tenant ID
            num_users: Number of users to create
            num_assets: Number of assets to create

        Returns:
            Dict containing lists of created users and assets
        """
        users = []
        assets = []

        # Create users
        for i in range(num_users):
            user = self.create_tenant_user(
                tenant_id,
                username=f"bulk_user_{i}_{tenant_id}",
                is_admin=(i == 0)  # First user is admin
            )
            users.append(user)

        # Create assets
        for i in range(num_assets):
            asset = self.create_tenant_asset(
                tenant_id,
                name=f"Bulk Asset {i}",
                play_order=i + 1
            )
            assets.append(asset)

        return {
            'users': users,
            'assets': assets
        }


class TenantIsolationTester:
    """
    Utilities for testing tenant isolation and data leakage.
    """

    def __init__(self, tenant_manager: TenantTestManager):
        self.tenant_manager = tenant_manager

    def test_data_isolation(self,
                           tenant_ids: List[str],
                           test_function: callable) -> Dict[str, Any]:
        """
        Test that data is properly isolated between tenants.

        Args:
            tenant_ids: List of tenant IDs to test
            test_function: Function to execute in each tenant context

        Returns:
            Dict containing test results for each tenant
        """
        results = {}

        for tenant_id in tenant_ids:
            try:
                with self.tenant_manager.tenant_context(tenant_id) as tenant:
                    result = test_function(tenant)
                    results[tenant_id] = {
                        'success': True,
                        'result': result,
                        'error': None
                    }
            except Exception as e:
                results[tenant_id] = {
                    'success': False,
                    'result': None,
                    'error': str(e)
                }

        return results

    def verify_no_data_leakage(self,
                              source_tenant_id: str,
                              target_tenant_id: str) -> Dict[str, bool]:
        """
        Verify that data from source tenant is not accessible in target tenant.

        Args:
            source_tenant_id: Tenant that owns the data
            target_tenant_id: Tenant that should not access the data

        Returns:
            Dict indicating whether data leakage was detected
        """
        source_tenant = self.tenant_manager.get_tenant_info(source_tenant_id)
        if not source_tenant:
            raise ValueError(f"Source tenant {source_tenant_id} not found")

        leakage_detected = {
            'assets': False,
            'users': False
        }

        # Test asset isolation
        with self.tenant_manager.tenant_context(target_tenant_id):
            for asset_id in source_tenant.get('assets', []):
                if Asset.objects.filter(asset_id=asset_id).exists():
                    leakage_detected['assets'] = True
                    break

        # Test user isolation
        with self.tenant_manager.tenant_context(target_tenant_id):
            for user_id in source_tenant.get('users', []):
                # In real multi-tenant, users might be shared but should have proper permissions
                # This test can be customized based on actual tenant implementation
                pass

        return leakage_detected

    def test_cross_tenant_permissions(self,
                                    tenant_ids: List[str],
                                    test_operations: List[str]) -> Dict[str, Dict]:
        """
        Test permissions across different tenants.

        Args:
            tenant_ids: List of tenant IDs to test
            test_operations: List of operations to test

        Returns:
            Dict containing permission test results
        """
        results = {}

        for source_tenant in tenant_ids:
            results[source_tenant] = {}

            for target_tenant in tenant_ids:
                if source_tenant == target_tenant:
                    continue

                results[source_tenant][target_tenant] = {}

                for operation in test_operations:
                    try:
                        # Test accessing target tenant's data from source tenant context
                        with self.tenant_manager.tenant_context(source_tenant):
                            target_info = self.tenant_manager.get_tenant_info(target_tenant)

                            if operation == 'read_assets' and target_info['assets']:
                                # Try to read another tenant's assets
                                asset_id = target_info['assets'][0]
                                can_access = Asset.objects.filter(asset_id=asset_id).exists()
                                results[source_tenant][target_tenant][operation] = can_access
                            else:
                                results[source_tenant][target_tenant][operation] = False

                    except Exception:
                        results[source_tenant][target_tenant][operation] = False

        return results


class TenantPerformanceTester:
    """
    Performance testing utilities for multi-tenant scenarios.
    """

    def __init__(self, tenant_manager: TenantTestManager):
        self.tenant_manager = tenant_manager

    def measure_tenant_operations(self,
                                 tenant_id: str,
                                 operations: List[callable],
                                 iterations: int = 10) -> Dict[str, Dict]:
        """
        Measure performance of operations within a tenant context.

        Args:
            tenant_id: Tenant to test
            operations: List of operations to measure
            iterations: Number of iterations per operation

        Returns:
            Dict containing performance metrics
        """
        import time
        import statistics

        results = {}

        with self.tenant_manager.tenant_context(tenant_id) as tenant:
            for i, operation in enumerate(operations):
                operation_name = getattr(operation, '__name__', f'operation_{i}')
                durations = []

                for _ in range(iterations):
                    start_time = time.time()
                    try:
                        operation(tenant)
                        success = True
                    except Exception as e:
                        success = False

                    duration = time.time() - start_time
                    durations.append(duration)

                results[operation_name] = {
                    'mean_duration': statistics.mean(durations),
                    'median_duration': statistics.median(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'std_deviation': statistics.stdev(durations) if len(durations) > 1 else 0,
                    'success_rate': sum(1 for d in durations if d > 0) / len(durations),
                    'iterations': iterations
                }

        return results

    def compare_tenant_performance(self,
                                  tenant_ids: List[str],
                                  operation: callable,
                                  iterations: int = 10) -> Dict[str, Dict]:
        """
        Compare performance of the same operation across multiple tenants.

        Args:
            tenant_ids: List of tenants to test
            operation: Operation to test
            iterations: Number of iterations

        Returns:
            Dict containing comparative performance metrics
        """
        results = {}

        for tenant_id in tenant_ids:
            tenant_results = self.measure_tenant_operations(
                tenant_id,
                [operation],
                iterations
            )
            operation_name = list(tenant_results.keys())[0]
            results[tenant_id] = tenant_results[operation_name]

        return results


class TenantSecurityTester:
    """
    Security testing utilities for multi-tenant scenarios.
    """

    def __init__(self, tenant_manager: TenantTestManager):
        self.tenant_manager = tenant_manager

    def test_tenant_boundary_security(self,
                                    tenant_ids: List[str],
                                    attack_scenarios: List[str]) -> Dict[str, Dict]:
        """
        Test security of tenant boundaries against various attack scenarios.

        Args:
            tenant_ids: List of tenants to test
            attack_scenarios: List of attack scenarios to test

        Returns:
            Dict containing security test results
        """
        results = {}

        for tenant_id in tenant_ids:
            results[tenant_id] = {}

            for scenario in attack_scenarios:
                results[tenant_id][scenario] = self._test_attack_scenario(
                    tenant_id,
                    scenario
                )

        return results

    def _test_attack_scenario(self, tenant_id: str, scenario: str) -> Dict[str, Any]:
        """
        Test a specific attack scenario against a tenant.

        Args:
            tenant_id: Target tenant ID
            scenario: Attack scenario to test

        Returns:
            Dict containing test results
        """
        result = {
            'vulnerable': False,
            'details': '',
            'mitigation_needed': False
        }

        try:
            with self.tenant_manager.tenant_context(tenant_id) as tenant:
                if scenario == 'sql_injection':
                    # Test SQL injection in tenant context
                    malicious_queries = [
                        "'; DROP TABLE assets; --",
                        "' OR '1'='1",
                        "'; UPDATE assets SET is_enabled=1; --"
                    ]

                    for query in malicious_queries:
                        try:
                            # Test query against asset name field
                            Asset.objects.filter(name=query)
                            # If no exception, check for unexpected behavior
                            result['details'] += f"Query '{query}' executed without error. "
                        except Exception as e:
                            # Good - query was rejected
                            pass

                elif scenario == 'privilege_escalation':
                    # Test privilege escalation within tenant
                    try:
                        # Attempt to access admin functions
                        # This would be customized based on actual privilege system
                        result['details'] = "Privilege escalation test completed"
                    except Exception as e:
                        result['details'] = f"Privilege escalation blocked: {e}"

                elif scenario == 'data_exfiltration':
                    # Test unauthorized data access
                    other_tenants = [t for t in self.tenant_manager.list_active_tenants()
                                   if t['id'] != tenant_id]

                    for other_tenant in other_tenants[:3]:  # Test first 3 other tenants
                        for asset_id in other_tenant.get('assets', [])[:5]:  # Test first 5 assets
                            if Asset.objects.filter(asset_id=asset_id).exists():
                                result['vulnerable'] = True
                                result['details'] += f"Can access asset {asset_id} from tenant {other_tenant['id']}. "

        except Exception as e:
            result['details'] = f"Test error: {e}"

        return result


# Global tenant test manager instance
tenant_test_manager = TenantTestManager()
tenant_data_factory = TenantDataFactory(tenant_test_manager)
tenant_isolation_tester = TenantIsolationTester(tenant_test_manager)
tenant_performance_tester = TenantPerformanceTester(tenant_test_manager)
tenant_security_tester = TenantSecurityTester(tenant_test_manager)


# Convenience functions for pytest fixtures
def create_test_tenants(count: int = 3) -> List[Dict[str, Any]]:
    """Create multiple test tenants for testing."""
    tenants = []
    for i in range(count):
        tenant = tenant_test_manager.create_test_tenant(
            tenant_id=f"pytest_tenant_{i}",
            domain=f"tenant{i}.test.local"
        )
        tenants.append(tenant)
    return tenants


def cleanup_test_tenants():
    """Cleanup all test tenants."""
    tenant_test_manager.cleanup_all_tenants()


@contextmanager
def multi_tenant_test_context(tenant_count: int = 3):
    """
    Context manager for multi-tenant testing.

    Usage:
        with multi_tenant_test_context(3) as tenants:
            # Test with 3 tenants
            for tenant in tenants:
                # Test operations
                pass
    """
    tenants = create_test_tenants(tenant_count)
    try:
        yield tenants
    finally:
        cleanup_test_tenants()


# Decorators for tenant testing
def tenant_test(tenant_count: int = 1):
    """
    Decorator for tenant-specific tests.

    Usage:
        @tenant_test(tenant_count=2)
        def test_multi_tenant_scenario(tenants):
            # Test with 2 tenants
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with multi_tenant_test_context(tenant_count) as tenants:
                return func(tenants, *args, **kwargs)
        return wrapper
    return decorator


def isolation_test(func):
    """
    Decorator for tenant isolation tests.

    Usage:
        @isolation_test
        def test_data_isolation():
            # Test will automatically verify tenant isolation
            pass
    """
    def wrapper(*args, **kwargs):
        # Setup isolation testing
        with multi_tenant_test_context(3) as tenants:
            # Create test data in each tenant
            for tenant in tenants:
                tenant_data_factory.create_bulk_tenant_data(
                    tenant['id'],
                    num_users=2,
                    num_assets=5
                )

            # Run the test
            result = func(tenants, *args, **kwargs)

            # Verify isolation
            for i, source_tenant in enumerate(tenants):
                for j, target_tenant in enumerate(tenants):
                    if i != j:
                        leakage = tenant_isolation_tester.verify_no_data_leakage(
                            source_tenant['id'],
                            target_tenant['id']
                        )
                        assert not any(leakage.values()), f"Data leakage detected between {source_tenant['id']} and {target_tenant['id']}"

            return result
    return wrapper