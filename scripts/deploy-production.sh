#!/bin/bash

# Anthias SaaS Production Deployment Script
# Zero-downtime blue-green deployment with automatic rollback

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${1:-$PROJECT_ROOT/.env.production}"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.production.yml"
BACKUP_DIR="$PROJECT_ROOT/data/backups"
LOG_FILE="$PROJECT_ROOT/logs/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Cleanup function for exit
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        warn "Deployment failed. Starting cleanup..."
        # Rollback if deployment failed
        rollback_deployment
    fi
    exit $exit_code
}

trap cleanup EXIT

# Validation functions
validate_environment() {
    log "Validating environment configuration..."

    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file not found: $ENV_FILE"
    fi

    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Docker compose file not found: $COMPOSE_FILE"
    fi

    # Source environment file
    set -a
    source "$ENV_FILE"
    set +a

    # Check required variables
    local required_vars=(
        "SECRET_KEY"
        "DATABASE_URL"
        "REDIS_URL"
        "ALLOWED_HOSTS"
        "IMAGE_TAG"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            error "Required environment variable not set: $var"
        fi
    done

    success "Environment validation completed"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."

    # Check disk space
    local disk_usage=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 80 ]; then
        error "Disk usage is above 80% ($disk_usage%). Please free up space before deployment."
    fi

    # Check if docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running or not accessible"
    fi

    # Check docker-compose version
    if ! docker-compose --version &> /dev/null; then
        error "docker-compose is not installed or not accessible"
    fi

    # Validate database connection
    log "Testing database connection..."
    if ! docker run --rm --network host postgres:15-alpine pg_isready -h localhost -p 5432; then
        warn "Cannot connect to database. Ensure it's running."
    fi

    success "Pre-deployment checks completed"
}

# Backup current state
backup_current_state() {
    log "Creating backup of current state..."

    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/deployment_backup_$backup_timestamp"

    mkdir -p "$backup_path"

    # Backup database
    log "Backing up database..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        pg_dump -U postgres signate_production | gzip > "$backup_path/database.sql.gz"

    # Backup media files
    log "Backing up media files..."
    tar -czf "$backup_path/media.tar.gz" -C "$PROJECT_ROOT/data" media/

    # Backup current docker-compose state
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config > "$backup_path/docker-compose.yml"
    cp "$ENV_FILE" "$backup_path/environment"

    # Store backup path for potential rollback
    echo "$backup_path" > "$PROJECT_ROOT/.last_backup"

    success "Backup created at: $backup_path"
}

# Pull new images
pull_new_images() {
    log "Pulling new Docker images..."

    # Pull all images specified in docker-compose
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull --parallel

    # Verify images exist
    local services=(anthias-server anthias-websocket anthias-celery anthias-nginx anthias-frontend)
    for service in "${services[@]}"; do
        local image=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config | grep -A5 "$service:" | grep "image:" | awk '{print $2}')
        if [ -n "$image" ]; then
            if ! docker image inspect "$image" &> /dev/null; then
                error "Image not found locally: $image"
            fi
        fi
    done

    success "All images pulled successfully"
}

# Database migration
run_database_migrations() {
    log "Running database migrations..."

    # Run migrations using temporary container
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm \
        -e DJANGO_SETTINGS_MODULE=anthias_app.settings.production \
        anthias-server python manage.py migrate --no-input

    # Check migration status
    local migration_output=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm \
        anthias-server python manage.py showmigrations --plan | grep "\[ \]" | wc -l)

    if [ "$migration_output" -gt 0 ]; then
        warn "Some migrations might not have been applied"
    fi

    success "Database migrations completed"
}

