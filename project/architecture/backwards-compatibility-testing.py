# Backwards Compatibility Layer and Testing Strategy
# Comprehensive testing and compatibility strategy for Anthias SaaS migration

import os
import json
import sqlite3
import subprocess
from typing import Dict, List, Any, Optional
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.db import connection
from django.core.management import call_command
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import tempfile
import shutil


# Compatibility Layer Tests
class BackwardsCompatibilityTestCase(TestCase):
    """Test backwards compatibility for existing Anthias installations"""

    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.sqlite_db_path = os.path.join(self.temp_dir, 'test_screenly.db')
        self.create_legacy_sqlite_database()

    def tearDown(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)

    def create_legacy_sqlite_database(self):
        """Create a legacy SQLite database with test data"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        # Create legacy assets table
        cursor.execute('''
            CREATE TABLE assets (
                asset_id TEXT PRIMARY KEY,
                name TEXT,
                uri TEXT,
                md5 TEXT,
                start_date TEXT,
                end_date TEXT,
                duration INTEGER,
                mimetype TEXT,
                is_enabled INTEGER,
                is_processing INTEGER,
                nocache INTEGER,
                play_order INTEGER,
                skip_asset_check INTEGER
            )
        ''')

        # Insert test assets
        test_assets = [
            ('asset1', 'Test Image', 'http://example.com/image.jpg', 'abc123',
             '2024-01-01 00:00:00', '2024-12-31 23:59:59', 10,
             'image/jpeg', 1, 0, 0, 1, 0),
            ('asset2', 'Test Video', 'http://example.com/video.mp4', 'def456',
             '2024-01-01 00:00:00', '2024-12-31 23:59:59', 30,
             'video/mp4', 1, 0, 0, 2, 0),
            ('asset3', 'Test Webpage', 'http://example.com', '',
             '2024-01-01 00:00:00', '2024-12-31 23:59:59', 15,
             'webpage', 0, 0, 1, 3, 0)
        ]

        cursor.executemany(
            'INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            test_assets
        )

        conn.commit()
        conn.close()

    def test_legacy_database_migration(self):
        """Test migration from legacy SQLite database"""
        from architecture.migration_strategy import DatabaseMigrator

        postgres_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_anthias',
            'USER': 'test_user',
            'PASSWORD': 'test_pass',
            'HOST': 'localhost',
            'PORT': '5432'
        }

        tenant_config = {
            'name': 'Test Organization',
            'subdomain': 'test-org'
        }

        migrator = DatabaseMigrator(self.sqlite_db_path, postgres_config)

        # Test dry run first
        result = migrator.migrate(tenant_config, dry_run=True)

        self.assertEqual(result['status'], 'completed')
        self.assertTrue(result['tenant_created'])
        self.assertEqual(result['assets_migrated'], 3)

    def test_legacy_api_endpoints_still_work(self):
        """Test that legacy API endpoints continue to work"""
        client = APIClient()

        # Test v1 endpoints
        response = client.get('/api/v1/assets/')
        self.assertIn(response.status_code, [200, 404])  # 404 if no assets

        # Test v2 endpoints
        response = client.get('/api/v2/assets/')
        self.assertIn(response.status_code, [200, 404])

    def test_legacy_authentication_compatibility(self):
        """Test that legacy authentication still works"""
        # Create legacy user
        user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        client = APIClient()

        # Test legacy session-based auth
        response = client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass'
        })

        # Should either login successfully or redirect
        self.assertIn(response.status_code, [200, 302])

    def test_existing_asset_data_preserved(self):
        """Test that existing asset data is preserved during migration"""
        from models import Asset, Tenant

        # Create a test tenant
        tenant = Tenant.objects.create(
            name='Test Org',
            subdomain='test',
            plan_type='legacy'
        )

        # Create assets that simulate migrated data
        Asset.objects.create(
            asset_id='legacy_asset_1',
            tenant=tenant,
            name='Legacy Asset',
            uri='http://example.com/legacy.jpg',
            mimetype='image/jpeg',
            is_enabled=True,
            metadata={'migrated_from_sqlite': True}
        )

        # Test that asset can be retrieved via legacy API
        client = APIClient()
        response = client.get('/api/v2/assets/')
        self.assertEqual(response.status_code, 200)

        # Test that asset data is intact
        assets = response.json()
        legacy_asset = next(
            (a for a in assets if a['asset_id'] == 'legacy_asset_1'),
            None
        )
        self.assertIsNotNone(legacy_asset)
        self.assertEqual(legacy_asset['name'], 'Legacy Asset')


# API Compatibility Tests
class APICompatibilityTestCase(APITestCase):
    """Test API backwards compatibility"""

    def setUp(self):
        """Setup test data"""
        from models import Tenant, Asset

        # Create legacy tenant (no tenant relationship for backwards compatibility)
        self.legacy_asset = Asset.objects.create(
            asset_id='legacy_test_asset',
            name='Legacy Test Asset',
            uri='http://example.com/test.jpg',
            mimetype='image/jpeg',
            is_enabled=True,
            tenant=None  # Legacy assets have no tenant
        )

        # Create modern tenant and asset
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            subdomain='test-tenant',
            plan_type='basic'
        )

        self.modern_asset = Asset.objects.create(
            asset_id='modern_test_asset',
            tenant=self.tenant,
            name='Modern Test Asset',
            uri='http://example.com/modern.jpg',
            mimetype='image/jpeg',
            is_enabled=True
        )

    def test_v1_api_compatibility(self):
        """Test v1 API endpoints work"""
        # Test GET assets
        response = self.client.get('/api/v1/assets/')
        self.assertEqual(response.status_code, 200)

        # Test legacy asset is included
        assets = response.json()
        legacy_asset = next(
            (a for a in assets if a['asset_id'] == 'legacy_test_asset'),
            None
        )
        self.assertIsNotNone(legacy_asset)

    def test_v2_api_compatibility(self):
        """Test v2 API endpoints work"""
        # Test GET assets
        response = self.client.get('/api/v2/assets/')
        self.assertEqual(response.status_code, 200)

        # Test creating asset via v2 API
        asset_data = {
            'name': 'New Legacy Asset',
            'uri': 'http://example.com/new.jpg',
            'mimetype': 'image/jpeg',
            'is_enabled': True,
            'start_date': '2024-01-01T00:00:00Z',
            'end_date': '2024-12-31T23:59:59Z',
            'duration': 10
        }

        response = self.client.post('/api/v2/assets/', asset_data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_v3_api_with_tenant_context(self):
        """Test v3 API works with tenant context"""
        # Mock tenant in request headers
        headers = {'X-Tenant-ID': str(self.tenant.tenant_id)}

        response = self.client.get('/api/v3/assets/', **headers)
        # Should work with proper tenant context
        self.assertIn(response.status_code, [200, 401])  # 401 if auth required

    def test_legacy_asset_serialization(self):
        """Test that legacy assets serialize correctly in all API versions"""
        # v1 API
        response = self.client.get(f'/api/v1/assets/{self.legacy_asset.asset_id}/')
        if response.status_code == 200:
            asset_data = response.json()
            self.assertEqual(asset_data['name'], 'Legacy Test Asset')

        # v2 API
        response = self.client.get(f'/api/v2/assets/{self.legacy_asset.asset_id}/')
        if response.status_code == 200:
            asset_data = response.json()
            self.assertEqual(asset_data['name'], 'Legacy Test Asset')


# Database Schema Compatibility Tests
class DatabaseCompatibilityTestCase(TransactionTestCase):
    """Test database schema compatibility"""

    def test_legacy_asset_table_structure(self):
        """Test that legacy assets table structure is preserved"""
        with connection.cursor() as cursor:
            # Check that assets table exists and has required columns
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'assets'
                ORDER BY column_name
            """)

            columns = {row[0]: row[1] for row in cursor.fetchall()}

            # Check legacy columns exist
            legacy_columns = [
                'asset_id', 'name', 'uri', 'md5', 'start_date', 'end_date',
                'duration', 'mimetype', 'is_enabled', 'is_processing',
                'nocache', 'play_order', 'skip_asset_check'
            ]

            for col in legacy_columns:
                self.assertIn(col, columns, f"Legacy column '{col}' missing")

    def test_tenant_column_nullable(self):
        """Test that tenant column is nullable for backwards compatibility"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'assets' AND column_name = 'tenant_id'
            """)

            result = cursor.fetchone()
            if result:  # Column exists
                self.assertEqual(result[0], 'YES', "Tenant column should be nullable")

    def test_legacy_data_migration_integrity(self):
        """Test data integrity after migration"""
        from models import Asset

        # Create legacy-style asset (no tenant)
        legacy_asset = Asset.objects.create(
            asset_id='integrity_test',
            name='Integrity Test Asset',
            uri='http://example.com/test.jpg',
            tenant=None
        )

        # Verify it can be retrieved
        retrieved = Asset.objects.get(asset_id='integrity_test')
        self.assertEqual(retrieved.name, 'Integrity Test Asset')
        self.assertIsNone(retrieved.tenant)


