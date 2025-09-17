# SQLite to PostgreSQL Migration Procedure

## Overview

This document provides a comprehensive step-by-step procedure for migrating the Anthias application from SQLite to PostgreSQL with zero-downtime requirements and comprehensive rollback capabilities.

## Prerequisites

### System Requirements
- Python 3.8+
- PostgreSQL 12+ server running
- SQLite 3.x database
- Sufficient disk space (3x database size recommended)
- Network connectivity to PostgreSQL server

### Required Python Packages
```bash
pip install psycopg2-binary sqlite3 hashlib
```

### Environment Setup
```bash
# Set PostgreSQL connection details
export POSTGRES_PASSWORD="your_secure_password"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="anthias"
export POSTGRES_USER="anthias_user"
```

## Pre-Migration Checklist

### 1. Environment Validation
- [ ] PostgreSQL server is running and accessible
- [ ] Database user has CREATE, INSERT, UPDATE, DELETE privileges
- [ ] Sufficient disk space available (3x current database size)
- [ ] Application is in maintenance mode or low-traffic period
- [ ] All dependencies are installed

### 2. Backup Creation
```bash
# Create comprehensive backup
python scripts/backup-sqlite-data.py \
    --source-db /data/.screenly/screenly.db \
    --backup-dir /backups \
    --retention-days 30
```

### 3. Infrastructure Verification
```bash
# Test PostgreSQL connectivity
psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT version();"

# Verify disk space
df -h /data
df -h /backups
```

## Migration Procedure

### Phase 1: Pre-Migration Validation

#### Step 1.1: Database Health Check
```bash
# Validate source database integrity
python scripts/backup-sqlite-data.py \
    --source-db /data/.screenly/screenly.db \
    --list

# Check for data quality issues
sqlite3 /data/.screenly/screenly.db <<EOF
PRAGMA integrity_check;
SELECT COUNT(*) FROM assets;
SELECT COUNT(*) FROM assets WHERE asset_id IS NULL;
EOF
```

#### Step 1.2: Schema Preparation
```bash
# Verify PostgreSQL schema readiness
python scripts/migrate-sqlite-to-postgresql.py \
    --sqlite-db /data/.screenly/screenly.db \
    --postgres-host $POSTGRES_HOST \
    --postgres-db $POSTGRES_DB \
    --postgres-user $POSTGRES_USER \
    --postgres-password $POSTGRES_PASSWORD \
    --tenant-id default \
    --dry-run
```

### Phase 2: Data Migration

#### Step 2.1: Execute Migration
```bash
# Perform the actual migration
python scripts/migrate-sqlite-to-postgresql.py \
    --sqlite-db /data/.screenly/screenly.db \
    --postgres-host $POSTGRES_HOST \
    --postgres-db $POSTGRES_DB \
    --postgres-user $POSTGRES_USER \
    --postgres-password $POSTGRES_PASSWORD \
    --tenant-id default \
    --batch-size 1000 \
    --backup-enabled
```

#### Step 2.2: Monitor Migration Progress
```bash
# Check migration logs
tail -f /tmp/migration.log

# Monitor PostgreSQL activity
psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables
WHERE tablename LIKE '%_assets';
"
```

### Phase 3: Validation and Testing

#### Step 3.1: Data Integrity Validation
```bash
# Comprehensive validation
python scripts/validate-migration.py \
    --sqlite-db /data/.screenly/screenly.db \
    --postgres-host $POSTGRES_HOST \
    --postgres-db $POSTGRES_DB \
    --postgres-user $POSTGRES_USER \
    --postgres-password $POSTGRES_PASSWORD \
    --tenant-id default \
    --sample-size 1000
```

#### Step 3.2: Performance Testing
```bash
# Run performance benchmarks
python scripts/validate-migration.py \
    --sqlite-db /data/.screenly/screenly.db \
    --postgres-host $POSTGRES_HOST \
    --postgres-db $POSTGRES_DB \
    --postgres-user $POSTGRES_USER \
    --postgres-password $POSTGRES_PASSWORD \
    --tenant-id default \
    --max-query-time 50
```

#### Step 3.3: Application Testing
```bash
# Test application API endpoints
curl -X GET http://localhost:8080/api/v1/assets
curl -X GET http://localhost:8080/api/v1/assets/count

# Verify asset operations
curl -X POST http://localhost:8080/api/v1/assets \
    -H "Content-Type: application/json" \
    -d '{"name": "test_asset", "uri": "http://example.com/test.jpg"}'
```

### Phase 4: Application Configuration Update

#### Step 4.1: Update Django Settings
```python
# Update anthias_django/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'anthias',
        'USER': 'anthias_user',
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}
```

#### Step 4.2: Update Connection Pooling
```python
# Add to settings.py for production
DATABASES['default']['OPTIONS'].update({
    'MAX_CONNS': 20,
    'conn_max_age': 600,
})
```

#### Step 4.3: Database Migrations
```bash
# Apply Django migrations to PostgreSQL
python manage.py migrate --database=default

# Verify migration state
python manage.py showmigrations
```

### Phase 5: Production Deployment

#### Step 5.1: Application Restart
```bash
# Restart application services
systemctl restart anthias-app
systemctl restart nginx

# Verify services are running
systemctl status anthias-app
systemctl status nginx
```

#### Step 5.2: Final Verification
```bash
# Test all critical endpoints
./scripts/test-runner.sh --migration-validation

# Check application logs
journalctl -u anthias-app -f

# Monitor PostgreSQL connections
psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE datname = 'anthias';
"
```

## Post-Migration Tasks

### 1. Performance Optimization
```sql
-- Analyze tables for optimal query planning
ANALYZE default_assets;

-- Update table statistics
VACUUM ANALYZE default_assets;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'default_assets';
```

### 2. Monitoring Setup
```bash
# Set up automated backup schedule
cat > /etc/cron.d/anthias-backup << 'EOF'
0 2 * * * postgres /usr/bin/pg_dump -h localhost -U anthias_user anthias > /backups/anthias_$(date +\%Y\%m\%d).sql
EOF

# Monitor database performance
cat > /etc/cron.d/anthias-monitoring << 'EOF'
*/5 * * * * postgres /usr/bin/psql -h localhost -U anthias_user -d anthias -c "SELECT COUNT(*) FROM default_assets WHERE is_enabled = true" >> /var/log/anthias-monitoring.log
EOF
```

### 3. Cleanup Tasks
```bash
# Archive old SQLite database
mv /data/.screenly/screenly.db /backups/screenly_pre_migration_$(date +%Y%m%d).db

# Clean up temporary migration files
rm -f /tmp/migration_*.json
rm -f /tmp/validation_*.json

# Update documentation
git add docs/migration/
git commit -m "Document PostgreSQL migration completion"
```

## Rollback Procedure (Emergency)

### Quick Rollback (< 5 minutes)
```bash
# Emergency rollback to SQLite
python scripts/rollback-migration.py \
    --postgres-host $POSTGRES_HOST \
    --postgres-db $POSTGRES_DB \
    --postgres-user $POSTGRES_USER \
    --postgres-password $POSTGRES_PASSWORD \
    --backup-path /backups/anthias_backup_YYYYMMDD_HHMMSS.db \
    --original-db-path /data/.screenly/screenly.db \
    --emergency-mode
```

### Detailed Rollback Process
See [rollback-guide.md](rollback-guide.md) for comprehensive rollback procedures.

## Troubleshooting

### Common Issues

#### Connection Errors
```bash
# Test PostgreSQL connectivity
pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER

# Check firewall settings
telnet $POSTGRES_HOST $POSTGRES_PORT

# Verify authentication
psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT current_user;"
```

#### Performance Issues
```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
WHERE query LIKE '%default_assets%'
ORDER BY mean_time DESC
LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'default_assets'
AND n_distinct > 100;
```

#### Data Inconsistencies
```bash
# Run comprehensive validation
python scripts/validate-migration.py \
    --sqlite-db /backups/screenly_backup.db \
    --postgres-host $POSTGRES_HOST \
    --deep-validation \
    --sample-size 10000
```

### Support and Escalation

#### Log Collection
```bash
# Collect all relevant logs
mkdir -p /tmp/migration-support
cp /tmp/migration.log /tmp/migration-support/
cp /tmp/validation.log /tmp/migration-support/
cp /var/log/postgresql/*.log /tmp/migration-support/
journalctl -u anthias-app > /tmp/migration-support/anthias.log

# Create support package
tar -czf migration-support-$(date +%Y%m%d).tar.gz /tmp/migration-support/
```

#### Emergency Contacts
- Database Team: db-team@company.com
- DevOps Team: devops@company.com
- On-call Engineer: +1-XXX-XXX-XXXX

## Success Criteria

The migration is considered successful when:

- [ ] All data integrity validations pass (100% score)
- [ ] All performance tests meet requirements (<50ms queries)
- [ ] Application functionality tests pass
- [ ] Zero data loss confirmed
- [ ] Rollback capability verified
- [ ] Monitoring and alerting configured
- [ ] Documentation updated
- [ ] Team training completed

## Security Considerations

### Database Security
```sql
-- Ensure proper user permissions
REVOKE ALL PRIVILEGES ON DATABASE anthias FROM PUBLIC;
GRANT CONNECT ON DATABASE anthias TO anthias_user;
GRANT USAGE ON SCHEMA public TO anthias_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anthias_user;

-- Enable connection logging
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
SELECT pg_reload_conf();
```

### Data Protection
```bash
# Encrypt backup files
gpg --symmetric --cipher-algo AES256 /backups/anthias_backup.db

# Set proper file permissions
chmod 600 /backups/*.db
chown postgres:postgres /backups/*.db
```

### Network Security
```bash
# Configure PostgreSQL to accept connections only from application servers
echo "host anthias anthias_user 10.0.1.0/24 md5" >> /etc/postgresql/*/main/pg_hba.conf
systemctl reload postgresql
```

## Performance Benchmarks

### Expected Performance Metrics
- Simple SELECT queries: <10ms
- COUNT queries: <25ms
- ORDER BY queries: <30ms
- Complex aggregations: <50ms
- Bulk inserts (1000 records): <500ms

### Monitoring Queries
```sql
-- Monitor query performance
SELECT
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time
FROM pg_stat_statements
WHERE query LIKE '%assets%'
ORDER BY mean_time DESC
LIMIT 20;

-- Monitor connection pooling
SELECT
    state,
    count(*) as connections
FROM pg_stat_activity
WHERE datname = 'anthias'
GROUP BY state;
```

## Maintenance Procedures

### Daily Tasks
```bash
#!/bin/bash
# Daily maintenance script

# Update table statistics
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "ANALYZE default_assets;"

# Check database size
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT pg_size_pretty(pg_database_size('anthias'));"

# Monitor query performance
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT COUNT(*) FROM pg_stat_statements WHERE mean_time > 50;"
```

### Weekly Tasks
```bash
#!/bin/bash
# Weekly maintenance script

# Full vacuum analyze
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE default_assets;"

# Backup database
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER anthias | gzip > /backups/weekly_backup_$(date +%Y%m%d).sql.gz

# Check index bloat
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f /scripts/check_index_bloat.sql
```

---

**Document Version:** 1.0
**Last Updated:** $(date)
**Migration Tool Version:** 1.0.0
**Reviewed By:** Database Team, DevOps Team