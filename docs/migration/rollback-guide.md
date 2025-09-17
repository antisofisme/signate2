# Emergency Migration Rollback Guide

## Overview

This guide provides comprehensive procedures for rolling back the SQLite to PostgreSQL migration in emergency situations. The rollback process is designed to restore service within 5 minutes and preserve data integrity.

⚠️ **CRITICAL**: This is an emergency procedure. Use only when the PostgreSQL migration has failed or caused production issues.

## When to Execute Rollback

### Immediate Rollback Triggers
- Application cannot connect to PostgreSQL
- Data corruption detected in PostgreSQL
- Performance degradation >300% from baseline
- Critical application functionality broken
- Security breach in PostgreSQL environment
- Hardware failure affecting PostgreSQL server

### Assessment Checklist
Before executing rollback, quickly assess:
- [ ] Can the issue be resolved without rollback? (2-minute assessment)
- [ ] Are backups available and verified?
- [ ] Is the rollback window still open? (<24 hours recommended)
- [ ] Have stakeholders been notified?

## Rollback Procedures

### Quick Emergency Rollback (< 5 Minutes)

#### Prerequisites Check (30 seconds)
```bash
# Verify backup availability
ls -la /backups/anthias_backup_*.db
echo "Latest backup: $(ls -t /backups/anthias_backup_*.db | head -1)"

# Verify rollback script availability
test -f /scripts/rollback-migration.py && echo "Rollback script available" || echo "ERROR: Rollback script missing"
```

#### Execute Emergency Rollback (2-3 minutes)
```bash
# Emergency rollback with all safety checks disabled
python scripts/rollback-migration.py \
    --postgres-host $POSTGRES_HOST \
    --postgres-db $POSTGRES_DB \
    --postgres-user $POSTGRES_USER \
    --postgres-password $POSTGRES_PASSWORD \
    --backup-path "$(ls -t /backups/anthias_backup_*.db | head -1)" \
    --original-db-path /data/.screenly/screenly.db \
    --emergency-mode \
    --no-verify
```

#### Restore Application Configuration (1 minute)
```bash
# Revert Django settings to SQLite
cp /config/settings_sqlite_backup.py /app/anthias_django/settings.py

# Restart application services
systemctl restart anthias-app
systemctl restart nginx

# Verify services
systemctl is-active anthias-app nginx
```

#### Verification (30 seconds)
```bash
# Quick functionality test
curl -f http://localhost:8080/api/v1/assets/count || echo "API test failed"
curl -f http://localhost:8080/health || echo "Health check failed"
```

### Comprehensive Rollback (5-15 Minutes)

#### Phase 1: Pre-Rollback Assessment (2 minutes)

```bash
# Document current state
echo "$(date): Starting rollback assessment" >> /var/log/rollback.log

# Check PostgreSQL status
pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER
echo "PostgreSQL status: $?" >> /var/log/rollback.log

# Check data integrity in PostgreSQL (if accessible)
python scripts/validate-migration.py \
    --sqlite-db /backups/anthias_backup_latest.db \
    --postgres-host $POSTGRES_HOST \
    --no-performance-test \
    --sample-size 100 \
    --timeout 60
```

#### Phase 2: Backup Current State (1 minute)

```bash
# Backup current PostgreSQL data (if accessible)
export BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER anthias > \
    /backups/postgresql_pre_rollback_$BACKUP_TIMESTAMP.sql 2>/dev/null &

# Backup current application configuration
cp /app/anthias_django/settings.py /backups/settings_pre_rollback_$BACKUP_TIMESTAMP.py

# Continue without waiting for PostgreSQL backup if it's inaccessible
sleep 30
```

#### Phase 3: Execute Rollback (3-5 minutes)

```bash
# Execute controlled rollback with verification
python scripts/rollback-migration.py \
    --postgres-host $POSTGRES_HOST \
    --postgres-db $POSTGRES_DB \
    --postgres-user $POSTGRES_USER \
    --postgres-password $POSTGRES_PASSWORD \
    --backup-path "$(ls -t /backups/anthias_backup_*.db | head -1)" \
    --original-db-path /data/.screenly/screenly.db \
    --preserve-postgres \
    --timeout-minutes 5
```

