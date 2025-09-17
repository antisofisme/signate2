#!/bin/bash

# PostgreSQL Backup Script for Anthias SaaS Platform
# Automated database backup with compression and retention management

set -euo pipefail

# Configuration
BACKUP_DIR="/var/lib/postgresql/backups"
RETENTION_DAYS=30
POSTGRES_DB=${POSTGRES_DB:-anthias_production}
POSTGRES_USER=${POSTGRES_USER:-anthias}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
BACKUP_FILE="$BACKUP_DIR/postgres_backup_$(date +%Y%m%d_%H%M%S).sql"

# Create database backup
pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --verbose \
    --no-owner \
    --no-privileges \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_FILE"

# Verify backup was created
if [ -f "$BACKUP_FILE" ]; then
    echo "Backup created successfully: $BACKUP_FILE"

    # Check backup file size
    BACKUP_SIZE=$(stat -c%s "$BACKUP_FILE")
    if [ "$BACKUP_SIZE" -gt 1024 ]; then
        echo "Backup size: $BACKUP_SIZE bytes"
    else
        echo "Warning: Backup file seems too small ($BACKUP_SIZE bytes)"
        exit 1
    fi
else
    echo "Error: Backup file was not created"
    exit 1
fi

# Clean up old backups
find "$BACKUP_DIR" -name "postgres_backup_*.sql" -mtime +$RETENTION_DAYS -delete

# Log backup completion
echo "PostgreSQL backup completed at $(date)"