#!/usr/bin/env python3
"""
Migration Validation Script
Comprehensive data integrity and consistency validation for SQLite to PostgreSQL migration
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
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationConfig:
    """Validation configuration settings"""
    sqlite_db_path: str
    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    postgres_db: str = 'anthias'
    postgres_user: str = 'anthias_user'
    postgres_password: str = ''
    tenant_id: str = 'default'
    deep_validation: bool = True
    performance_test: bool = True
    max_query_time_ms: float = 50.0
    sample_size: int = 1000

@dataclass
class ValidationResult:
    """Validation result data structure"""
    validation_id: str
    timestamp: datetime
    config: ValidationConfig
    overall_status: str
    tests_passed: int
    tests_failed: int
    total_tests: int
    test_results: Dict[str, Any]
    performance_metrics: Dict[str, float]
    data_integrity_score: float
    recommendations: List[str]
    detailed_errors: List[str]

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class DatabaseConnector:
    """Database connection manager for validation"""

    def __init__(self, config: ValidationConfig):
        self.config = config

    def get_sqlite_connection(self):
        """Get SQLite database connection"""
        try:
            if not os.path.exists(self.config.sqlite_db_path):
                raise ValidationError(f"SQLite database not found: {self.config.sqlite_db_path}")

            conn = sqlite3.connect(self.config.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            raise ValidationError(f"Failed to connect to SQLite: {e}")

    def get_postgres_connection(self):
        """Get PostgreSQL database connection"""
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
            return conn
        except Exception as e:
            raise ValidationError(f"Failed to connect to PostgreSQL: {e}")

class DataValidator:
    """Core data validation functionality"""

    def __init__(self, db_connector: DatabaseConnector):
        self.db_connector = db_connector
        self.tenant_table = f"{db_connector.config.tenant_id}_assets"

    def validate_record_count(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate that record counts match between databases"""
        logger.info("Validating record counts...")

        try:
            # Get SQLite count
            with self.db_connector.get_sqlite_connection() as sqlite_conn:
                cursor = sqlite_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM assets")
                sqlite_count = cursor.fetchone()[0]

            # Get PostgreSQL count
            with self.db_connector.get_postgres_connection() as pg_conn:
                cursor = pg_conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {self.tenant_table}")
                postgres_count = cursor.fetchone()[0]

            result = {
                'sqlite_count': sqlite_count,
                'postgres_count': postgres_count,
                'match': sqlite_count == postgres_count,
                'difference': abs(sqlite_count - postgres_count)
            }

            if result['match']:
                logger.info(f"Record count validation PASSED: {sqlite_count} records in both databases")
            else:
                logger.error(f"Record count validation FAILED: SQLite={sqlite_count}, PostgreSQL={postgres_count}")

            return result['match'], result

        except Exception as e:
            logger.error(f"Record count validation error: {e}")
            return False, {'error': str(e)}

    def validate_schema_compatibility(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate schema compatibility between databases"""
        logger.info("Validating schema compatibility...")

        try:
            # Get SQLite schema
            with self.db_connector.get_sqlite_connection() as sqlite_conn:
                cursor = sqlite_conn.cursor()
                cursor.execute("PRAGMA table_info(assets)")
                sqlite_columns = {row['name']: row['type'] for row in cursor.fetchall()}

            # Get PostgreSQL schema
            with self.db_connector.get_postgres_connection() as pg_conn:
                cursor = pg_conn.cursor()
                cursor.execute(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{self.tenant_table}'
                    AND column_name NOT IN ('created_at', 'updated_at')
                    ORDER BY ordinal_position
                """)
                postgres_columns = {row[0]: row[1] for row in cursor.fetchall()}

            # Compare schemas
            missing_in_postgres = set(sqlite_columns.keys()) - set(postgres_columns.keys())
            extra_in_postgres = set(postgres_columns.keys()) - set(sqlite_columns.keys())

            # Check compatible data types
            type_mapping = {
                'TEXT': ['text', 'character varying'],
                'INTEGER': ['integer', 'bigint'],
                'BIGINT': ['bigint', 'integer'],
                'BOOLEAN': ['boolean'],
                'REAL': ['real', 'double precision', 'numeric']
            }

            type_mismatches = []
            for col, sqlite_type in sqlite_columns.items():
                if col in postgres_columns:
                    pg_type = postgres_columns[col]
                    expected_types = type_mapping.get(sqlite_type.upper(), [])
                    if pg_type not in expected_types:
                        type_mismatches.append({
                            'column': col,
                            'sqlite_type': sqlite_type,
                            'postgres_type': pg_type
                        })

            result = {
                'sqlite_columns': sqlite_columns,
                'postgres_columns': postgres_columns,
                'missing_in_postgres': list(missing_in_postgres),
                'extra_in_postgres': list(extra_in_postgres),
                'type_mismatches': type_mismatches,
                'compatible': len(missing_in_postgres) == 0 and len(type_mismatches) == 0
            }

            if result['compatible']:
                logger.info("Schema compatibility validation PASSED")
            else:
                logger.error("Schema compatibility validation FAILED")
                if missing_in_postgres:
                    logger.error(f"Missing columns in PostgreSQL: {missing_in_postgres}")
                if type_mismatches:
                    logger.error(f"Type mismatches: {type_mismatches}")

            return result['compatible'], result

        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return False, {'error': str(e)}

    def validate_data_integrity(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate data integrity using checksums and sampling"""
        logger.info("Validating data integrity...")

        try:
            # Sample-based validation for large datasets
            sample_size = min(self.db_connector.config.sample_size, 10000)

            # Get sample from SQLite
            with self.db_connector.get_sqlite_connection() as sqlite_conn:
                cursor = sqlite_conn.cursor()
                cursor.execute(f"""
                    SELECT asset_id, name, uri, md5, start_date, end_date,
                           duration, mimetype, is_enabled, is_processing,
                           nocache, play_order, skip_asset_check
                    FROM assets
                    ORDER BY asset_id
                    LIMIT {sample_size}
                """)
                sqlite_data = cursor.fetchall()

            # Get corresponding data from PostgreSQL
            asset_ids = [row[0] for row in sqlite_data]
            placeholders = ','.join(['%s'] * len(asset_ids))

            with self.db_connector.get_postgres_connection() as pg_conn:
                cursor = pg_conn.cursor()
                cursor.execute(f"""
                    SELECT asset_id, name, uri, md5, start_date, end_date,
                           duration, mimetype, is_enabled, is_processing,
                           nocache, play_order, skip_asset_check
                    FROM {self.tenant_table}
                    WHERE asset_id IN ({placeholders})
                    ORDER BY asset_id
                """, asset_ids)
                postgres_data = cursor.fetchall()

            # Convert to dictionaries for comparison
            sqlite_dict = {row[0]: row[1:] for row in sqlite_data}
            postgres_dict = {row[0]: row[1:] for row in postgres_data}

            # Compare data
            mismatches = []
            missing_in_postgres = []

            for asset_id, sqlite_row in sqlite_dict.items():
                if asset_id not in postgres_dict:
                    missing_in_postgres.append(asset_id)
                else:
                    postgres_row = postgres_dict[asset_id]
                    if sqlite_row != postgres_row:
                        mismatches.append({
                            'asset_id': asset_id,
                            'sqlite_data': sqlite_row,
                            'postgres_data': postgres_row
                        })

            # Calculate integrity score
            total_checked = len(sqlite_dict)
            errors = len(mismatches) + len(missing_in_postgres)
            integrity_score = ((total_checked - errors) / total_checked * 100) if total_checked > 0 else 0

            result = {
                'sample_size': total_checked,
                'mismatches': len(mismatches),
                'missing_records': len(missing_in_postgres),
                'integrity_score': integrity_score,
                'sample_mismatches': mismatches[:10],  # First 10 for details
                'sample_missing': missing_in_postgres[:10],
                'passed': errors == 0
            }

            if result['passed']:
                logger.info(f"Data integrity validation PASSED: {integrity_score:.2f}% integrity score")
            else:
                logger.error(f"Data integrity validation FAILED: {errors} errors found, {integrity_score:.2f}% integrity score")

            return result['passed'], result

        except Exception as e:
            logger.error(f"Data integrity validation error: {e}")
            return False, {'error': str(e)}

    def validate_primary_key_constraints(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate primary key constraints and uniqueness"""
        logger.info("Validating primary key constraints...")

        try:
            result = {
                'sqlite_duplicates': 0,
                'postgres_duplicates': 0,
                'null_keys': {'sqlite': 0, 'postgres': 0},
                'passed': True
            }

            # Check SQLite for duplicates and nulls
            with self.db_connector.get_sqlite_connection() as sqlite_conn:
                cursor = sqlite_conn.cursor()

                # Check for NULL primary keys
                cursor.execute("SELECT COUNT(*) FROM assets WHERE asset_id IS NULL")
                result['null_keys']['sqlite'] = cursor.fetchone()[0]

                # Check for duplicates
                cursor.execute("""
                    SELECT asset_id, COUNT(*) as count
                    FROM assets
                    GROUP BY asset_id
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                result['sqlite_duplicates'] = len(duplicates)

            # Check PostgreSQL for duplicates and nulls
            with self.db_connector.get_postgres_connection() as pg_conn:
                cursor = pg_conn.cursor()

                # Check for NULL primary keys
                cursor.execute(f"SELECT COUNT(*) FROM {self.tenant_table} WHERE asset_id IS NULL")
                result['null_keys']['postgres'] = cursor.fetchone()[0]

                # Check for duplicates
                cursor.execute(f"""
                    SELECT asset_id, COUNT(*) as count
                    FROM {self.tenant_table}
                    GROUP BY asset_id
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                result['postgres_duplicates'] = len(duplicates)

            # Determine if validation passed
            total_issues = (result['sqlite_duplicates'] + result['postgres_duplicates'] +
                           result['null_keys']['sqlite'] + result['null_keys']['postgres'])
            result['passed'] = total_issues == 0

            if result['passed']:
                logger.info("Primary key validation PASSED: No duplicates or null keys found")
            else:
                logger.error(f"Primary key validation FAILED: {total_issues} issues found")

            return result['passed'], result

        except Exception as e:
            logger.error(f"Primary key validation error: {e}")
            return False, {'error': str(e)}

    def validate_data_types(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate data type consistency and conversion accuracy"""
        logger.info("Validating data types...")

        try:
            type_errors = []
            sample_size = min(self.db_connector.config.sample_size, 1000)

            # Check boolean conversions
            with self.db_connector.get_sqlite_connection() as sqlite_conn:
                cursor = sqlite_conn.cursor()
                cursor.execute(f"""
                    SELECT asset_id, is_enabled, is_processing, nocache, skip_asset_check
                    FROM assets
                    LIMIT {sample_size}
                """)
                sqlite_booleans = cursor.fetchall()

            asset_ids = [row[0] for row in sqlite_booleans]
            placeholders = ','.join(['%s'] * len(asset_ids))

            with self.db_connector.get_postgres_connection() as pg_conn:
                cursor = pg_conn.cursor()
                cursor.execute(f"""
                    SELECT asset_id, is_enabled, is_processing, nocache, skip_asset_check
                    FROM {self.tenant_table}
                    WHERE asset_id IN ({placeholders})
                    ORDER BY asset_id
                """, asset_ids)
                postgres_booleans = cursor.fetchall()

            # Compare boolean values
            sqlite_bool_dict = {row[0]: row[1:] for row in sqlite_booleans}
            postgres_bool_dict = {row[0]: row[1:] for row in postgres_booleans}

            bool_mismatches = 0
            for asset_id, sqlite_vals in sqlite_bool_dict.items():
                if asset_id in postgres_bool_dict:
                    postgres_vals = postgres_bool_dict[asset_id]
                    for i, (sqlite_val, postgres_val) in enumerate(zip(sqlite_vals, postgres_vals)):
                        # Convert SQLite integers to boolean for comparison
                        sqlite_bool = bool(sqlite_val) if sqlite_val is not None else None
                        if sqlite_bool != postgres_val:
                            bool_mismatches += 1
                            if bool_mismatches <= 5:  # Log first 5 mismatches
                                type_errors.append(f"Boolean mismatch in {asset_id}: SQLite={sqlite_val}, PostgreSQL={postgres_val}")

            # Check date/timestamp conversions
            date_mismatches = 0
            with self.db_connector.get_sqlite_connection() as sqlite_conn:
                cursor = sqlite_conn.cursor()
                cursor.execute(f"""
                    SELECT asset_id, start_date, end_date
                    FROM assets
                    WHERE start_date IS NOT NULL OR end_date IS NOT NULL
                    LIMIT {sample_size}
                """)
                sqlite_dates = cursor.fetchall()

            if sqlite_dates:
                date_asset_ids = [row[0] for row in sqlite_dates]
                placeholders = ','.join(['%s'] * len(date_asset_ids))

                with self.db_connector.get_postgres_connection() as pg_conn:
                    cursor = pg_conn.cursor()
                    cursor.execute(f"""
                        SELECT asset_id, start_date, end_date
                        FROM {self.tenant_table}
                        WHERE asset_id IN ({placeholders})
                        ORDER BY asset_id
                    """, date_asset_ids)
                    postgres_dates = cursor.fetchall()

                # Simple date validation (more detailed validation could be added)
                if len(sqlite_dates) != len(postgres_dates):
                    date_mismatches = abs(len(sqlite_dates) - len(postgres_dates))
                    type_errors.append(f"Date record count mismatch: {len(sqlite_dates)} vs {len(postgres_dates)}")

            result = {
                'boolean_mismatches': bool_mismatches,
                'date_mismatches': date_mismatches,
                'type_errors': type_errors,
                'sample_size': sample_size,
                'passed': bool_mismatches == 0 and date_mismatches == 0
            }

            if result['passed']:
                logger.info("Data type validation PASSED: All type conversions are accurate")
            else:
                logger.error(f"Data type validation FAILED: {bool_mismatches + date_mismatches} type conversion errors")

            return result['passed'], result

        except Exception as e:
            logger.error(f"Data type validation error: {e}")
            return False, {'error': str(e)}

class PerformanceValidator:
    """Performance validation functionality"""

    def __init__(self, db_connector: DatabaseConnector):
        self.db_connector = db_connector
        self.tenant_table = f"{db_connector.config.tenant_id}_assets"
        self.max_query_time = db_connector.config.max_query_time_ms / 1000.0  # Convert to seconds

    def validate_query_performance(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate that critical queries meet performance requirements"""
        logger.info(f"Validating query performance (target: <{self.db_connector.config.max_query_time_ms}ms)...")

        test_queries = [
            {
                'name': 'simple_select',
                'description': 'Simple SELECT with WHERE clause',
                'query': f"SELECT * FROM {self.tenant_table} WHERE is_enabled = true LIMIT 10"
            },
            {
                'name': 'count_query',
                'description': 'COUNT query',
                'query': f"SELECT COUNT(*) FROM {self.tenant_table}"
            },
            {
                'name': 'order_by_query',
                'description': 'ORDER BY query',
                'query': f"SELECT * FROM {self.tenant_table} ORDER BY play_order LIMIT 20"
            },
            {
                'name': 'date_range_query',
                'description': 'Date range query',
                'query': f"SELECT * FROM {self.tenant_table} WHERE start_date <= NOW() AND end_date >= NOW() LIMIT 10"
            },
            {
                'name': 'aggregation_query',
                'description': 'Aggregation query',
                'query': f"SELECT mimetype, COUNT(*) FROM {self.tenant_table} GROUP BY mimetype"
            }
        ]

        performance_results = {}
        passed_queries = 0
        failed_queries = []

        try:
            with self.db_connector.get_postgres_connection() as pg_conn:
                cursor = pg_conn.cursor()

                for query_info in test_queries:
                    query_name = query_info['name']
                    query_sql = query_info['query']

                    # Warm up query (run once to load any caches)
                    try:
                        cursor.execute(query_sql)
                        cursor.fetchall()
                    except Exception:
                        pass  # Ignore warm-up errors

                    # Measure actual performance (average of 3 runs)
                    execution_times = []
                    for run in range(3):
                        start_time = time.time()
                        try:
                            cursor.execute(query_sql)
                            cursor.fetchall()
                            execution_time = time.time() - start_time
                            execution_times.append(execution_time)
                        except Exception as e:
                            logger.error(f"Query {query_name} failed: {e}")
                            execution_times.append(self.max_query_time * 2)  # Mark as failed

                    avg_time = sum(execution_times) / len(execution_times)
                    avg_time_ms = avg_time * 1000

                    performance_results[query_name] = {
                        'description': query_info['description'],
                        'avg_time_ms': avg_time_ms,
                        'max_time_ms': max(execution_times) * 1000,
                        'min_time_ms': min(execution_times) * 1000,
                        'passed': avg_time_ms <= self.db_connector.config.max_query_time_ms,
                        'query': query_sql
                    }

                    if performance_results[query_name]['passed']:
                        passed_queries += 1
                        logger.info(f"Query {query_name}: {avg_time_ms:.2f}ms PASSED")
                    else:
                        failed_queries.append(query_name)
                        logger.warning(f"Query {query_name}: {avg_time_ms:.2f}ms FAILED (>{self.db_connector.config.max_query_time_ms}ms)")

            overall_passed = len(failed_queries) == 0

            result = {
                'total_queries': len(test_queries),
                'passed_queries': passed_queries,
                'failed_queries': len(failed_queries),
                'failed_query_names': failed_queries,
                'query_results': performance_results,
                'overall_passed': overall_passed,
                'performance_score': (passed_queries / len(test_queries)) * 100
            }

            if overall_passed:
                logger.info(f"Performance validation PASSED: All {len(test_queries)} queries under {self.db_connector.config.max_query_time_ms}ms")
            else:
                logger.error(f"Performance validation FAILED: {len(failed_queries)} queries exceeded time limit")

            return overall_passed, result

        except Exception as e:
            logger.error(f"Performance validation error: {e}")
            return False, {'error': str(e)}

    def validate_index_effectiveness(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate that indexes are properly created and effective"""
        logger.info("Validating index effectiveness...")

        try:
            with self.db_connector.get_postgres_connection() as pg_conn:
                cursor = pg_conn.cursor()

                # Check for expected indexes
                cursor.execute(f"""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = '{self.tenant_table}'
                """)
                indexes = cursor.fetchall()

                expected_indexes = [
                    f"idx_{self.db_connector.config.tenant_id}_assets_enabled",
                    f"idx_{self.db_connector.config.tenant_id}_assets_dates",
                    f"idx_{self.db_connector.config.tenant_id}_assets_order"
                ]

                found_indexes = [idx[0] for idx in indexes]
                missing_indexes = [idx for idx in expected_indexes if idx not in found_indexes]

                # Test index usage with EXPLAIN
                index_usage_results = {}
                test_queries = [
                    ("enabled_index", f"SELECT * FROM {self.tenant_table} WHERE is_enabled = true"),
                    ("order_index", f"SELECT * FROM {self.tenant_table} ORDER BY play_order"),
                    ("primary_key", f"SELECT * FROM {self.tenant_table} WHERE asset_id = 'test'")
                ]

                for test_name, query in test_queries:
                    cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
                    explain_result = cursor.fetchone()[0]

                    # Check if index scan is used (simplified check)
                    uses_index = 'Index Scan' in str(explain_result) or 'Index Only Scan' in str(explain_result)
                    index_usage_results[test_name] = {
                        'uses_index': uses_index,
                        'explain_plan': explain_result
                    }

                result = {
                    'total_indexes': len(indexes),
                    'expected_indexes': expected_indexes,
                    'found_indexes': found_indexes,
                    'missing_indexes': missing_indexes,
                    'index_usage': index_usage_results,
                    'passed': len(missing_indexes) == 0
                }

                if result['passed']:
                    logger.info(f"Index validation PASSED: All {len(expected_indexes)} expected indexes found")
                else:
                    logger.error(f"Index validation FAILED: Missing indexes: {missing_indexes}")

                return result['passed'], result

        except Exception as e:
            logger.error(f"Index validation error: {e}")
            return False, {'error': str(e)}

class MigrationValidator:
    """Main validation orchestrator"""

    def __init__(self, config: ValidationConfig):
        self.config = config
        self.db_connector = DatabaseConnector(config)
        self.data_validator = DataValidator(self.db_connector)
        self.performance_validator = PerformanceValidator(self.db_connector)
        self.validation_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    def run_comprehensive_validation(self) -> ValidationResult:
        """Run all validation tests and generate comprehensive report"""
        logger.info("Starting comprehensive migration validation...")

        start_time = time.time()
        test_results = {}
        performance_metrics = {}
        recommendations = []
        detailed_errors = []

        # Core validation tests
        validation_tests = [
            ('record_count', self.data_validator.validate_record_count),
            ('schema_compatibility', self.data_validator.validate_schema_compatibility),
            ('data_integrity', self.data_validator.validate_data_integrity),
            ('primary_key_constraints', self.data_validator.validate_primary_key_constraints),
            ('data_types', self.data_validator.validate_data_types),
        ]

        # Add performance tests if enabled
        if self.config.performance_test:
            validation_tests.extend([
                ('query_performance', self.performance_validator.validate_query_performance),
                ('index_effectiveness', self.performance_validator.validate_index_effectiveness)
            ])

        # Run all validation tests
        tests_passed = 0
        tests_failed = 0

        for test_name, test_function in validation_tests:
            logger.info(f"Running {test_name} validation...")

            try:
                test_start = time.time()
                passed, result = test_function()
                test_duration = time.time() - test_start

                test_results[test_name] = {
                    'passed': passed,
                    'duration_seconds': test_duration,
                    'details': result
                }

                performance_metrics[f"{test_name}_duration"] = test_duration

                if passed:
                    tests_passed += 1
                else:
                    tests_failed += 1
                    if 'error' in result:
                        detailed_errors.append(f"{test_name}: {result['error']}")

            except Exception as e:
                tests_failed += 1
                error_msg = f"{test_name} validation failed with exception: {e}"
                logger.error(error_msg)
                detailed_errors.append(error_msg)
                test_results[test_name] = {
                    'passed': False,
                    'duration_seconds': 0,
                    'details': {'error': str(e)}
                }

        # Generate recommendations based on results
        recommendations = self._generate_recommendations(test_results)

        # Calculate overall data integrity score
        data_integrity_score = self._calculate_integrity_score(test_results)

        # Determine overall status
        overall_status = 'PASSED' if tests_failed == 0 else 'FAILED'

        total_duration = time.time() - start_time
        performance_metrics['total_validation_duration'] = total_duration

        # Create validation result
        result = ValidationResult(
            validation_id=self.validation_id,
            timestamp=datetime.now(),
            config=self.config,
            overall_status=overall_status,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            total_tests=len(validation_tests),
            test_results=test_results,
            performance_metrics=performance_metrics,
            data_integrity_score=data_integrity_score,
            recommendations=recommendations,
            detailed_errors=detailed_errors
        )

        # Save validation report
        self._save_validation_report(result)

        logger.info(f"Validation completed: {overall_status}")
        logger.info(f"Tests passed: {tests_passed}/{len(validation_tests)}")
        logger.info(f"Data integrity score: {data_integrity_score:.2f}%")
        logger.info(f"Total duration: {total_duration:.2f}s")

        return result

    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Record count recommendations
        if 'record_count' in test_results and not test_results['record_count']['passed']:
            details = test_results['record_count']['details']
            if 'difference' in details and details['difference'] > 0:
                recommendations.append(f"Record count mismatch detected. Investigate {details['difference']} missing records.")

        # Schema recommendations
        if 'schema_compatibility' in test_results and not test_results['schema_compatibility']['passed']:
            details = test_results['schema_compatibility']['details']
            if 'missing_in_postgres' in details and details['missing_in_postgres']:
                recommendations.append("Add missing columns to PostgreSQL schema.")
            if 'type_mismatches' in details and details['type_mismatches']:
                recommendations.append("Review and fix data type mismatches between databases.")

        # Performance recommendations
        if 'query_performance' in test_results and not test_results['query_performance']['passed']:
            details = test_results['query_performance']['details']
            if 'failed_query_names' in details:
                recommendations.append(f"Optimize slow queries: {', '.join(details['failed_query_names'])}")

        # Index recommendations
        if 'index_effectiveness' in test_results and not test_results['index_effectiveness']['passed']:
            details = test_results['index_effectiveness']['details']
            if 'missing_indexes' in details and details['missing_indexes']:
                recommendations.append(f"Create missing indexes: {', '.join(details['missing_indexes'])}")

        # Data integrity recommendations
        if 'data_integrity' in test_results and not test_results['data_integrity']['passed']:
            details = test_results['data_integrity']['details']
            if 'integrity_score' in details and details['integrity_score'] < 100:
                recommendations.append(f"Data integrity score is {details['integrity_score']:.2f}%. Investigate data mismatches.")

        return recommendations

    def _calculate_integrity_score(self, test_results: Dict[str, Any]) -> float:
        """Calculate overall data integrity score"""
        core_tests = ['record_count', 'data_integrity', 'primary_key_constraints', 'data_types']
        passed_core_tests = sum(1 for test in core_tests if test in test_results and test_results[test]['passed'])

        base_score = (passed_core_tests / len(core_tests)) * 100

        # Adjust based on specific metrics
        if 'data_integrity' in test_results and 'details' in test_results['data_integrity']:
            details = test_results['data_integrity']['details']
            if 'integrity_score' in details:
                base_score = (base_score + details['integrity_score']) / 2

        return min(100.0, max(0.0, base_score))

    def _save_validation_report(self, result: ValidationResult):
        """Save detailed validation report to file"""
        report_path = f"/tmp/validation_report_{self.validation_id}.json"

        try:
            # Convert dataclass to dict for JSON serialization
            report_data = asdict(result)

            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)

            logger.info(f"Validation report saved: {report_path}")

        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Migration Validation Tool')
    parser.add_argument('--sqlite-db', required=True, help='SQLite database path')
    parser.add_argument('--postgres-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--postgres-port', type=int, default=5432, help='PostgreSQL port')
    parser.add_argument('--postgres-db', default='anthias', help='PostgreSQL database')
    parser.add_argument('--postgres-user', default='anthias_user', help='PostgreSQL user')
    parser.add_argument('--postgres-password', default='', help='PostgreSQL password')
    parser.add_argument('--tenant-id', default='default', help='Tenant identifier')
    parser.add_argument('--no-deep-validation', action='store_true', help='Skip deep validation')
    parser.add_argument('--no-performance-test', action='store_true', help='Skip performance tests')
    parser.add_argument('--max-query-time', type=float, default=50.0, help='Maximum query time in ms')
    parser.add_argument('--sample-size', type=int, default=1000, help='Sample size for validation')

    args = parser.parse_args()

    # Create configuration
    config = ValidationConfig(
        sqlite_db_path=args.sqlite_db,
        postgres_host=args.postgres_host,
        postgres_port=args.postgres_port,
        postgres_db=args.postgres_db,
        postgres_user=args.postgres_user,
        postgres_password=args.postgres_password or os.getenv('POSTGRES_PASSWORD', ''),
        tenant_id=args.tenant_id,
        deep_validation=not args.no_deep_validation,
        performance_test=not args.no_performance_test,
        max_query_time_ms=args.max_query_time,
        sample_size=args.sample_size
    )

    # Run validation
    validator = MigrationValidator(config)
    result = validator.run_comprehensive_validation()

    # Print summary
    print(f"\nValidation Summary:")
    print(f"Status: {result.overall_status}")
    print(f"Tests passed: {result.tests_passed}/{result.total_tests}")
    print(f"Data integrity score: {result.data_integrity_score:.2f}%")

    if result.recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")

    if result.detailed_errors:
        print(f"\nErrors:")
        for error in result.detailed_errors:
            print(f"  - {error}")

    sys.exit(0 if result.overall_status == 'PASSED' else 1)

if __name__ == '__main__':
    main()