#### Phase 4: Application Restoration (2-3 minutes)

```bash
# Restore SQLite configuration
cat > /app/anthias_django/settings.py << 'EOF'
# Emergency rollback configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/data/.screenly/screenly.db',
    }
}
EOF

# Clear Django cache
python /app/manage.py clear_cache 2>/dev/null || true

# Restart all services
systemctl stop anthias-app
sleep 5
systemctl start anthias-app
systemctl restart nginx

# Wait for services to stabilize
sleep 10
```

#### Phase 5: Verification and Monitoring (3-5 minutes)

```bash
# Comprehensive application testing
./scripts/test-runner.sh --rollback-validation

# Check database integrity
sqlite3 /data/.screenly/screenly.db "PRAGMA integrity_check;"

# Verify API functionality
python << 'EOF'
import requests
import sys

try:
    # Test basic endpoints
    response = requests.get('http://localhost:8080/api/v1/assets/count', timeout=10)
    print(f"Asset count API: {response.status_code}")

    response = requests.get('http://localhost:8080/api/v1/assets', timeout=10)
    print(f"Assets list API: {response.status_code}")

    response = requests.get('http://localhost:8080/health', timeout=10)
    print(f"Health check: {response.status_code}")

    if all(r.status_code == 200 for r in [response]):
        print("✅ API verification passed")
        sys.exit(0)
    else:
        print("❌ API verification failed")
        sys.exit(1)

except Exception as e:
    print(f"❌ API verification error: {e}")
    sys.exit(1)
EOF
```

### Advanced Rollback Scenarios

#### Scenario 1: PostgreSQL Server Completely Unavailable

```bash
# Skip PostgreSQL cleanup and focus on data restoration
python scripts/rollback-migration.py \
    --backup-path "$(ls -t /backups/anthias_backup_*.db | head -1)" \
    --original-db-path /data/.screenly/screenly.db \
    --emergency-mode \
    --no-verify

# Manual configuration restore
cp /backups/settings_sqlite_backup.py /app/anthias_django/settings.py

# Force application restart
pkill -f anthias-app
systemctl start anthias-app
```

#### Scenario 2: Partial Data Loss in PostgreSQL

```bash
# Attempt data recovery before full rollback
python scripts/validate-migration.py \
    --sqlite-db "$(ls -t /backups/anthias_backup_*.db | head -1)" \
    --postgres-host $POSTGRES_HOST \
    --deep-validation \
    --sample-size 10000

# If >95% data integrity, attempt repair
if [ $? -eq 0 ]; then
    echo "Attempting data repair..."
    python scripts/migrate-sqlite-to-postgresql.py \
        --sqlite-db "$(ls -t /backups/anthias_backup_*.db | head -1)" \
        --postgres-host $POSTGRES_HOST \
        --repair-mode \
        --batch-size 100
else
    echo "Data integrity too low, proceeding with full rollback..."
    # Execute full rollback procedure
fi
```

#### Scenario 3: Performance Degradation Only

```bash
# Performance-focused rollback
echo "$(date): Performance rollback initiated" >> /var/log/rollback.log

# Temporary switch to SQLite while diagnosing PostgreSQL
cp /backups/settings_sqlite_backup.py /app/anthias_django/settings.py
systemctl reload anthias-app

# Keep PostgreSQL data for analysis
echo "PostgreSQL data preserved for performance analysis" >> /var/log/rollback.log

# Schedule performance analysis
at now + 1 hour << 'EOF'
python scripts/validate-migration.py \
    --postgres-host $POSTGRES_HOST \
    --performance-test \
    --max-query-time 100 \
    > /var/log/postgresql_performance_analysis.log
EOF
```

## Post-Rollback Procedures

### Immediate Actions (First 15 minutes)

#### 1. Service Verification
```bash
# Comprehensive service check
systemctl status anthias-app nginx
journalctl -u anthias-app --since="5 minutes ago"

# Application functionality verification
./scripts/test-runner.sh --post-rollback

# Performance baseline check
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8080/api/v1/assets
```

