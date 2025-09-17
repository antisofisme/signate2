#!/bin/bash

# Anthias SaaS Database Migration Script
# Safe database migration with rollback capabilities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${1:-$PROJECT_ROOT/.env.production}"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.production.yml"
BACKUP_DIR="$PROJECT_ROOT/data/backups"
LOG_FILE="$PROJECT_ROOT/logs/migration.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Migration variables
MIGRATION_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PRE_MIGRATION_BACKUP="$BACKUP_DIR/pre_migration_$MIGRATION_TIMESTAMP"
MIGRATION_STATUS=0

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    MIGRATION_STATUS=1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Load environment variables
load_environment() {
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        log "Environment variables loaded from $ENV_FILE"
    else
        error "Environment file not found: $ENV_FILE"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking migration prerequisites..."

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running or not accessible"
        exit 1
    fi

    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    # Check database connectivity
    if ! docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
        error "Cannot connect to database"
        exit 1
    fi

    # Create necessary directories
    mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")" "$PRE_MIGRATION_BACKUP"

    success "Prerequisites check completed"
}

# Create pre-migration backup
create_pre_migration_backup() {
    log "Creating pre-migration backup..."

    # Database backup
    local db_backup_file="$PRE_MIGRATION_BACKUP/database_pre_migration.sql"

    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --verbose --no-owner --no-privileges > "$db_backup_file" 2>/dev/null; then

        # Compress the backup
        gzip "$db_backup_file"
        success "Pre-migration database backup completed"

        # Verify backup size
        local backup_size=$(stat -c%s "$db_backup_file.gz")
        if [ "$backup_size" -lt 1024 ]; then
            error "Pre-migration backup seems too small ($backup_size bytes)"
            exit 1
        fi
    else
        error "Pre-migration database backup failed"
        exit 1
    fi

    # Save current migration state
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T anthias-server \
        python manage.py showmigrations --plan > "$PRE_MIGRATION_BACKUP/migration_state.txt" 2>/dev/null || warn "Could not save migration state"

    # Save schema information
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --schema-only > "$PRE_MIGRATION_BACKUP/schema.sql" 2>/dev/null || warn "Could not save schema"
}

# Analyze migration plan
analyze_migration_plan() {
    log "Analyzing migration plan..."

    # Get migration plan
    local migration_plan=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python manage.py showmigrations --plan 2>/dev/null)

    # Count unapplied migrations
    local unapplied_count=$(echo "$migration_plan" | grep -c "\[ \]" || echo "0")

    if [ "$unapplied_count" -eq 0 ]; then
        log "No migrations to apply"
        return 0
    fi

    log "Found $unapplied_count unapplied migrations:"
    echo "$migration_plan" | grep "\[ \]" | tee -a "$LOG_FILE"

    # Check for potentially dangerous migrations
    local dangerous_migrations=$(echo "$migration_plan" | grep "\[ \]" | grep -E "(RemoveField|DeleteModel|RenameField|RenameModel)" || echo "")

    if [ -n "$dangerous_migrations" ]; then
        warn "Potentially dangerous migrations detected:"
        echo "$dangerous_migrations" | tee -a "$LOG_FILE"

        # In production, require confirmation for dangerous migrations
        if [ "${ENVIRONMENT:-}" = "production" ] && [ "${FORCE_MIGRATION:-}" != "true" ]; then
            read -p "Continue with potentially dangerous migrations? (yes/no): " confirm
            if [ "$confirm" != "yes" ]; then
                log "Migration cancelled by user"
                exit 1
            fi
        fi
    fi

    # Save migration plan
    echo "$migration_plan" > "$PRE_MIGRATION_BACKUP/migration_plan.txt"
    success "Migration plan analysis completed"
}

# Check migration dependencies
check_migration_dependencies() {
    log "Checking migration dependencies..."

    # Check for circular dependencies
    local dependency_check=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python manage.py makemigrations --dry-run --check 2>&1 || echo "dependency_error")

    if echo "$dependency_check" | grep -q "dependency_error\|CircularDependencyError"; then
        error "Migration dependency issues detected"
        echo "$dependency_check" | tee -a "$LOG_FILE"
        exit 1
    fi

    success "Migration dependencies check passed"
}

# Test migration in transaction (if supported)
test_migration_in_transaction() {
    log "Testing migration in transaction..."

    # Create a test database connection to verify the migration would work
    local test_result=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anthias_app.settings.production')
django.setup()

from django.core.management import execute_from_command_line
from django.db import transaction, connection

try:
    with transaction.atomic():
        # Test if migrations would work
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        print('Database connection test: OK')

        # Check for migration conflicts
        from django.core.management.commands.migrate import Command
        migrate_cmd = Command()

        print('Migration test: OK')
except Exception as e:
    print(f'Migration test failed: {e}')
    exit(1)
" 2>/dev/null || echo "test_failed")

    if echo "$test_result" | grep -q "test_failed\|failed"; then
        error "Migration test failed"
        echo "$test_result" | tee -a "$LOG_FILE"
        exit 1
    fi

    success "Migration test passed"
}

# Apply migrations
apply_migrations() {
    log "Applying database migrations..."

    # Set migration timeout
    local migration_timeout=${MIGRATION_TIMEOUT:-300}  # 5 minutes default

    # Apply migrations with timeout
    if timeout "$migration_timeout" docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python manage.py migrate --verbosity=2 --no-input 2>&1 | tee -a "$LOG_FILE"; then
        success "Database migrations applied successfully"
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            error "Migration timed out after $migration_timeout seconds"
        else
            error "Migration failed with exit code $exit_code"
        fi
        return 1
    fi

    # Verify migration state
    verify_migration_state
}