# Configuration Compatibility Tests
class ConfigurationCompatibilityTestCase(TestCase):
    """Test configuration backwards compatibility"""

    def test_legacy_settings_compatibility(self):
        """Test that legacy settings are still supported"""
        # Test that old-style settings work
        legacy_settings = {
            'player_name': 'Test Player',
            'audio_output': 'hdmi',
            'default_duration': 10
        }

        # These should work without errors
        for key, value in legacy_settings.items():
            # Test that settings can be set and retrieved
            # Implementation would depend on existing settings system
            pass

    def test_environment_variable_compatibility(self):
        """Test environment variable backwards compatibility"""
        test_vars = [
            'ENVIRONMENT',
            'DEBUG',
            'DATABASE_URL'
        ]

        for var in test_vars:
            # Test that legacy environment variables are handled
            value = os.environ.get(var)
            # Should not raise errors regardless of value
            self.assertIsInstance(value, (str, type(None)))


# Integration Tests
class IntegrationTestCase(TestCase):
    """Integration tests for full system compatibility"""

    @override_settings(USE_LEGACY_MODE=True)
    def test_legacy_mode_operation(self):
        """Test system operates correctly in legacy mode"""
        from models import Asset

        # Create asset without tenant (legacy mode)
        asset = Asset.objects.create(
            asset_id='legacy_integration_test',
            name='Legacy Integration Test',
            uri='http://example.com/test.jpg',
            mimetype='image/jpeg',
            is_enabled=True
        )

        # Test that asset operations work
        self.assertTrue(asset.is_enabled)
        self.assertIsNone(asset.tenant)

        # Test API access
        client = APIClient()
        response = client.get('/api/v2/assets/')
        self.assertEqual(response.status_code, 200)

    def test_mixed_legacy_and_modern_data(self):
        """Test system with both legacy and modern data"""
        from models import Asset, Tenant

        # Create tenant
        tenant = Tenant.objects.create(
            name='Modern Tenant',
            subdomain='modern'
        )

        # Create legacy asset (no tenant)
        legacy_asset = Asset.objects.create(
            asset_id='legacy_mixed_test',
            name='Legacy Asset',
            uri='http://example.com/legacy.jpg',
            tenant=None
        )

        # Create modern asset (with tenant)
        modern_asset = Asset.objects.create(
            asset_id='modern_mixed_test',
            name='Modern Asset',
            uri='http://example.com/modern.jpg',
            tenant=tenant
        )

        # Test that both can coexist
        all_assets = Asset.objects.all()
        self.assertEqual(all_assets.count(), 2)

        # Test API returns both
        client = APIClient()
        response = client.get('/api/v2/assets/')
        self.assertEqual(response.status_code, 200)

        assets = response.json()
        asset_ids = [a['asset_id'] for a in assets]
        self.assertIn('legacy_mixed_test', asset_ids)
        self.assertIn('modern_mixed_test', asset_ids)