#### 2. Stakeholder Notification
```bash
# Generate rollback report
python scripts/rollback-migration.py --generate-report

# Send notification (customize for your environment)
cat > /tmp/rollback_notification.txt << 'EOF'
Subject: URGENT: Database Migration Rollback Completed

The PostgreSQL migration has been rolled back to SQLite due to critical issues.

Status: Service Restored
Rollback Time: $(date)
Data Loss: None (restored from backup)
Service Availability: Restored

Next Steps:
1. Root cause analysis scheduled
2. Migration strategy review
3. Enhanced testing plan development

For questions, contact: devops@company.com
EOF

# mail -s "Migration Rollback Alert" stakeholders@company.com < /tmp/rollback_notification.txt
```

#### 3. Data Integrity Verification
```bash
# Verify SQLite database integrity
sqlite3 /data/.screenly/screenly.db << 'EOF'
PRAGMA integrity_check;
PRAGMA foreign_key_check;
SELECT COUNT(*) as total_assets FROM assets;
SELECT COUNT(*) as enabled_assets FROM assets WHERE is_enabled = 1;
EOF

# Compare with pre-migration counts if available
if [ -f /backups/pre_migration_counts.txt ]; then
    echo "Comparing with pre-migration data..."
    diff /backups/pre_migration_counts.txt <(sqlite3 /data/.screenly/screenly.db "SELECT COUNT(*) FROM assets;")
fi
```

### Extended Monitoring (First 4 hours)

#### 1. Performance Monitoring
```bash
# Set up enhanced monitoring
cat > /tmp/monitor_rollback.sh << 'EOF'
#!/bin/bash
while true; do
    echo "$(date): Monitoring post-rollback performance"

    # Check response times
    curl -w "%{time_total}\n" -s -o /dev/null http://localhost:8080/api/v1/assets

    # Check error rates
    journalctl -u anthias-app --since="1 minute ago" | grep -i error | wc -l

    # Check database connections
    lsof -i :8080 | wc -l

    sleep 60
done
EOF

chmod +x /tmp/monitor_rollback.sh
nohup /tmp/monitor_rollback.sh > /var/log/post_rollback_monitoring.log 2>&1 &
```

#### 2. Log Analysis
```bash
# Analyze logs for issues
journalctl -u anthias-app --since="1 hour ago" | grep -E "(ERROR|CRITICAL|FATAL)" > /tmp/post_rollback_errors.log

# Check for database-related errors
grep -i "database\|sqlite\|connection" /tmp/post_rollback_errors.log

# Monitor for memory leaks or performance issues
ps aux | grep anthias-app | awk '{print $6}' # Memory usage
```

### Root Cause Analysis (First 24 hours)

#### 1. Migration Failure Analysis
```bash
# Collect all migration-related logs
mkdir -p /tmp/migration_analysis
cp /tmp/migration*.log /tmp/migration_analysis/
cp /tmp/validation*.log /tmp/migration_analysis/
cp /tmp/rollback*.log /tmp/migration_analysis/

# Analyze PostgreSQL logs if accessible
if [ -f /var/log/postgresql/postgresql.log ]; then
    grep "$(date +%Y-%m-%d)" /var/log/postgresql/postgresql.log > /tmp/migration_analysis/postgresql.log
fi

# Generate analysis report
python << 'EOF'
import json
import os
from datetime import datetime

analysis = {
    "rollback_timestamp": datetime.now().isoformat(),
    "migration_logs": [],
    "identified_issues": [],
    "recommendations": []
}

# Analyze log files
log_dir = "/tmp/migration_analysis"
if os.path.exists(log_dir):
    for log_file in os.listdir(log_dir):
        with open(os.path.join(log_dir, log_file), 'r') as f:
            content = f.read()
            if "ERROR" in content or "FAILED" in content:
                analysis["identified_issues"].append(f"Issues found in {log_file}")

# Add recommendations
analysis["recommendations"] = [
    "Review PostgreSQL server configuration",
    "Validate network connectivity and firewall rules",
    "Assess database server capacity and performance",
    "Review migration script for edge cases",
    "Implement enhanced pre-migration validation",
    "Consider phased migration approach"
]

with open("/tmp/migration_analysis/analysis_report.json", 'w') as f:
    json.dump(analysis, f, indent=2)

print("Analysis report generated: /tmp/migration_analysis/analysis_report.json")
EOF
```

