#!/bin/bash

# Anthias SaaS Production Health Check Script
# Comprehensive system health monitoring

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.production.yml"
LOG_FILE="$PROJECT_ROOT/logs/health-check.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health check results
HEALTH_STATUS=0
FAILED_CHECKS=()

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    HEALTH_STATUS=1
    FAILED_CHECKS+=("$1")
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Load environment if exists
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

# Container health checks
check_container_health() {
    log "Checking container health status..."

    local containers=(
        "signate-postgres"
        "signate-redis"
        "signate-server"
        "signate-websocket"
        "signate-celery"
        "signate-nginx"
        "signate-frontend"
    )

    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
            local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-health-check")

            case "$health_status" in
                "healthy")
                    success "Container $container is healthy"
                    ;;
                "unhealthy")
                    error "Container $container is unhealthy"
                    ;;
                "starting")
                    warn "Container $container is starting"
                    ;;
                "no-health-check")
                    warn "Container $container has no health check configured"
                    ;;
                *)
                    error "Container $container has unknown health status: $health_status"
                    ;;
            esac
        else
            error "Container $container is not running"
        fi
    done
}

# Service endpoint checks
check_service_endpoints() {
    log "Checking service endpoints..."

    # Main application health endpoint
    if curl -f -s "http://localhost/health" > /dev/null; then
        success "Main application health endpoint is responding"
    else
        error "Main application health endpoint is not responding"
    fi

    # API endpoint check
    if curl -f -s "http://localhost/api/v1/health" > /dev/null; then
        success "API health endpoint is responding"
    else
        error "API health endpoint is not responding"
    fi

    # Frontend health check
    if curl -f -s "http://localhost:3000/api/health" > /dev/null; then
        success "Frontend health endpoint is responding"
    else
        warn "Frontend health endpoint is not responding"
    fi

    # WebSocket connection check
    if nc -z localhost 9001; then
        success "WebSocket service is accepting connections"
    else
        error "WebSocket service is not accepting connections"
    fi
}

# Database connectivity and performance
check_database_health() {
    log "Checking database health..."

    # Basic connectivity
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        pg_isready -U postgres -d signate_production > /dev/null 2>&1; then
        success "Database is accepting connections"
    else
        error "Database is not accepting connections"
        return
    fi

    # Connection count check
    local connection_count=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        psql -U postgres -d signate_production -t -c "SELECT count(*) FROM pg_stat_activity;" | tr -d ' \n\r')

    if [ "$connection_count" -gt 150 ]; then
        warn "High database connection count: $connection_count"
    else
        success "Database connection count is normal: $connection_count"
    fi

    # Database size check
    local db_size=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        psql -U postgres -d signate_production -t -c "SELECT pg_size_pretty(pg_database_size('signate_production'));" | tr -d ' \n\r')

    log "Database size: $db_size"

    # Check for long-running queries
    local long_queries=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        psql -U postgres -d signate_production -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '5 minutes';" | tr -d ' \n\r')

    if [ "$long_queries" -gt 0 ]; then
        warn "Found $long_queries long-running queries (>5 minutes)"
    else
        success "No long-running queries detected"
    fi
}

# Redis health and performance
check_redis_health() {
    log "Checking Redis health..."

    # Basic connectivity
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        success "Redis is responding to ping"
    else
        error "Redis is not responding to ping"
        return
    fi

    # Memory usage check
    local memory_info=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis \
        redis-cli info memory | grep "used_memory_human")
    log "Redis memory usage: $memory_info"

    # Connected clients check
    local connected_clients=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis \
        redis-cli info clients | grep "connected_clients" | cut -d: -f2 | tr -d '\r\n')

    if [ "$connected_clients" -gt 100 ]; then
        warn "High Redis client count: $connected_clients"
    else
        success "Redis client count is normal: $connected_clients"
    fi

    # Key count check
    local key_count=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis \
        redis-cli dbsize | tr -d '\r\n')
    log "Redis key count: $key_count"
}

# Celery worker health
check_celery_health() {
    log "Checking Celery worker health..."

    # Check if workers are active
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T anthias-celery \
        celery -A anthias_app inspect active > /dev/null 2>&1; then
        success "Celery workers are active"
    else
        error "Celery workers are not responding"
        return
    fi

    # Check worker stats
    local worker_stats=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T anthias-celery \
        celery -A anthias_app inspect stats 2>/dev/null | grep -c "OK" || echo "0")

    if [ "$worker_stats" -gt 0 ]; then
        success "Celery worker stats available: $worker_stats workers"
    else
        warn "Could not retrieve Celery worker stats"
    fi

    # Check queue length
    local queue_length=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis \
        redis-cli llen celery 2>/dev/null | tr -d '\r\n' || echo "0")

    if [ "$queue_length" -gt 100 ]; then
        warn "High Celery queue length: $queue_length tasks"
    else
        success "Celery queue length is normal: $queue_length tasks"
    fi
}

# System resource checks
check_system_resources() {
    log "Checking system resources..."

    # Disk space check
    local disk_usage=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        error "Critical disk space usage: ${disk_usage}%"
    elif [ "$disk_usage" -gt 80 ]; then
        warn "High disk space usage: ${disk_usage}%"
    else
        success "Disk space usage is normal: ${disk_usage}%"
    fi

    # Memory usage check
    local memory_usage=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        error "Critical memory usage: ${memory_usage}%"
    elif (( $(echo "$memory_usage > 80" | bc -l) )); then
        warn "High memory usage: ${memory_usage}%"
    else
        success "Memory usage is normal: ${memory_usage}%"
    fi

    # Load average check
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    local cpu_cores=$(nproc)

    if (( $(echo "$load_avg > $cpu_cores * 2" | bc -l) )); then
        error "High system load: $load_avg (cores: $cpu_cores)"
    elif (( $(echo "$load_avg > $cpu_cores" | bc -l) )); then
        warn "Elevated system load: $load_avg (cores: $cpu_cores)"
    else
        success "System load is normal: $load_avg (cores: $cpu_cores)"
    fi
}

# SSL certificate checks
check_ssl_certificates() {
    log "Checking SSL certificate status..."

    if [ -n "${SERVER_NAME:-}" ]; then
        # Check certificate expiration
        local cert_expiry=$(echo | openssl s_client -servername "$SERVER_NAME" -connect "$SERVER_NAME:443" 2>/dev/null | \
            openssl x509 -noout -dates | grep "notAfter" | cut -d= -f2)

        if [ -n "$cert_expiry" ]; then
            local expiry_timestamp=$(date -d "$cert_expiry" +%s)
            local current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))

            if [ "$days_until_expiry" -lt 7 ]; then
                error "SSL certificate expires in $days_until_expiry days"
            elif [ "$days_until_expiry" -lt 30 ]; then
                warn "SSL certificate expires in $days_until_expiry days"
            else
                success "SSL certificate is valid for $days_until_expiry more days"
            fi
        else
            warn "Could not check SSL certificate expiration"
        fi
    else
        warn "SERVER_NAME not set, skipping SSL certificate check"
    fi
}

# Application-specific checks
check_application_metrics() {
    log "Checking application-specific metrics..."

    # Check recent error logs
    local error_count=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs --since="1h" anthias-server 2>&1 | \
        grep -i "error\|exception\|critical" | wc -l)

    if [ "$error_count" -gt 10 ]; then
        warn "High error count in last hour: $error_count errors"
    else
        success "Error count in last hour is normal: $error_count errors"
    fi

    # Check if migrations are up to date
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T anthias-server \
        python manage.py showmigrations --plan | grep -q "\[ \]"; then
        warn "Unapplied migrations detected"
    else
        success "All migrations are applied"
    fi

    # Check admin user exists
    local admin_count=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T anthias-server \
        python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).count())" 2>/dev/null | tail -1)

    if [ "$admin_count" -gt 0 ]; then
        success "Admin users exist: $admin_count"
    else
        warn "No admin users found"
    fi
}

# Generate health report
generate_health_report() {
    log "Generating health report..."

    local report_file="$PROJECT_ROOT/logs/health-report-$(date +%Y%m%d_%H%M%S).json"

    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "overall_status": "$([[ $HEALTH_STATUS -eq 0 ]] && echo "healthy" || echo "unhealthy")",
    "failed_checks": $(printf '%s\n' "${FAILED_CHECKS[@]}" | jq -R . | jq -s .),
    "system_info": {
        "hostname": "$(hostname)",
        "uptime": "$(uptime -p)",
        "docker_version": "$(docker --version)",
        "compose_version": "$(docker-compose --version)"
    }
}
EOF

    log "Health report saved to: $report_file"
}

# Send alerts if unhealthy
send_alerts() {
    if [ $HEALTH_STATUS -ne 0 ]; then
        local alert_message="🚨 Production Health Check FAILED\n\nFailed checks:\n$(printf '%s\n' "${FAILED_CHECKS[@]}")"

        # Slack notification
        if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
            local payload="{\"text\":\"$alert_message\"}"
            curl -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK_URL" || true
        fi

        # Email notification (if configured)
        if command -v mail &> /dev/null && [ -n "${ADMIN_EMAIL:-}" ]; then
            echo -e "$alert_message" | mail -s "Anthias SaaS Health Check Alert" "$ADMIN_EMAIL" || true
        fi

        log "Alert notifications sent"
    fi
}

# Main health check function
main() {
    log "Starting comprehensive health check..."

    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"

    # Run all health checks
    check_container_health
    check_service_endpoints
    check_database_health
    check_redis_health
    check_celery_health
    check_system_resources
    check_ssl_certificates
    check_application_metrics

    # Generate report and send alerts
    generate_health_report
    send_alerts

    # Final status
    if [ $HEALTH_STATUS -eq 0 ]; then
        success "All health checks passed ✅"
    else
        error "Health check failed with ${#FAILED_CHECKS[@]} failed checks ❌"
        echo "Failed checks:"
        printf ' - %s\n' "${FAILED_CHECKS[@]}"
    fi

    exit $HEALTH_STATUS
}

# Script execution
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi