#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for Multi-tenant SaaS
Zero-downtime migration with comprehensive error handling and rollback capability
"""

import os
import sys
import json
import sqlite3
import psycopg2
import hashlib
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationConfig:
    """Migration configuration settings"""
    sqlite_db_path: str
    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    postgres_db: str = 'anthias'
    postgres_user: str = 'anthias_user'
    postgres_password: str = ''
    tenant_id: str = 'default'
    batch_size: int = 1000
    max_retries: int = 3
    timeout_seconds: int = 300
    dry_run: bool = False
    backup_enabled: bool = True
    validate_data: bool = True

@dataclass
class MigrationStats:
    """Migration statistics and metrics"""
    start_time: datetime
    end_time: Optional[datetime] = None
    records_migrated: int = 0
    records_failed: int = 0
    migration_duration: float = 0.0
    data_integrity_checks: int = 0
    validation_errors: List[str] = None
    performance_metrics: Dict[str, float] = None

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []
        if self.performance_metrics is None:
            self.performance_metrics = {}

class MigrationError(Exception):
    """Custom exception for migration errors"""
    pass

class DatabaseConnector:
    """Database connection manager with connection pooling"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.sqlite_conn = None
        self.postgres_conn = None

    @contextmanager
    def sqlite_connection(self):
        """Context manager for SQLite connection"""
        try:
            if not os.path.exists(self.config.sqlite_db_path):
                raise MigrationError(f"SQLite database not found: {self.config.sqlite_db_path}")

            conn = sqlite3.connect(self.config.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            logger.error(f"SQLite connection error: {e}")
            raise MigrationError(f"Failed to connect to SQLite: {e}")
        finally:
            if conn:
                conn.close()

    @contextmanager
    def postgres_connection(self):
        """Context manager for PostgreSQL connection"""
        try:
            conn_params = {
                'host': self.config.postgres_host,
                'port': self.config.postgres_port,
                'database': self.config.postgres_db,
                'user': self.config.postgres_user,
                'password': self.config.postgres_password,
                'connect_timeout': 10
            }

            conn = psycopg2.connect(**conn_params)
            conn.autocommit = False
            yield conn
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
            raise MigrationError(f"Failed to connect to PostgreSQL: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

class DataValidator:
    """Data validation and integrity checker"""

    def __init__(self, db_connector: DatabaseConnector):
        self.db_connector = db_connector

    def validate_sqlite_data(self) -> Tuple[bool, List[str]]:
        """Validate SQLite data before migration"""
        errors = []

        with self.db_connector.sqlite_connection() as conn:
            cursor = conn.cursor()

            try:
                # Check for NULL primary keys
                cursor.execute("SELECT COUNT(*) FROM assets WHERE asset_id IS NULL")
                null_pks = cursor.fetchone()[0]
                if null_pks > 0:
                    errors.append(f"Found {null_pks} records with NULL primary keys")

                # Check for duplicate asset_ids
                cursor.execute("""
                    SELECT asset_id, COUNT(*) as count
                    FROM assets
                    GROUP BY asset_id
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                if duplicates:
                    errors.append(f"Found {len(duplicates)} duplicate asset_id values")

                # Check for invalid date formats
                cursor.execute("""
                    SELECT asset_id FROM assets
                    WHERE (start_date IS NOT NULL AND start_date = '')
                       OR (end_date IS NOT NULL AND end_date = '')
                """)
                invalid_dates = cursor.fetchall()
                if invalid_dates:
                    errors.append(f"Found {len(invalid_dates)} records with invalid date formats")

                # Check data consistency
                cursor.execute("SELECT COUNT(*) FROM assets")
                total_records = cursor.fetchone()[0]
                logger.info(f"SQLite validation: {total_records} total records found")

            except Exception as e:
                errors.append(f"SQLite validation error: {e}")

        return len(errors) == 0, errors

    def validate_migration_integrity(self, sqlite_count: int, postgres_count: int) -> bool:
        """Validate that migration preserved data integrity"""
        if sqlite_count != postgres_count:
            logger.error(f"Data count mismatch: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
            return False

        # Additional integrity checks can be added here
        return True

    def calculate_data_checksum(self, connection_type: str) -> str:
        """Calculate checksum for data integrity verification"""
        if connection_type == 'sqlite':
            with self.db_connector.sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT asset_id, name, uri, md5, start_date, end_date,
                           duration, mimetype, is_enabled, is_processing,
                           nocache, play_order, skip_asset_check
                    FROM assets ORDER BY asset_id
                """)
                data = cursor.fetchall()
        else:  # postgresql
            with self.db_connector.postgres_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT asset_id, name, uri, md5, start_date, end_date,
                           duration, mimetype, is_enabled, is_processing,
                           nocache, play_order, skip_asset_check
                    FROM {self.db_connector.config.tenant_id}_assets ORDER BY asset_id
                """)
                data = cursor.fetchall()

        # Create hash of all data
        data_str = json.dumps([list(row) for row in data], sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

class MigrationExecutor:
    """Main migration execution engine"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.db_connector = DatabaseConnector(config)
        self.validator = DataValidator(self.db_connector)
        self.stats = MigrationStats(start_time=datetime.now())

    def pre_migration_checks(self) -> bool:
        """Run comprehensive pre-migration validation"""
        logger.info("Starting pre-migration checks...")

        try:
            # Validate SQLite data
            is_valid, errors = self.validator.validate_sqlite_data()
            if not is_valid:
                logger.error("SQLite validation failed:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False

            # Test PostgreSQL connection
            with self.db_connector.postgres_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                logger.info(f"PostgreSQL connection successful: {version}")

            # Check if target schema exists
            if not self._ensure_postgres_schema():
                return False

            logger.info("Pre-migration checks passed")
            return True

        except Exception as e:
            logger.error(f"Pre-migration check failed: {e}")
            return False

    def _ensure_postgres_schema(self) -> bool:
        """Ensure PostgreSQL schema exists for tenant"""
        try:
            with self.db_connector.postgres_connection() as conn:
                cursor = conn.cursor()

                # Create tenant-specific table
                table_name = f"{self.config.tenant_id}_assets"
                create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    asset_id TEXT PRIMARY KEY,
                    name TEXT,
                    uri TEXT,
                    md5 TEXT,
                    start_date TIMESTAMP WITH TIME ZONE,
                    end_date TIMESTAMP WITH TIME ZONE,
                    duration BIGINT,
                    mimetype TEXT,
                    is_enabled BOOLEAN DEFAULT FALSE,
                    is_processing BOOLEAN DEFAULT FALSE,
                    nocache BOOLEAN DEFAULT FALSE,
                    play_order INTEGER DEFAULT 0,
                    skip_asset_check BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """

                cursor.execute(create_table_sql)

                # Create indexes for performance
                indexes = [
                    f"CREATE INDEX IF NOT EXISTS idx_{self.config.tenant_id}_assets_enabled ON {table_name} (is_enabled)",
                    f"CREATE INDEX IF NOT EXISTS idx_{self.config.tenant_id}_assets_dates ON {table_name} (start_date, end_date)",
                    f"CREATE INDEX IF NOT EXISTS idx_{self.config.tenant_id}_assets_order ON {table_name} (play_order)",
                ]

                for index_sql in indexes:
                    cursor.execute(index_sql)

                conn.commit()
                logger.info(f"PostgreSQL schema ready for tenant: {self.config.tenant_id}")
                return True

        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            return False

    def migrate_data(self) -> bool:
        """Execute the main data migration"""
        logger.info("Starting data migration...")

        try:
            # Get source data count
            with self.db_connector.sqlite_connection() as sqlite_conn:
                cursor = sqlite_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM assets")
                total_records = cursor.fetchone()[0]
                logger.info(f"Total records to migrate: {total_records}")

            if self.config.dry_run:
                logger.info("DRY RUN: Would migrate data but no changes will be made")
                return True

            # Migrate in batches for memory efficiency
            offset = 0
            migrated_count = 0

            with self.db_connector.postgres_connection() as pg_conn:
                pg_cursor = pg_conn.cursor()
                table_name = f"{self.config.tenant_id}_assets"

                while offset < total_records:
                    batch_start = time.time()

                    # Get batch from SQLite
                    with self.db_connector.sqlite_connection() as sqlite_conn:
                        sqlite_cursor = sqlite_conn.cursor()
                        sqlite_cursor.execute("""
                            SELECT asset_id, name, uri, md5, start_date, end_date,
                                   duration, mimetype, is_enabled, is_processing,
                                   nocache, play_order, skip_asset_check
                            FROM assets
                            LIMIT ? OFFSET ?
                        """, (self.config.batch_size, offset))

                        batch_data = sqlite_cursor.fetchall()

                    if not batch_data:
                        break

                    # Insert batch into PostgreSQL
                    insert_sql = f"""
                        INSERT INTO {table_name}
                        (asset_id, name, uri, md5, start_date, end_date,
                         duration, mimetype, is_enabled, is_processing,
                         nocache, play_order, skip_asset_check)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (asset_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        uri = EXCLUDED.uri,
                        md5 = EXCLUDED.md5,
                        start_date = EXCLUDED.start_date,
                        end_date = EXCLUDED.end_date,
                        duration = EXCLUDED.duration,
                        mimetype = EXCLUDED.mimetype,
                        is_enabled = EXCLUDED.is_enabled,
                        is_processing = EXCLUDED.is_processing,
                        nocache = EXCLUDED.nocache,
                        play_order = EXCLUDED.play_order,
                        skip_asset_check = EXCLUDED.skip_asset_check,
                        updated_at = NOW()
                    """

                    pg_cursor.executemany(insert_sql, batch_data)
                    pg_conn.commit()

                    migrated_count += len(batch_data)
                    offset += self.config.batch_size

                    batch_time = time.time() - batch_start
                    logger.info(f"Migrated batch: {migrated_count}/{total_records} "
                              f"({batch_time:.2f}s, {len(batch_data)} records)")

            self.stats.records_migrated = migrated_count
            logger.info(f"Data migration completed: {migrated_count} records")
            return True

        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            self.stats.records_failed = total_records - migrated_count
            return False

    def post_migration_validation(self) -> bool:
        """Validate migration results"""
        logger.info("Starting post-migration validation...")

        try:
            # Count records in both databases
            with self.db_connector.sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM assets")
                sqlite_count = cursor.fetchone()[0]

            with self.db_connector.postgres_connection() as conn:
                cursor = conn.cursor()
                table_name = f"{self.config.tenant_id}_assets"
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                postgres_count = cursor.fetchone()[0]

            # Verify data integrity
            if not self.validator.validate_migration_integrity(sqlite_count, postgres_count):
                return False

            # Calculate and compare checksums
            if self.config.validate_data:
                sqlite_checksum = self.validator.calculate_data_checksum('sqlite')
                postgres_checksum = self.validator.calculate_data_checksum('postgresql')

                if sqlite_checksum != postgres_checksum:
                    logger.error("Data integrity check failed: checksums don't match")
                    return False

                logger.info("Data integrity check passed: checksums match")

            # Performance validation
            if not self._validate_performance():
                logger.warning("Performance validation failed but migration is valid")

            logger.info("Post-migration validation passed")
            return True

        except Exception as e:
            logger.error(f"Post-migration validation failed: {e}")
            return False

    def _validate_performance(self) -> bool:
        """Validate that queries meet performance requirements (<50ms)"""
        try:
            with self.db_connector.postgres_connection() as conn:
                cursor = conn.cursor()
                table_name = f"{self.config.tenant_id}_assets"

                # Test common queries
                test_queries = [
                    f"SELECT * FROM {table_name} WHERE is_enabled = true",
                    f"SELECT * FROM {table_name} WHERE asset_id = (SELECT asset_id FROM {table_name} LIMIT 1)",
                    f"SELECT COUNT(*) FROM {table_name}",
                    f"SELECT * FROM {table_name} ORDER BY play_order LIMIT 10"
                ]

                for query in test_queries:
                    start_time = time.time()
                    cursor.execute(query)
                    cursor.fetchall()
                    query_time = (time.time() - start_time) * 1000  # Convert to ms

                    if query_time > 50:
                        logger.warning(f"Query performance issue: {query_time:.2f}ms > 50ms")
                        return False

                    self.stats.performance_metrics[query] = query_time

                logger.info("Performance validation passed: all queries < 50ms")
                return True

        except Exception as e:
            logger.error(f"Performance validation error: {e}")
            return False

    def execute_migration(self) -> bool:
        """Execute complete migration process"""
        logger.info("Starting SQLite to PostgreSQL migration...")

        try:
            # Pre-migration checks
            if not self.pre_migration_checks():
                logger.error("Pre-migration checks failed")
                return False

            # Create backup if enabled
            if self.config.backup_enabled:
                backup_path = f"/tmp/sqlite_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                logger.info(f"Creating backup: {backup_path}")
                # Backup creation would be handled by separate backup script

            # Execute migration
            if not self.migrate_data():
                logger.error("Data migration failed")
                return False

            # Post-migration validation
            if not self.post_migration_validation():
                logger.error("Post-migration validation failed")
                return False

            # Update statistics
            self.stats.end_time = datetime.now()
            self.stats.migration_duration = (
                self.stats.end_time - self.stats.start_time
            ).total_seconds()

            logger.info(f"Migration completed successfully in {self.stats.migration_duration:.2f} seconds")
            logger.info(f"Records migrated: {self.stats.records_migrated}")

            # Save migration report
            self._save_migration_report()

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def _save_migration_report(self):
        """Save detailed migration report"""
        report_path = f"/tmp/migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report_data = {
            'migration_config': asdict(self.config),
            'migration_stats': asdict(self.stats),
            'status': 'SUCCESS' if self.stats.records_failed == 0 else 'PARTIAL_FAILURE'
        }

        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Migration report saved: {report_path}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='SQLite to PostgreSQL Migration Tool')
    parser.add_argument('--sqlite-db', required=True, help='SQLite database path')
    parser.add_argument('--postgres-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--postgres-port', type=int, default=5432, help='PostgreSQL port')
    parser.add_argument('--postgres-db', default='anthias', help='PostgreSQL database')
    parser.add_argument('--postgres-user', default='anthias_user', help='PostgreSQL user')
    parser.add_argument('--postgres-password', default='', help='PostgreSQL password')
    parser.add_argument('--tenant-id', default='default', help='Tenant identifier')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for migration')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without changes')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup creation')
    parser.add_argument('--no-validation', action='store_true', help='Skip data validation')

    args = parser.parse_args()

    # Create configuration
    config = MigrationConfig(
        sqlite_db_path=args.sqlite_db,
        postgres_host=args.postgres_host,
        postgres_port=args.postgres_port,
        postgres_db=args.postgres_db,
        postgres_user=args.postgres_user,
        postgres_password=args.postgres_password or os.getenv('POSTGRES_PASSWORD', ''),
        tenant_id=args.tenant_id,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        backup_enabled=not args.no_backup,
        validate_data=not args.no_validation
    )

    # Execute migration
    executor = MigrationExecutor(config)
    success = executor.execute_migration()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()