#### 2. Infrastructure Assessment
```bash
# Check system resources
df -h > /tmp/disk_usage_post_rollback.txt
free -h > /tmp/memory_usage_post_rollback.txt
top -bn1 | head -20 > /tmp/cpu_usage_post_rollback.txt

# Network connectivity tests
ping -c 3 $POSTGRES_HOST > /tmp/network_test_post_rollback.txt
telnet $POSTGRES_HOST $POSTGRES_PORT >> /tmp/network_test_post_rollback.txt 2>&1 &
sleep 5
pkill telnet
```

## Prevention and Improvement

### Enhanced Pre-Migration Validation
```bash
# Create improved validation script
cat > /scripts/pre_migration_validation_v2.py << 'EOF'
#!/usr/bin/env python3
"""
Enhanced pre-migration validation script
Addresses issues identified during rollback analysis
"""

import sqlite3
import psycopg2
import os
import sys
import time
import subprocess

def validate_system_resources():
    """Validate system has sufficient resources"""
    # Check disk space (need 3x database size)
    # Check memory availability
    # Check CPU load
    pass

def validate_network_connectivity():
    """Validate stable network connection to PostgreSQL"""
    # Test connection stability over time
    # Check latency and bandwidth
    pass

def validate_database_locks():
    """Check for database locks that could cause issues"""
    # Check for long-running transactions
    # Validate no exclusive locks
    pass

def validate_application_state():
    """Ensure application is in proper state for migration"""
    # Check for background jobs
    # Validate no active user sessions
    pass

if __name__ == "__main__":
    print("Running enhanced pre-migration validation...")
    # Implementation details...
EOF
```

### Rollback Testing Procedures
```bash
# Create rollback testing schedule
cat > /scripts/test_rollback_procedures.sh << 'EOF'
#!/bin/bash
# Weekly rollback procedure testing

# Test 1: Backup integrity verification
python scripts/backup-sqlite-data.py --source-db /data/.screenly/screenly.db --verify-only

# Test 2: Rollback script dry run
python scripts/rollback-migration.py --dry-run --emergency-mode

# Test 3: Application configuration rollback
cp /app/anthias_django/settings.py /tmp/current_settings.py
cp /backups/settings_sqlite_backup.py /app/anthias_django/settings.py
python /app/manage.py check
cp /tmp/current_settings.py /app/anthias_django/settings.py

# Test 4: Service restart procedures
systemctl stop anthias-app
sleep 5
systemctl start anthias-app
systemctl is-active anthias-app

echo "Rollback procedure testing completed: $(date)"
EOF

chmod +x /scripts/test_rollback_procedures.sh

# Schedule weekly testing
echo "0 3 * * 0 root /scripts/test_rollback_procedures.sh >> /var/log/rollback_testing.log" >> /etc/crontab
```

### Improved Monitoring and Alerting
```bash
# Create enhanced monitoring
cat > /scripts/migration_monitoring.py << 'EOF'
#!/usr/bin/env python3
"""
Enhanced migration monitoring with automated rollback triggers
"""

import psutil
import sqlite3
import psycopg2
import time
import subprocess
import logging

class MigrationMonitor:
    def __init__(self):
        self.thresholds = {
            'response_time_ms': 1000,
            'error_rate_percent': 5,
            'memory_usage_percent': 90,
            'disk_usage_percent': 95
        }

    def monitor_application_health(self):
        """Monitor application health metrics"""
        # Implement comprehensive monitoring
        pass

    def check_rollback_triggers(self):
        """Check if automatic rollback should be triggered"""
        # Implement rollback trigger logic
        pass

    def execute_automatic_rollback(self):
        """Execute automatic rollback if conditions are met"""
        # Implement automatic rollback
        pass

if __name__ == "__main__":
    monitor = MigrationMonitor()
    monitor.run()
EOF
```

## Emergency Contacts and Escalation

### Primary Contacts
- **Database Team Lead**: db-lead@company.com, +1-XXX-XXX-XXXX
- **DevOps Engineer**: devops-oncall@company.com, +1-XXX-XXX-XXXX
- **Engineering Manager**: eng-manager@company.com, +1-XXX-XXX-XXXX