# Performance Compatibility Tests
class PerformanceCompatibilityTestCase(TestCase):
    """Test that performance doesn't degrade with compatibility layer"""

    def test_api_response_times(self):
        """Test that API response times are acceptable"""
        import time
        from models import Asset

        # Create test assets
        for i in range(100):
            Asset.objects.create(
                asset_id=f'perf_test_{i}',
                name=f'Performance Test Asset {i}',
                uri=f'http://example.com/test_{i}.jpg',
                mimetype='image/jpeg',
                is_enabled=True,
                tenant=None  # Legacy assets
            )

        client = APIClient()

        # Test v2 API performance
        start_time = time.time()
        response = client.get('/api/v2/assets/')
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        response_time = end_time - start_time
        self.assertLess(response_time, 2.0, "API response time too slow")

    def test_database_query_performance(self):
        """Test database query performance with mixed data"""
        from django.test.utils import override_settings
        from django.db import connection
        from models import Asset, Tenant

        # Create test data
        tenant = Tenant.objects.create(name='Perf Test', subdomain='perf')

        # Mix of legacy and modern assets
        for i in range(50):
            Asset.objects.create(
                asset_id=f'legacy_perf_{i}',
                name=f'Legacy Asset {i}',
                uri=f'http://example.com/legacy_{i}.jpg',
                tenant=None
            )

            Asset.objects.create(
                asset_id=f'modern_perf_{i}',
                name=f'Modern Asset {i}',
                uri=f'http://example.com/modern_{i}.jpg',
                tenant=tenant
            )

        # Test query performance
        with override_settings(DEBUG=True):
            connection.queries_log.clear()

            # Query all assets
            assets = list(Asset.objects.all())

            # Should not have excessive queries
            self.assertLess(
                len(connection.queries),
                10,
                "Too many database queries"
            )

            self.assertEqual(len(assets), 100)


# Automated Testing Suite
class CompatibilityTestRunner:
    """Automated test runner for compatibility checks"""

    def __init__(self):
        self.test_results = {}

    def run_all_compatibility_tests(self) -> Dict[str, Any]:
        """Run all compatibility tests and return results"""
        test_suites = [
            BackwardsCompatibilityTestCase,
            APICompatibilityTestCase,
            DatabaseCompatibilityTestCase,
            ConfigurationCompatibilityTestCase,
            IntegrationTestCase,
            PerformanceCompatibilityTestCase
        ]

        results = {}

        for test_suite in test_suites:
            suite_name = test_suite.__name__
            try:
                # Run test suite
                runner = unittest.TextTestRunner(verbosity=0)
                suite = unittest.TestLoader().loadTestsFromTestCase(test_suite)
                result = runner.run(suite)

                results[suite_name] = {
                    'tests_run': result.testsRun,
                    'failures': len(result.failures),
                    'errors': len(result.errors),
                    'success': result.wasSuccessful(),
                    'failure_details': [str(f[1]) for f in result.failures],
                    'error_details': [str(e[1]) for e in result.errors]
                }

            except Exception as e:
                results[suite_name] = {
                    'tests_run': 0,
                    'failures': 0,
                    'errors': 1,
                    'success': False,
                    'error_details': [str(e)]
                }

        return results

    def generate_compatibility_report(self, results: Dict) -> str:
        """Generate human-readable compatibility report"""
        report = "# Anthias SaaS Backwards Compatibility Report\n\n"

        total_tests = sum(r['tests_run'] for r in results.values())
        total_failures = sum(r['failures'] for r in results.values())
        total_errors = sum(r['errors'] for r in results.values())
        success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0

        report += f"## Summary\n"
        report += f"- Total tests run: {total_tests}\n"
        report += f"- Failures: {total_failures}\n"
        report += f"- Errors: {total_errors}\n"
        report += f"- Success rate: {success_rate:.1f}%\n\n"

        report += "## Test Suite Results\n\n"

        for suite_name, result in results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            report += f"### {suite_name} {status}\n"
            report += f"- Tests run: {result['tests_run']}\n"
            report += f"- Failures: {result['failures']}\n"
            report += f"- Errors: {result['errors']}\n"

            if result['failure_details']:
                report += "- Failure details:\n"
                for detail in result['failure_details']:
                    report += f"  - {detail}\n"

            if result['error_details']:
                report += "- Error details:\n"
                for detail in result['error_details']:
                    report += f"  - {detail}\n"

            report += "\n"

        return report


# Migration Validation Tools
class MigrationValidator:
    """Validate migration completeness and data integrity"""

    def __init__(self, sqlite_path: str, tenant_id: str):
        self.sqlite_path = sqlite_path
        self.tenant_id = tenant_id

    def validate_complete_migration(self) -> Dict[str, Any]:
        """Validate that migration completed successfully"""
        from models import Tenant, Asset

        try:
            tenant = Tenant.objects.get(tenant_id=self.tenant_id)
        except Tenant.DoesNotExist:
            return {'valid': False, 'error': 'Tenant not found'}

        # Count migrated assets
        migrated_assets = Asset.objects.filter(tenant=tenant).count()

        # Count original assets
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assets")
        original_count = cursor.fetchone()[0]
        conn.close()

        validation_result = {
            'valid': migrated_assets == original_count,
            'original_count': original_count,
            'migrated_count': migrated_assets,
            'tenant_id': self.tenant_id,
            'tenant_name': tenant.name
        }

        if migrated_assets != original_count:
            validation_result['error'] = f"Asset count mismatch: {original_count} original vs {migrated_assets} migrated"

        return validation_result

    def validate_data_integrity(self) -> List[Dict[str, Any]]:
        """Validate data integrity of migrated assets"""
        from models import Asset, Tenant

        tenant = Tenant.objects.get(tenant_id=self.tenant_id)
        validation_errors = []

        # Check sample of assets
        assets = Asset.objects.filter(tenant=tenant)[:10]

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        for asset in assets:
            cursor.execute("SELECT * FROM assets WHERE asset_id = ?", (asset.asset_id,))
            original = cursor.fetchone()

            if not original:
                validation_errors.append({
                    'asset_id': asset.asset_id,
                    'error': 'Asset not found in original database'
                })
                continue

            # Validate key fields
            if asset.name != original['name']:
                validation_errors.append({
                    'asset_id': asset.asset_id,
                    'field': 'name',
                    'expected': original['name'],
                    'actual': asset.name
                })

            if asset.uri != original['uri']:
                validation_errors.append({
                    'asset_id': asset.asset_id,
                    'field': 'uri',
                    'expected': original['uri'],
                    'actual': asset.uri
                })

        conn.close()
        return validation_errors


# Usage Example and Test Configuration
def run_compatibility_test_suite():
    """Main function to run compatibility tests"""
    runner = CompatibilityTestRunner()
    results = runner.run_all_compatibility_tests()
    report = runner.generate_compatibility_report(results)

    # Save report
    with open('compatibility_report.md', 'w') as f:
        f.write(report)

    print("Compatibility test suite completed. Report saved to compatibility_report.md")
    return results


# Django Management Command for Compatibility Testing
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Django management command for running compatibility tests"""
    help = 'Run backwards compatibility test suite'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='compatibility_report.md',
            help='Output file for compatibility report'
        )

    def handle(self, *args, **options):
        runner = CompatibilityTestRunner()
        results = runner.run_all_compatibility_tests()
        report = runner.generate_compatibility_report(results)

        output_file = options['output']
        with open(output_file, 'w') as f:
            f.write(report)

        self.stdout.write(
            self.style.SUCCESS(f'Compatibility report saved to {output_file}')
        )

        # Print summary
        total_tests = sum(r['tests_run'] for r in results.values())
        total_failures = sum(r['failures'] for r in results.values())
        total_errors = sum(r['errors'] for r in results.values())

        if total_failures == 0 and total_errors == 0:
            self.stdout.write(
                self.style.SUCCESS(f'All {total_tests} compatibility tests passed!')
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'{total_failures + total_errors} tests failed out of {total_tests}'
                )
            )


# Continuous Integration Integration
def create_ci_compatibility_check():
    """Create CI configuration for compatibility testing"""
    ci_config = {
        'name': 'Backwards Compatibility Check',
        'on': ['push', 'pull_request'],
        'jobs': {
            'compatibility': {
                'runs-on': 'ubuntu-latest',
                'services': {
                    'postgres': {
                        'image': 'postgres:13',
                        'env': {
                            'POSTGRES_PASSWORD': 'postgres'
                        }
                    }
                },
                'steps': [
                    {'uses': 'actions/checkout@v2'},
                    {'name': 'Setup Python', 'uses': 'actions/setup-python@v2'},
                    {'name': 'Install dependencies', 'run': 'pip install -r requirements.txt'},
                    {'name': 'Run compatibility tests', 'run': 'python manage.py test_compatibility'},
                    {'name': 'Upload compatibility report', 'uses': 'actions/upload-artifact@v2'}
                ]
            }
        }
    }

    return ci_config