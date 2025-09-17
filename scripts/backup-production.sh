#!/bin/bash

# Anthias SaaS Production Backup Script
# Automated backup of database, media files, and configurations

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.production.yml"
BACKUP_DIR="$PROJECT_ROOT/data/backups"
LOG_FILE="$PROJECT_ROOT/logs/backup.log"

# Default configuration
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
DB_BACKUP_COMPRESSION=${DB_BACKUP_COMPRESSION:-gzip}
ENABLE_CLOUD_BACKUP=${ENABLE_CLOUD_BACKUP:-false}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Backup variables
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$BACKUP_TIMESTAMP"
BACKUP_STATUS=0

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    BACKUP_STATUS=1
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
        warn "Environment file not found: $ENV_FILE"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking backup prerequisites..."

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

    # Create backup directory
    mkdir -p "$BACKUP_PATH" "$PROJECT_ROOT/logs"

    # Check available disk space (require at least 5GB free)
    local available_space=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    local required_space=5242880  # 5GB in KB

    if [ "$available_space" -lt "$required_space" ]; then
        error "Insufficient disk space for backup. Available: ${available_space}KB, Required: ${required_space}KB"
        exit 1
    fi

    success "Prerequisites check completed"
}

# Backup PostgreSQL database
backup_database() {
    log "Starting database backup..."

    local db_backup_file="$BACKUP_PATH/database.sql"
    local db_compressed_file="$BACKUP_PATH/database.sql.gz"

    # Create database dump
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --verbose --no-owner --no-privileges > "$db_backup_file" 2>/dev/null; then

        # Compress the backup
        if [ "$DB_BACKUP_COMPRESSION" = "gzip" ]; then
            gzip "$db_backup_file"
            success "Database backup completed and compressed: $db_compressed_file"
        else
            success "Database backup completed: $db_backup_file"
        fi

        # Verify backup integrity
        local backup_size=$(stat -c%s "$db_compressed_file" 2>/dev/null || stat -c%s "$db_backup_file")
        if [ "$backup_size" -gt 1024 ]; then  # At least 1KB
            success "Database backup verification passed (Size: ${backup_size} bytes)"
        else
            error "Database backup verification failed (Size too small: ${backup_size} bytes)"
        fi
    else
        error "Database backup failed"
    fi
}

# Backup media files
backup_media_files() {
    log "Starting media files backup..."

    local media_backup_file="$BACKUP_PATH/media.tar.gz"
    local media_source="$PROJECT_ROOT/data/media"

    if [ -d "$media_source" ]; then
        # Create compressed archive of media files
        if tar -czf "$media_backup_file" -C "$(dirname "$media_source")" "$(basename "$media_source")" --exclude="*.tmp" --exclude="*.log" --exclude="*.cache" 2>/dev/null; then
            success "Media files backup completed: $media_backup_file"

            # Verify media backup
            local media_size=$(stat -c%s "$media_backup_file")
            local file_count=$(tar -tzf "$media_backup_file" | wc -l)
            log "Media backup contains $file_count files (Size: ${media_size} bytes)"
        else
            warn "Media files backup failed or directory is empty"
        fi
    else
        warn "Media directory not found: $media_source"
    fi
}

# Backup static files
backup_static_files() {
    log "Starting static files backup..."

    local static_backup_file="$BACKUP_PATH/static.tar.gz"
    local static_source="$PROJECT_ROOT/data/static"

    if [ -d "$static_source" ]; then
        if tar -czf "$static_backup_file" -C "$(dirname "$static_source")" "$(basename "$static_source")" 2>/dev/null; then
            success "Static files backup completed: $static_backup_file"
        else
            warn "Static files backup failed"
        fi
    else
        warn "Static directory not found: $static_source"
    fi
}