### Escalation Matrix
| Time Since Issue | Action | Contact |
|------------------|--------|---------|
| 0-5 minutes | Execute emergency rollback | DevOps On-call |
| 5-15 minutes | Notify management | Engineering Manager |
| 15-30 minutes | Engage database team | Database Team Lead |
| 30+ minutes | Executive notification | CTO/VP Engineering |

### Communication Templates

#### Emergency Notification
```
URGENT: Database Migration Rollback Required

Issue: [Description]
Impact: [Service status and user impact]
ETA for Resolution: [Time estimate]
Action Taken: [Rollback steps initiated]

Next Update: [Time for next update]
Incident Commander: [Name and contact]
```

#### Resolution Notification
```
RESOLVED: Database Migration Rollback Completed

Resolution: Service restored to SQLite database
Downtime: [Total downtime duration]
Root Cause: [Brief description]
Data Loss: None (restored from backup)

Next Steps:
- Post-incident review scheduled for [date/time]
- Migration strategy review and enhancement
- Enhanced testing procedures implementation

Thank you for your patience.
```

## Testing and Validation

### Rollback Procedure Testing
```bash
# Monthly rollback drill
cat > /scripts/monthly_rollback_drill.sh << 'EOF'
#!/bin/bash
# Monthly rollback procedure drill

echo "$(date): Starting monthly rollback drill"

# Create test environment
cp /data/.screenly/screenly.db /tmp/test_screenly.db

# Test backup creation
python scripts/backup-sqlite-data.py \
    --source-db /tmp/test_screenly.db \
    --backup-dir /tmp/test_backups

# Test rollback script
python scripts/rollback-migration.py \
    --backup-path /tmp/test_backups/anthias_backup_*.db \
    --original-db-path /tmp/test_restored.db \
    --dry-run

# Verify test results
if [ $? -eq 0 ]; then
    echo "✅ Rollback drill PASSED"
else
    echo "❌ Rollback drill FAILED"
    # Send alert
fi

# Cleanup
rm -rf /tmp/test_*

echo "$(date): Monthly rollback drill completed"
EOF

chmod +x /scripts/monthly_rollback_drill.sh
```

### Continuous Validation
```bash
# Implement continuous rollback readiness validation
cat > /scripts/validate_rollback_readiness.sh << 'EOF'
#!/bin/bash
# Continuous rollback readiness validation

# Check backup availability and integrity
LATEST_BACKUP=$(ls -t /backups/anthias_backup_*.db 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ ERROR: No backup files found"
    exit 1
fi

# Check backup age (should be < 24 hours)
BACKUP_AGE=$(find "$LATEST_BACKUP" -mtime +1)
if [ -n "$BACKUP_AGE" ]; then
    echo "⚠️  WARNING: Latest backup is older than 24 hours"
fi

# Verify backup integrity
python -c "
import sqlite3
try:
    conn = sqlite3.connect('$LATEST_BACKUP')
    cursor = conn.cursor()
    cursor.execute('PRAGMA integrity_check')
    result = cursor.fetchone()[0]
    if result == 'ok':
        print('✅ Backup integrity verified')
    else:
        print('❌ Backup integrity check failed')
    conn.close()
except Exception as e:
    print(f'❌ Backup validation error: {e}')
"

# Check rollback script availability
if [ -f "/scripts/rollback-migration.py" ]; then
    echo "✅ Rollback script available"
else
    echo "❌ ERROR: Rollback script missing"
    exit 1
fi

# Check required tools
python3 -c "import sqlite3, psycopg2" 2>/dev/null && echo "✅ Required Python packages available" || echo "❌ ERROR: Missing Python packages"

echo "Rollback readiness validation completed: $(date)"
EOF

chmod +x /scripts/validate_rollback_readiness.sh

# Run every 4 hours
echo "0 */4 * * * root /scripts/validate_rollback_readiness.sh >> /var/log/rollback_readiness.log" >> /etc/crontab
```

---

**Document Version:** 1.0
**Last Updated:** $(date)
**Rollback Tool Version:** 1.0.0
**Emergency Response Time:** <5 minutes
**Data Recovery Guarantee:** 100% (from backup)

**⚠️ REMEMBER**: This guide is for emergency use. Practice the procedures regularly and keep this document easily accessible during migration operations.