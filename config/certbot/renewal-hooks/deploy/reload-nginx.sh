#!/bin/bash

# Certbot SSL Certificate Renewal Hook
# Automatically reload Nginx when certificates are renewed

set -euo pipefail

# Configuration
COMPOSE_FILE="/opt/signate/docker/docker-compose.production.yml"
ENV_FILE="/opt/signate/.env.production"
LOG_FILE="/opt/signate/logs/ssl-renewal.log"

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
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Main function
main() {
    log "SSL certificate renewal hook triggered"

    # Check if this is a renewal (not initial issuance)
    if [ -n "${RENEWED_DOMAINS:-}" ]; then
        log "Certificates renewed for domains: $RENEWED_DOMAINS"

        # Verify certificate files exist
        if [ -f "${RENEWED_LINEAGE}/fullchain.pem" ] && [ -f "${RENEWED_LINEAGE}/privkey.pem" ]; then
            success "Certificate files verified"

            # Copy certificates to the correct location for Docker
            if [ -d "/opt/signate/data/ssl/certs" ]; then
                cp "${RENEWED_LINEAGE}/fullchain.pem" "/opt/signate/data/ssl/certs/"
                cp "${RENEWED_LINEAGE}/privkey.pem" "/opt/signate/data/ssl/private/"
                cp "${RENEWED_LINEAGE}/chain.pem" "/opt/signate/data/ssl/certs/"

                # Set proper permissions
                chmod 644 "/opt/signate/data/ssl/certs/fullchain.pem"
                chmod 644 "/opt/signate/data/ssl/certs/chain.pem"
                chmod 600 "/opt/signate/data/ssl/private/privkey.pem"

                success "Certificate files copied to Docker volumes"
            fi

            # Reload Nginx in Docker container
            if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec anthias-nginx nginx -t; then
                if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec anthias-nginx nginx -s reload; then
                    success "Nginx reloaded successfully"
                else
                    error "Failed to reload Nginx"
                    exit 1
                fi
            else
                error "Nginx configuration test failed"
                exit 1
            fi

            # Test HTTPS connectivity
            local domain=$(echo "$RENEWED_DOMAINS" | cut -d' ' -f1)
            if curl -f -s "https://$domain/health" > /dev/null; then
                success "HTTPS connectivity test passed for $domain"
            else
                warn "HTTPS connectivity test failed for $domain"
            fi

            # Send notification
            send_notification "SUCCESS" "$RENEWED_DOMAINS"

        else
            error "Certificate files not found after renewal"
            exit 1
        fi
    else
        warn "No renewed domains specified"
    fi
}

# Send renewal notification
send_notification() {
    local status="$1"
    local domains="$2"

    local message="🔒 SSL Certificate Renewal $status
Domains: $domains
Renewal Time: $(date)"

    # Slack notification
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local payload="{\"text\":\"$message\"}"
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK_URL" || true
    fi

    log "SSL renewal notification sent"
}

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Execute main function
main "$@"