# Backup configuration files
backup_configurations() {
    log "Starting configuration backup..."

    local config_backup_file="$BACKUP_PATH/configurations.tar.gz"

    # Create temporary directory for configurations
    local temp_config_dir=$(mktemp -d)

    # Copy important configuration files
    cp "$ENV_FILE" "$temp_config_dir/environment" 2>/dev/null || warn "Environment file not found"
    cp "$COMPOSE_FILE" "$temp_config_dir/docker-compose.yml" 2>/dev/null || warn "Compose file not found"
    cp -r "$PROJECT_ROOT/config" "$temp_config_dir/" 2>/dev/null || warn "Config directory not found"
    cp -r "$PROJECT_ROOT/scripts" "$temp_config_dir/" 2>/dev/null || warn "Scripts directory not found"

    # Backup SSL certificates if they exist
    if [ -d "$PROJECT_ROOT/data/ssl" ]; then
        cp -r "$PROJECT_ROOT/data/ssl" "$temp_config_dir/" 2>/dev/null || warn "SSL directory backup failed"
    fi

    # Create archive
    if tar -czf "$config_backup_file" -C "$temp_config_dir" . 2>/dev/null; then
        success "Configuration backup completed: $config_backup_file"
    else
        warn "Configuration backup failed"
    fi

    # Cleanup
    rm -rf "$temp_config_dir"
}

# Backup Docker volumes
backup_docker_volumes() {
    log "Starting Docker volumes backup..."

    local volumes_backup_file="$BACKUP_PATH/docker_volumes.tar.gz"

    # Get list of volumes used by the application
    local volumes=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config --volumes 2>/dev/null || echo "")

    if [ -n "$volumes" ]; then
        # Create temporary directory for volume data
        local temp_volumes_dir=$(mktemp -d)

        # Backup each volume
        while IFS= read -r volume; do
            if [ -n "$volume" ]; then
                log "Backing up volume: $volume"
                docker run --rm -v "$volume:/volume" -v "$temp_volumes_dir:/backup" alpine \
                    tar -czf "/backup/$volume.tar.gz" -C /volume . 2>/dev/null || warn "Failed to backup volume: $volume"
            fi
        done <<< "$volumes"

        # Create combined archive
        if tar -czf "$volumes_backup_file" -C "$temp_volumes_dir" . 2>/dev/null; then
            success "Docker volumes backup completed: $volumes_backup_file"
        else
            warn "Docker volumes backup failed"
        fi

        # Cleanup
        rm -rf "$temp_volumes_dir"
    else
        warn "No Docker volumes found to backup"
    fi
}

# Create backup metadata
create_backup_metadata() {
    log "Creating backup metadata..."

    local metadata_file="$BACKUP_PATH/backup_metadata.json"

    cat > "$metadata_file" << EOF
{
    "backup_timestamp": "$BACKUP_TIMESTAMP",
    "backup_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "hostname": "$(hostname)",
    "environment": "${ENVIRONMENT:-production}",
    "database": {
        "type": "postgresql",
        "host": "${POSTGRES_HOST:-postgres}",
        "database": "${POSTGRES_DB:-anthias_production}",
        "user": "${POSTGRES_USER:-anthias}"
    },
    "application": {
        "version": "${APP_VERSION:-1.0.0}",
        "git_hash": "${GIT_HASH:-unknown}",
        "git_branch": "${GIT_BRANCH:-main}"
    },
    "backup_components": {
        "database": true,
        "media_files": true,
        "static_files": true,
        "configurations": true,
        "docker_volumes": true
    },
    "backup_size": "$(du -sh "$BACKUP_PATH" | cut -f1)",
    "retention_days": $BACKUP_RETENTION_DAYS
}
EOF

    success "Backup metadata created: $metadata_file"
}

