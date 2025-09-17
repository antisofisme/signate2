#!/usr/bin/env python3
"""
Emergency Migration Rollback Script
Automated rollback procedures for SQLite to PostgreSQL migration
"""

import os
import sys
import json
import sqlite3
import psycopg2
import shutil
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/rollback.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RollbackConfig:
    """Rollback configuration settings"""
    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    postgres_db: str = 'anthias'
    postgres_user: str = 'anthias_user'
    postgres_password: str = ''
    tenant_id: str = 'default'
    backup_path: str = ''
    original_db_path: str = ''
    rollback_timeout_minutes: int = 5
    verify_rollback: bool = True
    preserve_postgres_data: bool = False
    emergency_mode: bool = False

@dataclass
class RollbackResult:
    """Rollback operation result"""
    success: bool
    rollback_id: str
    timestamp: datetime
    duration: float
    steps_completed: List[str]
    steps_failed: List[str]
    data_restored: bool
    postgres_cleaned: bool
    backup_verified: bool
    error_message: str = ''
    recommendations: List[str] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []

class RollbackError(Exception):
    """Custom exception for rollback errors"""
    pass

class BackupManager:
    """Backup verification and restoration manager"""

    @staticmethod
    def verify_backup_integrity(backup_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Verify backup file integrity before rollback"""
        logger.info(f"Verifying backup integrity: {backup_path}")

        verification_result = {
            'file_exists': False,
            'file_size': 0,
            'readable': False,
            'sqlite_valid': False,
            'metadata_available': False,
            'checksum_verified': False
        }

        try:
            # Check if backup file exists
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False, verification_result

            verification_result['file_exists'] = True
            verification_result['file_size'] = os.path.getsize(backup_path)

            # Check if file is readable
            try:
                with open(backup_path, 'rb') as f:
                    f.read(1024)  # Try to read first 1KB
                verification_result['readable'] = True
            except Exception as e:
                logger.error(f"Backup file is not readable: {e}")
                return False, verification_result

            # Handle compressed backups
            actual_backup_path = backup_path
            temp_extracted = False

            if backup_path.endswith('.gz'):
                import gzip
                temp_backup_path = backup_path[:-3] + '_temp'
                try:
                    with gzip.open(backup_path, 'rb') as f_in:
                        with open(temp_backup_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    actual_backup_path = temp_backup_path
                    temp_extracted = True
                except Exception as e:
                    logger.error(f"Failed to extract compressed backup: {e}")
                    return False, verification_result

            # Verify SQLite database integrity
            try:
                with sqlite3.connect(actual_backup_path) as conn:
                    cursor = conn.cursor()

                    # Check database integrity
                    cursor.execute("PRAGMA integrity_check")
                    integrity_result = cursor.fetchone()[0]

                    if integrity_result == "ok":
                        verification_result['sqlite_valid'] = True

                        # Check if assets table exists and has data
                        cursor.execute("SELECT COUNT(*) FROM assets")
                        asset_count = cursor.fetchone()[0]
                        logger.info(f"Backup contains {asset_count} assets")

                        if asset_count == 0:
                            logger.warning("Backup database contains no assets")
                    else:
                        logger.error(f"Backup database integrity check failed: {integrity_result}")

            except Exception as e:
                logger.error(f"SQLite verification failed: {e}")
            finally:
                # Clean up temporary extracted file
                if temp_extracted and os.path.exists(actual_backup_path):
                    try:
                        os.remove(actual_backup_path)
                    except Exception:
                        pass

            # Check for metadata file
            metadata_path = backup_path + '.metadata.json'
            if os.path.exists(metadata_path):
                verification_result['metadata_available'] = True

                # Verify checksum if metadata contains it
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)

                    if 'file_info' in metadata and 'checksum_sha256' in metadata['file_info']:
                        expected_checksum = metadata['file_info']['checksum_sha256']
                        actual_checksum = BackupManager._calculate_checksum(backup_path)

                        verification_result['checksum_verified'] = expected_checksum == actual_checksum
                        if not verification_result['checksum_verified']:
                            logger.error("Backup checksum verification failed")
                        else:
                            logger.info("Backup checksum verification passed")

                except Exception as e:
                    logger.warning(f"Failed to verify backup checksum: {e}")

            # Overall verification
            is_valid = (verification_result['file_exists'] and
                       verification_result['readable'] and
                       verification_result['sqlite_valid'])

            if is_valid:
                logger.info("Backup integrity verification PASSED")
            else:
                logger.error("Backup integrity verification FAILED")

            return is_valid, verification_result

        except Exception as e:
            logger.error(f"Backup verification error: {e}")
            return False, verification_result

    @staticmethod
    def _calculate_checksum(file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        import hashlib
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    @staticmethod
    def restore_from_backup(backup_path: str, target_path: str) -> bool:
        """Restore database from backup"""
        logger.info(f"Restoring database from backup: {backup_path} -> {target_path}")

        try:
            # Ensure target directory exists
            target_dir = os.path.dirname(target_path)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            # Handle compressed backups
            if backup_path.endswith('.gz'):
                import gzip
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(target_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, target_path)

            # Verify restored file
            if os.path.exists(target_path):
                with sqlite3.connect(target_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM assets")
                    count = cursor.fetchone()[0]
                    logger.info(f"Restored database contains {count} assets")

                logger.info("Database restoration completed successfully")
                return True
            else:
                logger.error("Restored database file not found")
                return False

        except Exception as e:
            logger.error(f"Database restoration failed: {e}")
            return False

class PostgreSQLCleaner:
    """PostgreSQL cleanup and data removal manager"""

    def __init__(self, config: RollbackConfig):
        self.config = config
        self.tenant_table = f"{config.tenant_id}_assets"

    def cleanup_migration_data(self) -> Tuple[bool, Dict[str, Any]]:
        """Clean up migrated data from PostgreSQL"""
        logger.info(f"Cleaning up PostgreSQL migration data for tenant: {self.config.tenant_id}")

        cleanup_result = {
            'tables_dropped': [],
            'indexes_dropped': [],
            'data_backed_up': False,
            'total_records_removed': 0
        }

        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()

                # Backup data before deletion if requested
                if self.config.preserve_postgres_data:
                    backup_table = f"{self.tenant_table}_rollback_backup_{int(time.time())}"
                    try:
                        cursor.execute(f"""
                            CREATE TABLE {backup_table} AS
                            SELECT * FROM {self.tenant_table}
                        """)
                        cleanup_result['data_backed_up'] = True
                        cleanup_result['backup_table'] = backup_table
                        logger.info(f"Data backed up to table: {backup_table}")
                    except Exception as e:
                        logger.warning(f"Failed to backup data: {e}")

                # Count records before deletion
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {self.tenant_table}")
                    cleanup_result['total_records_removed'] = cursor.fetchone()[0]
                except Exception:
                    cleanup_result['total_records_removed'] = 0

                # Drop indexes
                expected_indexes = [
                    f"idx_{self.config.tenant_id}_assets_enabled",
                    f"idx_{self.config.tenant_id}_assets_dates",
                    f"idx_{self.config.tenant_id}_assets_order"
                ]

                for index_name in expected_indexes:
                    try:
                        cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                        cleanup_result['indexes_dropped'].append(index_name)
                        logger.info(f"Dropped index: {index_name}")
                    except Exception as e:
                        logger.warning(f"Failed to drop index {index_name}: {e}")

                # Drop main table
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {self.tenant_table}")
                    cleanup_result['tables_dropped'].append(self.tenant_table)
                    logger.info(f"Dropped table: {self.tenant_table}")
                except Exception as e:
                    logger.error(f"Failed to drop table {self.tenant_table}: {e}")
                    return False, cleanup_result

                conn.commit()
                logger.info("PostgreSQL cleanup completed successfully")
                return True, cleanup_result

        except Exception as e:
            logger.error(f"PostgreSQL cleanup failed: {e}")
            return False, cleanup_result

    def verify_cleanup(self) -> bool:
        """Verify that cleanup was successful"""
        logger.info("Verifying PostgreSQL cleanup...")

        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()

                # Check if table still exists
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = '{self.tenant_table}'
                    )
                """)
                table_exists = cursor.fetchone()[0]

                if table_exists:
                    logger.error(f"Table {self.tenant_table} still exists after cleanup")
                    return False

                # Check if indexes still exist
                cursor.execute(f"""
                    SELECT COUNT(*) FROM pg_indexes
                    WHERE tablename = '{self.tenant_table}'
                """)
                index_count = cursor.fetchone()[0]

                if index_count > 0:
                    logger.warning(f"Found {index_count} remaining indexes for {self.tenant_table}")

                logger.info("PostgreSQL cleanup verification passed")
                return True

        except Exception as e:
            logger.error(f"Cleanup verification failed: {e}")
            return False

    def _get_postgres_connection(self):
        """Get PostgreSQL connection"""
        try:
            conn_params = {
                'host': self.config.postgres_host,
                'port': self.config.postgres_port,
                'database': self.config.postgres_db,
                'user': self.config.postgres_user,
                'password': self.config.postgres_password,
                'connect_timeout': 10
            }

            return psycopg2.connect(**conn_params)
        except Exception as e:
            raise RollbackError(f"Failed to connect to PostgreSQL: {e}")

