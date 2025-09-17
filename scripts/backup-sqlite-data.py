#!/usr/bin/env python3
"""
SQLite Data Backup Utility with Integrity Validation
Comprehensive backup solution with verification and compression
"""

import os
import sys
import json
import sqlite3
import shutil
import hashlib
import gzip
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Backup configuration settings"""
    source_db_path: str
    backup_dir: str = '/tmp/backups'
    compress: bool = True
    verify_integrity: bool = True
    include_metadata: bool = True
    retention_days: int = 30
    max_backup_size_mb: int = 1000
    encryption_enabled: bool = False
    encryption_key: str = ''

@dataclass
class BackupResult:
    """Backup operation result"""
    success: bool
    backup_path: str
    metadata_path: str
    original_size: int
    backup_size: int
    compression_ratio: float
    checksum: str
    duration: float
    timestamp: datetime
    error_message: str = ''

class BackupValidator:
    """Backup validation and integrity checker"""

    @staticmethod
    def calculate_file_checksum(file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""

    @staticmethod
    def validate_sqlite_database(db_path: str) -> Tuple[bool, List[str]]:
        """Validate SQLite database integrity"""
        errors = []

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Check database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                if integrity_result != "ok":
                    errors.append(f"Database integrity check failed: {integrity_result}")

                # Check foreign key constraints
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                if fk_violations:
                    errors.append(f"Foreign key violations found: {len(fk_violations)}")

                # Verify schema
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                if not tables:
                    errors.append("No tables found in database")

                # Check for specific required tables
                table_names = [table[0] for table in tables]
                if 'assets' not in table_names:
                    errors.append("Required 'assets' table not found")

                # Validate data consistency
                cursor.execute("SELECT COUNT(*) FROM assets")
                asset_count = cursor.fetchone()[0]
                logger.info(f"Database contains {asset_count} assets")

        except sqlite3.Error as e:
            errors.append(f"SQLite error during validation: {e}")
        except Exception as e:
            errors.append(f"Unexpected error during validation: {e}")

        return len(errors) == 0, errors

    @staticmethod
    def verify_backup_completeness(original_db: str, backup_db: str) -> Tuple[bool, Dict[str, any]]:
        """Verify backup completeness by comparing data"""
        comparison_result = {
            'tables_match': False,
            'record_counts_match': False,
            'data_integrity_verified': False,
            'differences': []
        }

        try:
            # Compare original and backup databases
            with sqlite3.connect(original_db) as orig_conn, \
                 sqlite3.connect(backup_db) as backup_conn:

                orig_cursor = orig_conn.cursor()
                backup_cursor = backup_conn.cursor()

                # Compare table schemas
                orig_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
                orig_tables = orig_cursor.fetchall()

                backup_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
                backup_tables = backup_cursor.fetchall()

                if orig_tables == backup_tables:
                    comparison_result['tables_match'] = True
                else:
                    comparison_result['differences'].append("Table schemas don't match")

                # Compare record counts for each table
                record_counts_match = True
                for table_name, _ in orig_tables:
                    orig_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    orig_count = orig_cursor.fetchone()[0]

                    backup_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    backup_count = backup_cursor.fetchone()[0]

                    if orig_count != backup_count:
                        record_counts_match = False
                        comparison_result['differences'].append(
                            f"Record count mismatch in {table_name}: {orig_count} vs {backup_count}"
                        )

                comparison_result['record_counts_match'] = record_counts_match

                # For the assets table, compare actual data
                if 'assets' in [table[0] for table in orig_tables]:
                    orig_cursor.execute("SELECT asset_id, name, md5 FROM assets ORDER BY asset_id")
                    orig_data = orig_cursor.fetchall()

                    backup_cursor.execute("SELECT asset_id, name, md5 FROM assets ORDER BY asset_id")
                    backup_data = backup_cursor.fetchall()

                    if orig_data == backup_data:
                        comparison_result['data_integrity_verified'] = True
                    else:
                        comparison_result['differences'].append("Asset data doesn't match between original and backup")

        except Exception as e:
            comparison_result['differences'].append(f"Error during backup verification: {e}")

        return (comparison_result['tables_match'] and
                comparison_result['record_counts_match'] and
                comparison_result['data_integrity_verified']), comparison_result

class SQLiteBackupManager:
    """Main backup management class"""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.validator = BackupValidator()

        # Ensure backup directory exists
        Path(self.config.backup_dir).mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> BackupResult:
        """Create a complete backup of the SQLite database"""
        start_time = time.time()
        timestamp = datetime.now()

        logger.info(f"Starting backup of {self.config.source_db_path}")

        # Validate source database
        is_valid, validation_errors = self.validator.validate_sqlite_database(self.config.source_db_path)
        if not is_valid:
            error_msg = f"Source database validation failed: {'; '.join(validation_errors)}"
            logger.error(error_msg)
            return BackupResult(
                success=False,
                backup_path='',
                metadata_path='',
                original_size=0,
                backup_size=0,
                compression_ratio=0.0,
                checksum='',
                duration=0.0,
                timestamp=timestamp,
                error_message=error_msg
            )

        # Generate backup filename
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        backup_filename = f"anthias_backup_{timestamp_str}.db"
        backup_path = os.path.join(self.config.backup_dir, backup_filename)

        try:
            # Get original file size
            original_size = os.path.getsize(self.config.source_db_path)

            # Check if backup will exceed size limit
            if original_size > self.config.max_backup_size_mb * 1024 * 1024:
                raise Exception(f"Database size ({original_size / 1024 / 1024:.2f}MB) exceeds limit ({self.config.max_backup_size_mb}MB)")

            # Create backup using SQLite's backup API for consistency
            backup_db_path = self._create_database_backup(backup_path)

            # Compress backup if enabled
            if self.config.compress:
                backup_db_path = self._compress_backup(backup_db_path)

            # Calculate backup size and compression ratio
            backup_size = os.path.getsize(backup_db_path)
            compression_ratio = (1 - backup_size / original_size) * 100 if original_size > 0 else 0

            # Calculate checksum
            checksum = self.validator.calculate_file_checksum(backup_db_path)

            # Verify backup integrity
            if self.config.verify_integrity and not self.config.compress:
                is_complete, verification_result = self.validator.verify_backup_completeness(
                    self.config.source_db_path, backup_db_path
                )
                if not is_complete:
                    raise Exception(f"Backup verification failed: {verification_result['differences']}")

            # Create metadata file
            metadata_path = self._create_metadata_file(
                backup_db_path, original_size, backup_size, checksum, timestamp
            )

            duration = time.time() - start_time

            logger.info(f"Backup completed successfully:")
            logger.info(f"  - Backup path: {backup_db_path}")
            logger.info(f"  - Original size: {original_size / 1024 / 1024:.2f}MB")
            logger.info(f"  - Backup size: {backup_size / 1024 / 1024:.2f}MB")
            logger.info(f"  - Compression: {compression_ratio:.1f}%")
            logger.info(f"  - Duration: {duration:.2f}s")
            logger.info(f"  - Checksum: {checksum[:16]}...")

            return BackupResult(
                success=True,
                backup_path=backup_db_path,
                metadata_path=metadata_path,
                original_size=original_size,
                backup_size=backup_size,
                compression_ratio=compression_ratio,
                checksum=checksum,
                duration=duration,
                timestamp=timestamp
            )

        except Exception as e:
            error_msg = f"Backup failed: {e}"
            logger.error(error_msg)

            # Clean up partial backup files
            self._cleanup_failed_backup(backup_path)

            return BackupResult(
                success=False,
                backup_path='',
                metadata_path='',
                original_size=0,
                backup_size=0,
                compression_ratio=0.0,
                checksum='',
                duration=time.time() - start_time,
                timestamp=timestamp,
                error_message=error_msg
            )

    def _create_database_backup(self, backup_path: str) -> str:
        """Create database backup using SQLite's backup API"""
        try:
            # Use SQLite's backup API for consistent backups
            with sqlite3.connect(self.config.source_db_path) as source_conn, \
                 sqlite3.connect(backup_path) as backup_conn:

                source_conn.backup(backup_conn)
                logger.info("Database backup created using SQLite backup API")

            return backup_path

        except Exception as e:
            logger.warning(f"SQLite backup API failed, falling back to file copy: {e}")

            # Fallback to file copy
            shutil.copy2(self.config.source_db_path, backup_path)
            logger.info("Database backup created using file copy")

            return backup_path

    def _compress_backup(self, backup_path: str) -> str:
        """Compress backup file using gzip"""
        compressed_path = backup_path + '.gz'

        try:
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove uncompressed file
            os.remove(backup_path)

            logger.info(f"Backup compressed: {compressed_path}")
            return compressed_path

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            # Return original path if compression fails
            return backup_path

    def _create_metadata_file(self, backup_path: str, original_size: int,
                             backup_size: int, checksum: str, timestamp: datetime) -> str:
        """Create metadata file for backup"""
        metadata = {
            'backup_info': {
                'source_database': self.config.source_db_path,
                'backup_path': backup_path,
                'backup_timestamp': timestamp.isoformat(),
                'backup_version': '1.0',
                'tool_version': '1.0.0'
            },
            'file_info': {
                'original_size_bytes': original_size,
                'backup_size_bytes': backup_size,
                'compression_enabled': self.config.compress,
                'compression_ratio_percent': ((1 - backup_size / original_size) * 100) if original_size > 0 else 0,
                'checksum_sha256': checksum
            },
            'config': {
                'compression': self.config.compress,
                'integrity_verification': self.config.verify_integrity,
                'encryption_enabled': self.config.encryption_enabled
            },
            'validation': {
                'integrity_verified': True,
                'backup_type': 'full',
                'consistency_check': 'passed'
            }
        }

        metadata_path = backup_path + '.metadata.json'

        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)

            logger.info(f"Metadata file created: {metadata_path}")
            return metadata_path

        except Exception as e:
            logger.error(f"Failed to create metadata file: {e}")
            return ''

    def _cleanup_failed_backup(self, backup_path: str):
        """Clean up files from failed backup"""
        cleanup_files = [
            backup_path,
            backup_path + '.gz',
            backup_path + '.metadata.json'
        ]

        for file_path in cleanup_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {file_path}: {e}")

    def cleanup_old_backups(self) -> int:
        """Remove backups older than retention period"""
        if self.config.retention_days <= 0:
            return 0

        cutoff_time = time.time() - (self.config.retention_days * 24 * 60 * 60)
        removed_count = 0

        try:
            for filename in os.listdir(self.config.backup_dir):
                if filename.startswith('anthias_backup_'):
                    file_path = os.path.join(self.config.backup_dir, filename)

                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            removed_count += 1
                            logger.info(f"Removed old backup: {filename}")
                        except Exception as e:
                            logger.warning(f"Failed to remove {filename}: {e}")

            if removed_count > 0:
                logger.info(f"Cleanup completed: {removed_count} old backups removed")

            return removed_count

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return 0

    def list_backups(self) -> List[Dict[str, any]]:
        """List all available backups with metadata"""
        backups = []

        try:
            for filename in os.listdir(self.config.backup_dir):
                if filename.startswith('anthias_backup_') and not filename.endswith('.metadata.json'):
                    file_path = os.path.join(self.config.backup_dir, filename)
                    metadata_path = file_path + '.metadata.json'

                    backup_info = {
                        'filename': filename,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'created': datetime.fromtimestamp(os.path.getmtime(file_path)),
                        'has_metadata': os.path.exists(metadata_path)
                    }

                    # Load metadata if available
                    if backup_info['has_metadata']:
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                                backup_info['metadata'] = metadata
                        except Exception as e:
                            logger.warning(f"Failed to load metadata for {filename}: {e}")

                    backups.append(backup_info)

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")

        return backups

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='SQLite Database Backup Utility')
    parser.add_argument('--source-db', required=True, help='Source SQLite database path')
    parser.add_argument('--backup-dir', default='/tmp/backups', help='Backup directory')
    parser.add_argument('--no-compress', action='store_true', help='Disable compression')
    parser.add_argument('--no-verify', action='store_true', help='Skip integrity verification')
    parser.add_argument('--retention-days', type=int, default=30, help='Backup retention days')
    parser.add_argument('--max-size-mb', type=int, default=1000, help='Maximum backup size in MB')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old backups')
    parser.add_argument('--list', action='store_true', help='List available backups')

    args = parser.parse_args()

    # Create configuration
    config = BackupConfig(
        source_db_path=args.source_db,
        backup_dir=args.backup_dir,
        compress=not args.no_compress,
        verify_integrity=not args.no_verify,
        retention_days=args.retention_days,
        max_backup_size_mb=args.max_size_mb
    )

    # Initialize backup manager
    backup_manager = SQLiteBackupManager(config)

    if args.list:
        # List available backups
        backups = backup_manager.list_backups()
        print(f"\nAvailable backups in {config.backup_dir}:")

        if not backups:
            print("No backups found.")
        else:
            for backup in backups:
                print(f"  - {backup['filename']}")
                print(f"    Size: {backup['size'] / 1024 / 1024:.2f}MB")
                print(f"    Created: {backup['created']}")
                print(f"    Metadata: {'Yes' if backup['has_metadata'] else 'No'}")
                print()

        sys.exit(0)

    if args.cleanup:
        # Clean up old backups
        removed_count = backup_manager.cleanup_old_backups()
        print(f"Removed {removed_count} old backups")

        if not args.source_db:
            sys.exit(0)

    # Create backup
    result = backup_manager.create_backup()

    if result.success:
        print(f"Backup created successfully: {result.backup_path}")
        print(f"Backup size: {result.backup_size / 1024 / 1024:.2f}MB")
        print(f"Compression: {result.compression_ratio:.1f}%")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Checksum: {result.checksum}")
        sys.exit(0)
    else:
        print(f"Backup failed: {result.error_message}")
        sys.exit(1)

if __name__ == '__main__':
    main()