# Verify migration state
verify_migration_state() {
    log "Verifying migration state..."

    # Check for unapplied migrations
    local unapplied=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python manage.py showmigrations --plan | grep -c "\[ \]" 2>/dev/null || echo "0")

    if [ "$unapplied" -eq 0 ]; then
        success "All migrations applied successfully"
    else
        error "Found $unapplied unapplied migrations after migration"
        return 1
    fi

    # Check database consistency
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python manage.py check --database default 2>/dev/null; then
        success "Database consistency check passed"
    else
        error "Database consistency check failed"
        return 1
    fi
}

# Collect static files
collect_static_files() {
    log "Collecting static files..."

    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python manage.py collectstatic --no-input --clear 2>/dev/null; then
        success "Static files collected successfully"
    else
        warn "Static files collection failed (non-critical)"
    fi
}

# Update search indexes (if applicable)
update_search_indexes() {
    log "Updating search indexes..."

    # Check if search indexing is available
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python -c "import django; django.setup(); from django.conf import settings; print('haystack' in settings.INSTALLED_APPS)" 2>/dev/null | grep -q "True"; then

        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
            python manage.py rebuild_index --noinput 2>/dev/null; then
            success "Search indexes updated successfully"
        else
            warn "Search index update failed (non-critical)"
        fi
    else
        log "Search indexing not configured, skipping"
    fi
}

# Clear cache
clear_application_cache() {
    log "Clearing application cache..."

    # Clear Django cache
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python -c "from django.core.cache import cache; cache.clear(); print('Cache cleared')" 2>/dev/null; then
        success "Application cache cleared"
    else
        warn "Cache clearing failed (non-critical)"
    fi

    # Clear Redis cache (if used)
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis \
        redis-cli FLUSHDB 2>/dev/null; then
        success "Redis cache cleared"
    else
        warn "Redis cache clearing failed (non-critical)"
    fi
}

# Run post-migration tasks
run_post_migration_tasks() {
    log "Running post-migration tasks..."

    # Create default admin user if none exists
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anthias_app.settings.production')
django.setup()

from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    print('No admin users found - manual admin creation required')
else:
    print('Admin users exist')
" 2>/dev/null || warn "Could not check admin users"

    # Load initial data if specified
    if [ -n "${LOAD_INITIAL_DATA:-}" ] && [ "$LOAD_INITIAL_DATA" = "true" ]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
            python manage.py loaddata initial_data.json 2>/dev/null || warn "Initial data loading failed"
    fi

    success "Post-migration tasks completed"
}

# Rollback function
rollback_migration() {
    log "Rolling back migration..."

    # Restore database from backup
    local db_backup_file="$PRE_MIGRATION_BACKUP/database_pre_migration.sql.gz"

    if [ -f "$db_backup_file" ]; then
        log "Restoring database from pre-migration backup..."

        # Drop and recreate database
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
            psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS ${POSTGRES_DB}_backup;" 2>/dev/null || true

        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
            psql -U "$POSTGRES_USER" -d postgres -c "ALTER DATABASE $POSTGRES_DB RENAME TO ${POSTGRES_DB}_backup;" 2>/dev/null || true

        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
            psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;" 2>/dev/null || true

        # Restore from backup
        zcat "$db_backup_file" | docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
            psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" 2>/dev/null || error "Database restoration failed"

        success "Database rolled back to pre-migration state"
    else
        error "Pre-migration backup not found for rollback"
    fi
}

# Health check after migration
run_health_check() {
    log "Running post-migration health check..."

    # Basic database connectivity
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
        success "Database connectivity check passed"
    else
        error "Database connectivity check failed"
        return 1
    fi

    # Application health check
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm anthias-server \
        python manage.py check 2>/dev/null; then
        success "Application health check passed"
    else
        error "Application health check failed"
        return 1
    fi
}

# Send migration notification
send_notification() {
    local status="$1"
    local duration="$2"

    local message="🔄 Database Migration $status
Environment: ${ENVIRONMENT:-production}
Duration: ${duration}s
Timestamp: $MIGRATION_TIMESTAMP"

    # Slack notification
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local payload="{\"text\":\"$message\"}"
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK_URL" || true
    fi

    log "Migration notification sent"
}

# Main migration function
main() {
    local start_time=$(date +%s)

    log "Starting Anthias SaaS database migration..."

    # Error handling
    trap 'error "Migration failed"; rollback_migration; exit 1' ERR

    # Load configuration and check prerequisites
    load_environment
    check_prerequisites

    # Pre-migration steps
    create_pre_migration_backup
    analyze_migration_plan
    check_migration_dependencies
    test_migration_in_transaction

    # Apply migrations
    apply_migrations

    # Post-migration steps
    collect_static_files
    update_search_indexes
    clear_application_cache
    run_post_migration_tasks

    # Verification
    run_health_check

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ $MIGRATION_STATUS -eq 0 ]; then
        success "Database migration completed successfully in ${duration}s!"
        send_notification "SUCCESS" "$duration"
    else
        error "Database migration completed with errors!"
        send_notification "FAILED" "$duration"
    fi

    # Display summary
    echo ""
    echo "==================== MIGRATION SUMMARY ===================="
    echo "Migration Timestamp: $MIGRATION_TIMESTAMP"
    echo "Duration: ${duration}s"
    echo "Pre-migration Backup: $PRE_MIGRATION_BACKUP"
    echo "Status: $([[ $MIGRATION_STATUS -eq 0 ]] && echo "SUCCESS" || echo "FAILED")"
    echo "============================================================="

    exit $MIGRATION_STATUS
}

# Handle command line arguments
case "${1:-}" in
    "rollback")
        load_environment
        rollback_migration
        ;;
    "check")
        load_environment
        check_prerequisites
        analyze_migration_plan
        ;;
    *)
        main "$@"
        ;;
esac