class RollbackOrchestrator:
    """Main rollback orchestration class"""

    def __init__(self, config: RollbackConfig):
        self.config = config
        self.postgres_cleaner = PostgreSQLCleaner(config)
        self.rollback_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    def execute_emergency_rollback(self) -> RollbackResult:
        """Execute emergency rollback procedure"""
        logger.info("Starting EMERGENCY migration rollback...")

        start_time = time.time()
        steps_completed = []
        steps_failed = []

        # Initialize result
        result = RollbackResult(
            success=False,
            rollback_id=self.rollback_id,
            timestamp=datetime.now(),
            duration=0.0,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            data_restored=False,
            postgres_cleaned=False,
            backup_verified=False
        )

        try:
            # Step 1: Verify backup integrity
            logger.info("Step 1: Verifying backup integrity...")
            if self.config.backup_path:
                backup_valid, verification_details = BackupManager.verify_backup_integrity(self.config.backup_path)
                result.backup_verified = backup_valid

                if backup_valid:
                    steps_completed.append("backup_verification")
                    logger.info("Backup verification PASSED")
                else:
                    steps_failed.append("backup_verification")
                    result.error_message = f"Backup verification failed: {verification_details}"
                    logger.error(result.error_message)

                    if not self.config.emergency_mode:
                        return result
            else:
                steps_completed.append("backup_verification_skipped")
                logger.warning("No backup path provided, skipping backup verification")

            # Step 2: Clean up PostgreSQL data
            logger.info("Step 2: Cleaning up PostgreSQL migration data...")
            cleanup_success, cleanup_details = self.postgres_cleaner.cleanup_migration_data()

            if cleanup_success:
                steps_completed.append("postgres_cleanup")
                result.postgres_cleaned = True
                logger.info(f"PostgreSQL cleanup completed: {cleanup_details['total_records_removed']} records removed")
            else:
                steps_failed.append("postgres_cleanup")
                logger.error("PostgreSQL cleanup failed")

                if not self.config.emergency_mode:
                    result.error_message = "PostgreSQL cleanup failed"
                    return result

            # Step 3: Restore original database (if backup available)
            if self.config.backup_path and self.config.original_db_path:
                logger.info("Step 3: Restoring original database from backup...")

                # Create backup of current state before restoration
                current_backup_path = f"{self.config.original_db_path}.pre_rollback_{self.rollback_id}"
                try:
                    if os.path.exists(self.config.original_db_path):
                        shutil.copy2(self.config.original_db_path, current_backup_path)
                        logger.info(f"Current database backed up to: {current_backup_path}")
                except Exception as e:
                    logger.warning(f"Failed to backup current database: {e}")

                # Restore from backup
                restore_success = BackupManager.restore_from_backup(
                    self.config.backup_path,
                    self.config.original_db_path
                )

                if restore_success:
                    steps_completed.append("database_restoration")
                    result.data_restored = True
                    logger.info("Database restoration completed")
                else:
                    steps_failed.append("database_restoration")
                    logger.error("Database restoration failed")

                    # Attempt to restore previous state
                    if os.path.exists(current_backup_path):
                        try:
                            shutil.copy2(current_backup_path, self.config.original_db_path)
                            logger.info("Previous database state restored")
                        except Exception as e:
                            logger.error(f"Failed to restore previous state: {e}")

                    if not self.config.emergency_mode:
                        result.error_message = "Database restoration failed"
                        return result
            else:
                steps_completed.append("database_restoration_skipped")
                logger.info("No restoration paths provided, skipping database restoration")

            # Step 4: Verify rollback success
            if self.config.verify_rollback:
                logger.info("Step 4: Verifying rollback success...")

                verification_success = True

                # Verify PostgreSQL cleanup
                if result.postgres_cleaned:
                    cleanup_verified = self.postgres_cleaner.verify_cleanup()
                    if not cleanup_verified:
                        verification_success = False
                        steps_failed.append("cleanup_verification")
                        logger.error("PostgreSQL cleanup verification failed")
                    else:
                        steps_completed.append("cleanup_verification")

                # Verify database restoration
                if result.data_restored and self.config.original_db_path:
                    try:
                        with sqlite3.connect(self.config.original_db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM assets")
                            asset_count = cursor.fetchone()[0]
                            logger.info(f"Restored database contains {asset_count} assets")
                            steps_completed.append("restoration_verification")
                    except Exception as e:
                        verification_success = False
                        steps_failed.append("restoration_verification")
                        logger.error(f"Database restoration verification failed: {e}")

                if verification_success:
                    steps_completed.append("rollback_verification")
                    logger.info("Rollback verification completed successfully")
                else:
                    steps_failed.append("rollback_verification")
                    logger.error("Rollback verification failed")

            # Determine overall success
            critical_steps = ["postgres_cleanup"]
            critical_failures = [step for step in steps_failed if step in critical_steps]

            result.success = len(critical_failures) == 0

            if result.success:
                logger.info("Emergency rollback completed SUCCESSFULLY")
                result.recommendations.append("Verify application functionality after rollback")
                result.recommendations.append("Review migration logs to identify and fix issues")
                result.recommendations.append("Consider additional testing before re-attempting migration")
            else:
                logger.error("Emergency rollback FAILED")
                result.error_message = f"Critical step failures: {critical_failures}"
                result.recommendations.append("Manual intervention may be required")
                result.recommendations.append("Check database connections and permissions")
                result.recommendations.append("Consider restoring from external backups")

        except Exception as e:
            logger.error(f"Emergency rollback failed with exception: {e}")
            result.error_message = f"Rollback exception: {e}"
            steps_failed.append("unexpected_error")

        finally:
            result.duration = time.time() - start_time
            logger.info(f"Rollback completed in {result.duration:.2f} seconds")

            # Save rollback report
            self._save_rollback_report(result)

        return result

    def _save_rollback_report(self, result: RollbackResult):
        """Save detailed rollback report"""
        report_path = f"/tmp/rollback_report_{self.rollback_id}.json"

        try:
            report_data = asdict(result)
            report_data['config'] = asdict(self.config)

            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)

            logger.info(f"Rollback report saved: {report_path}")

        except Exception as e:
            logger.error(f"Failed to save rollback report: {e}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Emergency Migration Rollback Tool')
    parser.add_argument('--postgres-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--postgres-port', type=int, default=5432, help='PostgreSQL port')
    parser.add_argument('--postgres-db', default='anthias', help='PostgreSQL database')
    parser.add_argument('--postgres-user', default='anthias_user', help='PostgreSQL user')
    parser.add_argument('--postgres-password', default='', help='PostgreSQL password')
    parser.add_argument('--tenant-id', default='default', help='Tenant identifier')
    parser.add_argument('--backup-path', help='Backup file path for restoration')
    parser.add_argument('--original-db-path', help='Original database path for restoration')
    parser.add_argument('--timeout-minutes', type=int, default=5, help='Rollback timeout in minutes')
    parser.add_argument('--no-verify', action='store_true', help='Skip rollback verification')
    parser.add_argument('--preserve-postgres', action='store_true', help='Backup PostgreSQL data before cleanup')
    parser.add_argument('--emergency-mode', action='store_true', help='Continue rollback even if non-critical steps fail')
    parser.add_argument('--list-backups', action='store_true', help='List available backups')

    args = parser.parse_args()

    if args.list_backups:
        # List available backups
        backup_dir = '/tmp/backups'
        if os.path.exists(backup_dir):
            print(f"\nAvailable backups in {backup_dir}:")
            for filename in os.listdir(backup_dir):
                if filename.startswith('anthias_backup_'):
                    file_path = os.path.join(backup_dir, filename)
                    size_mb = os.path.getsize(file_path) / 1024 / 1024
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    print(f"  - {filename} ({size_mb:.2f}MB, {mtime})")
        else:
            print("No backup directory found")
        sys.exit(0)

    # Confirm rollback operation
    if not args.emergency_mode:
        print("\n⚠️  WARNING: This will perform an emergency rollback of the migration!")
        print("This operation will:")
        print("  - Remove all migrated data from PostgreSQL")
        print("  - Restore the original SQLite database (if backup provided)")
        print("  - Cannot be undone once started")

        confirmation = input("\nAre you sure you want to proceed? Type 'ROLLBACK' to confirm: ")
        if confirmation != 'ROLLBACK':
            print("Rollback cancelled.")
            sys.exit(0)

    # Create configuration
    config = RollbackConfig(
        postgres_host=args.postgres_host,
        postgres_port=args.postgres_port,
        postgres_db=args.postgres_db,
        postgres_user=args.postgres_user,
        postgres_password=args.postgres_password or os.getenv('POSTGRES_PASSWORD', ''),
        tenant_id=args.tenant_id,
        backup_path=args.backup_path or '',
        original_db_path=args.original_db_path or '',
        rollback_timeout_minutes=args.timeout_minutes,
        verify_rollback=not args.no_verify,
        preserve_postgres_data=args.preserve_postgres,
        emergency_mode=args.emergency_mode
    )

    # Execute rollback
    orchestrator = RollbackOrchestrator(config)
    result = orchestrator.execute_emergency_rollback()

    # Print summary
    print(f"\nRollback Summary:")
    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Duration: {result.duration:.2f} seconds")
    print(f"Steps completed: {len(result.steps_completed)}")
    print(f"Steps failed: {len(result.steps_failed)}")
    print(f"Data restored: {'Yes' if result.data_restored else 'No'}")
    print(f"PostgreSQL cleaned: {'Yes' if result.postgres_cleaned else 'No'}")

    if result.recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")

    if result.error_message:
        print(f"\nError: {result.error_message}")

    if result.steps_failed:
        print(f"\nFailed steps: {', '.join(result.steps_failed)}")

    sys.exit(0 if result.success else 1)

if __name__ == '__main__':
    main()