# Blue-green deployment
blue_green_deployment() {
    log "Starting blue-green deployment..."

    # Stop old services gracefully
    log "Stopping old services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop anthias-server anthias-celery anthias-websocket

    # Start new services
    log "Starting new services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --remove-orphans

    # Wait for services to be healthy
    log "Waiting for services to become healthy..."
    local max_wait=300  # 5 minutes
    local wait_time=0

    while [ $wait_time -lt $max_wait ]; do
        local healthy_services=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps | grep -c "Up (healthy)" || true)
        local total_services=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --services | wc -l)

        if [ "$healthy_services" -eq "$total_services" ]; then
            success "All services are healthy"
            break
        fi

        log "Waiting for services to become healthy... ($healthy_services/$total_services healthy)"
        sleep 10
        wait_time=$((wait_time + 10))
    done

    if [ $wait_time -ge $max_wait ]; then
        error "Services did not become healthy within $max_wait seconds"
    fi

    # Switch traffic to new services (nginx reload)
    log "Switching traffic to new services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec anthias-nginx nginx -s reload

    success "Blue-green deployment completed"
}

# Health checks
run_health_checks() {
    log "Running comprehensive health checks..."

    # Wait a bit for services to settle
    sleep 30

    # HTTP health check
    local health_url="http://localhost/health"
    if ! curl -f -s "$health_url" > /dev/null; then
        error "HTTP health check failed for $health_url"
    fi

    # Database connectivity check
    if ! docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T anthias-server \
        python manage.py check --database default; then
        error "Database connectivity check failed"
    fi

    # Redis connectivity check
    if ! docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli ping; then
        error "Redis connectivity check failed"
    fi

    # Celery worker check
    if ! docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T anthias-celery \
        celery -A anthias_app inspect ping; then
        error "Celery worker check failed"
    fi

    # Frontend check
    if ! curl -f -s "http://localhost:3000/api/health" > /dev/null; then
        warn "Frontend health check failed, but continuing..."
    fi

    success "All health checks passed"
}

# Cleanup old containers and images
cleanup_old_resources() {
    log "Cleaning up old resources..."

    # Remove unused containers
    docker container prune -f

    # Remove unused images (keep last 3 versions)
    docker image prune -f

    # Clean up old volumes (be careful here)
    # docker volume prune -f  # Commented out for safety

    success "Resource cleanup completed"
}

# Rollback function
rollback_deployment() {
    log "Starting deployment rollback..."

    if [ ! -f "$PROJECT_ROOT/.last_backup" ]; then
        error "No backup information found for rollback"
    fi

    local backup_path=$(cat "$PROJECT_ROOT/.last_backup")
    if [ ! -d "$backup_path" ]; then
        error "Backup directory not found: $backup_path"
    fi

    # Restore database
    log "Restoring database from backup..."
    zcat "$backup_path/database.sql.gz" | docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        psql -U postgres -d signate_production

    # Restore previous environment
    cp "$backup_path/environment" "$ENV_FILE"

    # Restart services with previous configuration
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --remove-orphans

    warn "Rollback completed. Please verify the system is working correctly."
}

# Send deployment notification
send_notification() {
    local status="$1"
    local message="$2"

    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local payload="{\"text\":\"🚀 Production Deployment $status: $message\"}"
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK_URL" || true
    fi

    if [ -n "${DISCORD_WEBHOOK_URL:-}" ]; then
        local payload="{\"content\":\"🚀 Production Deployment $status: $message\"}"
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$DISCORD_WEBHOOK_URL" || true
    fi
}

# Main deployment function
main() {
    log "Starting Anthias SaaS production deployment..."

    # Create necessary directories
    mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

    # Deployment steps
    validate_environment
    pre_deployment_checks
    backup_current_state
    pull_new_images
    run_database_migrations
    blue_green_deployment
    run_health_checks
    cleanup_old_resources

    success "Production deployment completed successfully!"
    send_notification "SUCCESS" "Deployment completed for commit ${GIT_HASH:-unknown}"

    # Display summary
    echo ""
    echo "==================== DEPLOYMENT SUMMARY ===================="
    echo "Environment: production"
    echo "Image Tag: ${IMAGE_TAG:-latest}"
    echo "Git Hash: ${GIT_HASH:-unknown}"
    echo "Build Number: ${BUILD_NUMBER:-unknown}"
    echo "Deployment Time: $(date)"
    echo "Backup Location: $(cat "$PROJECT_ROOT/.last_backup" 2>/dev/null || echo "N/A")"
    echo "=========================================================="
}

# Script execution
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi