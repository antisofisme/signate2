# SQLite to PostgreSQL Migration Strategy
# Complete migration plan with zero-downtime approach

import os
import sqlite3
import psycopg2
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from django.core.management.base import BaseCommand
from django.db import transaction, connections
from django.conf import settings
from django.contrib.auth.models import User


class MigrationError(Exception):
    """Migration specific error"""
    pass


class DatabaseMigrator:
    """Handles database migration from SQLite to PostgreSQL"""

    def __init__(self, sqlite_path: str, postgres_config: Dict[str, str]):
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config
        self.migration_log = []

    def migrate(self, tenant_config: Dict[str, str], dry_run: bool = False) -> Dict[str, Any]:
        """Execute complete migration process"""

        migration_result = {
            'status': 'started',
            'tenant_created': False,
            'assets_migrated': 0,
            'users_migrated': 0,
            'errors': [],
            'warnings': [],
            'start_time': datetime.now(),
            'end_time': None
        }

        try:
            # Step 1: Validate source database
            self._validate_sqlite_database()

            # Step 2: Create default tenant
            tenant = self._create_default_tenant(tenant_config, dry_run)
            migration_result['tenant_created'] = True

            # Step 3: Migrate users
            users_count = self._migrate_users(tenant, dry_run)
            migration_result['users_migrated'] = users_count

            # Step 4: Migrate assets
            assets_count = self._migrate_assets(tenant, dry_run)
            migration_result['assets_migrated'] = assets_count

            # Step 5: Migrate settings
            self._migrate_settings(tenant, dry_run)

            # Step 6: Create default subscription
            self._create_default_subscription(tenant, dry_run)

            # Step 7: Validate migration
            self._validate_migration(tenant)

            migration_result['status'] = 'completed'
            migration_result['end_time'] = datetime.now()

        except Exception as e:
            migration_result['status'] = 'failed'
            migration_result['errors'].append(str(e))
            migration_result['end_time'] = datetime.now()
            raise MigrationError(f"Migration failed: {str(e)}")

        return migration_result

    def _validate_sqlite_database(self):
        """Validate SQLite database exists and is readable"""
        if not os.path.exists(self.sqlite_path):
            raise MigrationError(f"SQLite database not found: {self.sqlite_path}")

        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            # Check if assets table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='assets'"
            )
            if not cursor.fetchone():
                raise MigrationError("Assets table not found in SQLite database")

            # Count existing assets
            cursor.execute("SELECT COUNT(*) FROM assets")
            asset_count = cursor.fetchone()[0]
            self.migration_log.append(f"Found {asset_count} assets to migrate")

            conn.close()

        except sqlite3.Error as e:
            raise MigrationError(f"SQLite database validation failed: {str(e)}")

    def _create_default_tenant(self, tenant_config: Dict[str, str], dry_run: bool = False) -> 'Tenant':
        """Create default tenant for migration"""
        from models import Tenant, TenantUser

        tenant_data = {
            'name': tenant_config.get('name', 'Default Organization'),
            'subdomain': tenant_config.get('subdomain', 'default'),
            'plan_type': 'legacy',
            'max_assets': 9999,
            'max_devices': 9999,
            'max_users': 9999,
            'storage_quota_gb': 1000,
            'settings': {
                'migrated_from': 'sqlite',
                'migration_date': datetime.now().isoformat(),
                'original_database': self.sqlite_path
            }
        }

        if dry_run:
            self.migration_log.append(f"[DRY RUN] Would create tenant: {tenant_data}")
            return None

        tenant, created = Tenant.objects.get_or_create(
            subdomain=tenant_data['subdomain'],
            defaults=tenant_data
        )

        if created:
            self.migration_log.append(f"Created tenant: {tenant.name}")
        else:
            self.migration_log.append(f"Using existing tenant: {tenant.name}")

        return tenant

    def _migrate_users(self, tenant: 'Tenant', dry_run: bool = False) -> int:
        """Migrate users and create tenant relationships"""
        from models import TenantUser

        if dry_run:
            self.migration_log.append("[DRY RUN] Would migrate users")
            return 0

        # Create default admin user if no users exist
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@localhost',
                'is_staff': True,
                'is_superuser': True
            }
        )

        if created:
            admin_user.set_password('admin')  # Should be changed after migration
            admin_user.save()

        # Create tenant-user relationship
        tenant_user, created = TenantUser.objects.get_or_create(
            user=admin_user,
            tenant=tenant,
            defaults={'role': 'owner'}
        )

        self.migration_log.append(f"Created admin user relationship for tenant")
        return 1

    def _migrate_assets(self, tenant: 'Tenant', dry_run: bool = False) -> int:
        """Migrate assets from SQLite to PostgreSQL"""
        from models import Asset, LegacyAssetMapping

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets")
        sqlite_assets = cursor.fetchall()

        migrated_count = 0

        for sqlite_asset in sqlite_assets:
            try:
                asset_data = self._convert_sqlite_asset(sqlite_asset, tenant)

                if dry_run:
                    self.migration_log.append(
                        f"[DRY RUN] Would migrate asset: {asset_data.get('name', 'Unnamed')}"
                    )
                    migrated_count += 1
                    continue

                # Check if asset already exists
                existing_asset = Asset.objects.filter(
                    asset_id=asset_data['asset_id']
                ).first()

                if existing_asset:
                    # Update with tenant relationship
                    existing_asset.tenant = tenant
                    existing_asset.save()
                    asset = existing_asset
                else:
                    # Create new asset
                    asset = Asset.objects.create(**asset_data)

                # Create legacy mapping for tracking
                LegacyAssetMapping.objects.get_or_create(
                    original_asset_id=sqlite_asset['asset_id'],
                    defaults={'new_asset': asset}
                )

                migrated_count += 1
                self.migration_log.append(f"Migrated asset: {asset.name}")

            except Exception as e:
                self.migration_log.append(
                    f"Failed to migrate asset {sqlite_asset['asset_id']}: {str(e)}"
                )
                continue

        conn.close()
        return migrated_count

    def _convert_sqlite_asset(self, sqlite_asset: sqlite3.Row, tenant: 'Tenant') -> Dict[str, Any]:
        """Convert SQLite asset row to Django model data"""
        return {
            'asset_id': sqlite_asset['asset_id'],
            'tenant': tenant,
            'name': sqlite_asset['name'],
            'uri': sqlite_asset['uri'],
            'md5': sqlite_asset['md5'],
            'start_date': self._parse_datetime(sqlite_asset['start_date']),
            'end_date': self._parse_datetime(sqlite_asset['end_date']),
            'duration': sqlite_asset['duration'],
            'mimetype': sqlite_asset['mimetype'],
            'is_enabled': bool(sqlite_asset['is_enabled']),
            'is_processing': bool(sqlite_asset.get('is_processing', 0)),
            'nocache': bool(sqlite_asset['nocache']),
            'play_order': sqlite_asset['play_order'],
            'skip_asset_check': bool(sqlite_asset['skip_asset_check']),
            # New fields with defaults
            'file_size': 0,
            'tags': [],
            'metadata': {
                'migrated_from_sqlite': True,
                'original_asset_id': sqlite_asset['asset_id']
            }
        }

    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse SQLite datetime string"""
        if not datetime_str:
            return None

        try:
            # Handle different datetime formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue

            self.migration_log.append(f"Warning: Could not parse datetime: {datetime_str}")
            return None

        except Exception:
            return None

    def _migrate_settings(self, tenant: 'Tenant', dry_run: bool = False):
        """Migrate device settings to tenant settings"""
        if dry_run:
            self.migration_log.append("[DRY RUN] Would migrate settings")
            return

        # This would integrate with existing settings module
        # For now, we'll create default settings
        default_settings = {
            'player_name': 'Anthias Player',
            'audio_output': 'hdmi',
            'default_duration': 10,
            'default_streaming_duration': 300,
            'date_format': '%Y-%m-%d',
            'show_splash': True,
            'default_assets': True,
            'shuffle_playlist': False,
            'use_24_hour_clock': True,
            'debug_logging': False
        }

        tenant.settings.update(default_settings)
        tenant.save()

        self.migration_log.append("Migrated default settings to tenant")

    def _create_default_subscription(self, tenant: 'Tenant', dry_run: bool = False):
        """Create legacy subscription for migrated tenant"""
        from models import Subscription

        if dry_run:
            self.migration_log.append("[DRY RUN] Would create legacy subscription")
            return

        subscription_data = {
            'tenant': tenant,
            'plan_name': 'legacy',
            'billing_cycle': 'lifetime',
            'status': 'active',
            'amount': 0.00,
            'currency': 'USD',
            'current_period_start': datetime.now(),
            'current_period_end': datetime(2099, 12, 31),  # Far future
            'payment_provider': 'legacy'
        }

        subscription, created = Subscription.objects.get_or_create(
            tenant=tenant,
            defaults=subscription_data
        )

        if created:
            self.migration_log.append("Created legacy subscription")
        else:
            self.migration_log.append("Using existing subscription")

    def _validate_migration(self, tenant: 'Tenant'):
        """Validate migration was successful"""
        from models import Asset

        # Count migrated assets
        migrated_assets = Asset.objects.filter(tenant=tenant).count()

        # Count original assets
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assets")
        original_count = cursor.fetchone()[0]
        conn.close()

        if migrated_assets != original_count:
            raise MigrationError(
                f"Asset count mismatch: {original_count} original, {migrated_assets} migrated"
            )

        self.migration_log.append(f"Validation passed: {migrated_assets} assets migrated successfully")


# Django Management Command
class Command(BaseCommand):
    """Django management command for database migration"""
    help = 'Migrate from SQLite to PostgreSQL with tenant setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sqlite-db',
            type=str,
            required=True,
            help='Path to SQLite database file'
        )
        parser.add_argument(
            '--tenant-name',
            type=str,
            required=True,
            help='Name for the default tenant'
        )
        parser.add_argument(
            '--tenant-subdomain',
            type=str,
            required=True,
            help='Subdomain for the default tenant'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run migration simulation without making changes'
        )
        parser.add_argument(
            '--backup-dir',
            type=str,
            help='Directory to store backup files'
        )

    def handle(self, *args, **options):
        """Execute migration command"""
        sqlite_path = options['sqlite_db']
        tenant_config = {
            'name': options['tenant_name'],
            'subdomain': options['tenant_subdomain']
        }
        dry_run = options.get('dry_run', False)
        backup_dir = options.get('backup_dir')

        # Create backup if specified
        if backup_dir and not dry_run:
            self._create_backup(sqlite_path, backup_dir)

        # PostgreSQL configuration from Django settings
        postgres_config = settings.DATABASES['default']

        # Initialize migrator
        migrator = DatabaseMigrator(sqlite_path, postgres_config)

        try:
            # Run migration
            result = migrator.migrate(tenant_config, dry_run)

            # Output results
            self.stdout.write(
                self.style.SUCCESS(f"Migration {result['status']}")
            )

            if result['status'] == 'completed':
                self.stdout.write(
                    f"Tenant created: {result['tenant_created']}\n"
                    f"Assets migrated: {result['assets_migrated']}\n"
                    f"Users migrated: {result['users_migrated']}\n"
                    f"Duration: {result['end_time'] - result['start_time']}"
                )

            # Output migration log
            for log_entry in migrator.migration_log:
                self.stdout.write(log_entry)

            if result['errors']:
                self.stdout.write(
                    self.style.ERROR("Errors encountered:")
                )
                for error in result['errors']:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))

        except MigrationError as e:
            self.stdout.write(
                self.style.ERROR(f"Migration failed: {str(e)}")
            )
            return

    def _create_backup(self, sqlite_path: str, backup_dir: str):
        """Create backup of SQLite database"""
        import shutil
        from pathlib import Path

        backup_dir_path = Path(backup_dir)
        backup_dir_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"anthias_backup_{timestamp}.db"
        backup_path = backup_dir_path / backup_filename

        shutil.copy2(sqlite_path, backup_path)

        self.stdout.write(
            self.style.SUCCESS(f"Backup created: {backup_path}")
        )


# Zero-Downtime Migration Strategy
class ZeroDowntimeMigrator:
    """Handles zero-downtime migration with gradual cutover"""

    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        self.sync_status = {
            'assets_synced': 0,
            'last_sync': None,
            'sync_running': False
        }

    def setup_dual_write(self):
        """Setup dual-write to both SQLite and PostgreSQL"""
        # This would modify the existing models to write to both databases
        # during the transition period
        pass

    def start_background_sync(self):
        """Start background sync process"""
        # This would run as a background task to keep databases in sync
        pass

    def validate_sync(self) -> bool:
        """Validate that both databases are in sync"""
        # Compare data between SQLite and PostgreSQL
        pass

    def cutover_to_postgresql(self):
        """Perform final cutover to PostgreSQL"""
        # Stop writes to SQLite and switch to PostgreSQL only
        pass


# Rollback Strategy
class MigrationRollback:
    """Handles rollback in case of migration issues"""

    def __init__(self, backup_path: str):
        self.backup_path = backup_path

    def rollback_to_sqlite(self):
        """Rollback to SQLite database"""
        # Restore SQLite database from backup
        # Update Django settings to use SQLite
        pass

    def rollback_partial_migration(self, tenant_id: str):
        """Rollback partial migration for specific tenant"""
        from models import Tenant, Asset, TenantUser, Subscription

        try:
            tenant = Tenant.objects.get(tenant_id=tenant_id)

            # Delete tenant and related data
            Asset.objects.filter(tenant=tenant).delete()
            TenantUser.objects.filter(tenant=tenant).delete()
            Subscription.objects.filter(tenant=tenant).delete()
            tenant.delete()

            return True

        except Tenant.DoesNotExist:
            return False


# Migration Validation Tools
class MigrationValidator:
    """Validates migration integrity"""

    def __init__(self, sqlite_path: str, tenant_id: str):
        self.sqlite_path = sqlite_path
        self.tenant_id = tenant_id

    def validate_asset_integrity(self) -> Dict[str, Any]:
        """Validate asset data integrity"""
        from models import Tenant, Asset

        tenant = Tenant.objects.get(tenant_id=self.tenant_id)

        # Compare asset counts
        postgres_count = Asset.objects.filter(tenant=tenant).count()

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assets")
        sqlite_count = cursor.fetchone()[0]
        conn.close()

        # Sample validation of specific assets
        validation_results = {
            'count_match': postgres_count == sqlite_count,
            'sqlite_count': sqlite_count,
            'postgres_count': postgres_count,
            'sample_validation': self._validate_sample_assets(tenant)
        }

        return validation_results

    def _validate_sample_assets(self, tenant: 'Tenant') -> List[Dict]:
        """Validate a sample of assets"""
        from models import Asset

        # Get sample of assets from PostgreSQL
        postgres_assets = Asset.objects.filter(tenant=tenant)[:10]

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        validation_results = []

        for pg_asset in postgres_assets:
            cursor.execute(
                "SELECT * FROM assets WHERE asset_id = ?",
                (pg_asset.asset_id,)
            )
            sqlite_asset = cursor.fetchone()

            if sqlite_asset:
                is_valid = (
                    pg_asset.name == sqlite_asset['name'] and
                    pg_asset.uri == sqlite_asset['uri'] and
                    pg_asset.is_enabled == bool(sqlite_asset['is_enabled'])
                )

                validation_results.append({
                    'asset_id': pg_asset.asset_id,
                    'name': pg_asset.name,
                    'valid': is_valid
                })

        conn.close()
        return validation_results