# Upload to cloud storage (optional)
upload_to_cloud() {
    if [ "$ENABLE_CLOUD_BACKUP" = "true" ] && [ -n "${AWS_STORAGE_BUCKET_NAME:-}" ]; then
        log "Starting cloud backup upload..."

        # Check if AWS CLI is available
        if command -v aws &> /dev/null; then
            local s3_path="s3://$AWS_STORAGE_BUCKET_NAME/backups/$(basename "$BACKUP_PATH")"

            # Upload backup directory to S3
            if aws s3 sync "$BACKUP_PATH" "$s3_path" --delete --storage-class STANDARD_IA; then
                success "Backup uploaded to cloud storage: $s3_path"

                # Set lifecycle policy for automatic deletion
                aws s3api put-object-lifecycle-configuration \
                    --bucket "$AWS_STORAGE_BUCKET_NAME" \
                    --lifecycle-configuration file://<(cat << EOF
{
    "Rules": [
        {
            "ID": "BackupRetentionRule",
            "Status": "Enabled",
            "Filter": {"Prefix": "backups/"},
            "Expiration": {"Days": $BACKUP_RETENTION_DAYS}
        }
    ]
}
EOF
) 2>/dev/null || warn "Failed to set S3 lifecycle policy"
            else
                error "Failed to upload backup to cloud storage"
            fi
        else
            warn "AWS CLI not available for cloud backup"
        fi
    else
        log "Cloud backup disabled or not configured"
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."

    # Remove local backups older than retention period
    find "$BACKUP_DIR" -type d -name "20*" -mtime +$BACKUP_RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true

    # Count remaining backups
    local backup_count=$(find "$BACKUP_DIR" -type d -name "20*" | wc -l)
    log "Local backups remaining: $backup_count"

    success "Old backup cleanup completed"
}

# Verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."

    local verification_failed=false

    # Verify database backup
    local db_file="$BACKUP_PATH/database.sql.gz"
    if [ -f "$db_file" ]; then
        if gzip -t "$db_file" 2>/dev/null; then
            success "Database backup integrity verified"
        else
            error "Database backup integrity check failed"
            verification_failed=true
        fi
    fi

    # Verify media backup
    local media_file="$BACKUP_PATH/media.tar.gz"
    if [ -f "$media_file" ]; then
        if tar -tzf "$media_file" >/dev/null 2>&1; then
            success "Media backup integrity verified"
        else
            error "Media backup integrity check failed"
            verification_failed=true
        fi
    fi

    # Verify static backup
    local static_file="$BACKUP_PATH/static.tar.gz"
    if [ -f "$static_file" ]; then
        if tar -tzf "$static_file" >/dev/null 2>&1; then
            success "Static backup integrity verified"
        else
            error "Static backup integrity check failed"
            verification_failed=true
        fi
    fi

    if [ "$verification_failed" = "true" ]; then
        error "Backup verification failed"
        BACKUP_STATUS=1
    else
        success "All backup verifications passed"
    fi
}

# Send backup notification
send_notification() {
    local status="$1"
    local backup_size=$(du -sh "$BACKUP_PATH" | cut -f1)

    local message="📦 Production Backup $status
Timestamp: $BACKUP_TIMESTAMP
Size: $backup_size
Location: $BACKUP_PATH"

    # Slack notification
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local payload="{\"text\":\"$message\"}"
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK_URL" || true
    fi

    # Email notification
    if command -v mail &> /dev/null && [ -n "${ADMIN_EMAIL:-}" ]; then
        echo "$message" | mail -s "Anthias SaaS Backup $status" "$ADMIN_EMAIL" || true
    fi

    log "Backup notification sent"
}

# Main backup function
main() {
    log "Starting Anthias SaaS production backup..."

    # Load configuration and check prerequisites
    load_environment
    check_prerequisites

    # Perform backup operations
    backup_database
    backup_media_files
    backup_static_files
    backup_configurations
    backup_docker_volumes
    create_backup_metadata

    # Verify backup integrity
    verify_backup

    # Upload to cloud if enabled
    upload_to_cloud

    # Cleanup old backups
    cleanup_old_backups

    # Send notification
    if [ $BACKUP_STATUS -eq 0 ]; then
        success "Production backup completed successfully!"
        send_notification "SUCCESS"
    else
        error "Production backup completed with errors!"
        send_notification "FAILED"
    fi

    # Display summary
    echo ""
    echo "==================== BACKUP SUMMARY ===================="
    echo "Backup Timestamp: $BACKUP_TIMESTAMP"
    echo "Backup Location: $BACKUP_PATH"
    echo "Backup Size: $(du -sh "$BACKUP_PATH" | cut -f1)"
    echo "Status: $([[ $BACKUP_STATUS -eq 0 ]] && echo "SUCCESS" || echo "FAILED")"
    echo "Files:"
    ls -la "$BACKUP_PATH" 2>/dev/null || echo "Backup directory not accessible"
    echo "=========================================================="

    exit $BACKUP_STATUS
}

# Script execution
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi