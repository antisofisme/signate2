#!/bin/bash

# Anthias SaaS SSL Certificate Setup Script
# Automated Let's Encrypt SSL certificate provisioning and management

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.production.yml"
SSL_DIR="$PROJECT_ROOT/data/ssl"
LOG_FILE="$PROJECT_ROOT/logs/ssl-setup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# SSL setup variables
SSL_EMAIL=""
SSL_DOMAINS=""
STAGING=${STAGING:-false}

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

# Display usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Setup SSL certificates for Anthias SaaS Platform

OPTIONS:
    -e, --email EMAIL       Email address for Let's Encrypt notifications
    -d, --domains DOMAINS   Comma-separated list of domains
    -s, --staging          Use Let's Encrypt staging environment
    --renew                Renew existing certificates
    --revoke               Revoke existing certificates
    -h, --help             Display this help message

EXAMPLES:
    $0 -e admin@example.com -d "example.com,www.example.com"
    $0 --renew
    $0 --staging -e test@example.com -d "staging.example.com"

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--email)
                SSL_EMAIL="$2"
                shift 2
                ;;
            -d|--domains)
                SSL_DOMAINS="$2"
                shift 2
                ;;
            -s|--staging)
                STAGING=true
                shift
                ;;
            --renew)
                ACTION="renew"
                shift
                ;;
            --revoke)
                ACTION="revoke"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
}

# Load environment variables
load_environment() {
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        log "Environment variables loaded from $ENV_FILE"

        # Use environment variables if not provided via command line
        SSL_EMAIL=${SSL_EMAIL:-${SSL_EMAIL_ENV:-}}
        SSL_DOMAINS=${SSL_DOMAINS:-${SSL_DOMAINS_ENV:-}}
    else
        warn "Environment file not found: $ENV_FILE"
    fi
}

# Validate input parameters
validate_parameters() {
    if [ -z "$SSL_EMAIL" ]; then
        error "Email address is required. Use -e option or set SSL_EMAIL in environment"
    fi

    if [ -z "$SSL_DOMAINS" ]; then
        error "Domains are required. Use -d option or set SSL_DOMAINS in environment"
    fi

    # Validate email format
    if ! echo "$SSL_EMAIL" | grep -qE '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'; then
        error "Invalid email address format: $SSL_EMAIL"
    fi

    # Validate domain format
    IFS=',' read -ra DOMAIN_ARRAY <<< "$SSL_DOMAINS"
    for domain in "${DOMAIN_ARRAY[@]}"; do
        domain=$(echo "$domain" | xargs)  # Trim whitespace
        if ! echo "$domain" | grep -qE '^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$'; then
            error "Invalid domain format: $domain"
        fi
    done

    success "Parameter validation completed"
}

# Check prerequisites
check_prerequisites() {
    log "Checking SSL setup prerequisites..."

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running or not accessible"
    fi

    # Check if ports 80 and 443 are available
    if netstat -tuln | grep -q ":80 "; then
        log "Port 80 is in use (expected for web server)"
    fi

    if netstat -tuln | grep -q ":443 "; then
        log "Port 443 is in use (expected for HTTPS)"
    fi

    # Create SSL directories
    mkdir -p "$SSL_DIR/certs" "$SSL_DIR/private" "$(dirname "$LOG_FILE")"

    # Set proper permissions
    chmod 755 "$SSL_DIR"
    chmod 755 "$SSL_DIR/certs"
    chmod 700 "$SSL_DIR/private"

    success "Prerequisites check completed"
}

# Generate DH parameters
generate_dhparams() {
    local dhparam_file="$SSL_DIR/certs/dhparam.pem"

    if [ ! -f "$dhparam_file" ]; then
        log "Generating Diffie-Hellman parameters (this may take a while)..."
        openssl dhparam -out "$dhparam_file" 2048
        chmod 644 "$dhparam_file"
        success "DH parameters generated"
    else
        log "DH parameters already exist"
    fi
}

# Setup Nginx for ACME challenge
setup_nginx_acme() {
    log "Setting up Nginx for ACME challenge..."

    # Create ACME challenge directory
    mkdir -p "$PROJECT_ROOT/data/certbot"

    # Create temporary Nginx configuration for ACME challenge
    cat > "$PROJECT_ROOT/config/nginx/acme.conf" << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name _;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        try_files $uri =404;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
EOF

    # Start Nginx with ACME configuration
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d anthias-nginx

    success "Nginx configured for ACME challenge"
}

# Obtain SSL certificates
obtain_certificates() {
    log "Obtaining SSL certificates from Let's Encrypt..."

    local certbot_args=""
    if [ "$STAGING" = "true" ]; then
        certbot_args="--staging"
        warn "Using Let's Encrypt staging environment"
    fi

    # Convert comma-separated domains to -d arguments
    local domain_args=""
    IFS=',' read -ra DOMAIN_ARRAY <<< "$SSL_DOMAINS"
    for domain in "${DOMAIN_ARRAY[@]}"; do
        domain=$(echo "$domain" | xargs)  # Trim whitespace
        domain_args="$domain_args -d $domain"
    done

    # Run Certbot to obtain certificates
    docker run --rm --name certbot \
        -v "$SSL_DIR/certs:/etc/letsencrypt" \
        -v "$SSL_DIR/private:/etc/letsencrypt" \
        -v "$PROJECT_ROOT/data/certbot:/var/www/certbot" \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$SSL_EMAIL" \
        --agree-tos \
        --no-eff-email \
        $certbot_args \
        $domain_args

    if [ $? -eq 0 ]; then
        success "SSL certificates obtained successfully"
        copy_certificates
    else
        error "Failed to obtain SSL certificates"
    fi
}

# Copy certificates to the correct locations
copy_certificates() {
    log "Copying certificates to correct locations..."

    local primary_domain=$(echo "$SSL_DOMAINS" | cut -d',' -f1 | xargs)
    local cert_dir="$SSL_DIR/certs/live/$primary_domain"

    if [ -d "$cert_dir" ]; then
        # Copy certificates to nginx-accessible locations
        cp "$cert_dir/fullchain.pem" "$SSL_DIR/certs/"
        cp "$cert_dir/privkey.pem" "$SSL_DIR/private/"
        cp "$cert_dir/chain.pem" "$SSL_DIR/certs/"

        # Set proper permissions
        chmod 644 "$SSL_DIR/certs/fullchain.pem"
        chmod 644 "$SSL_DIR/certs/chain.pem"
        chmod 600 "$SSL_DIR/private/privkey.pem"

        success "Certificates copied successfully"
    else
        error "Certificate directory not found: $cert_dir"
    fi
}

# Configure SSL in Nginx
configure_nginx_ssl() {
    log "Configuring Nginx for SSL..."

    # Update Nginx configuration to use SSL
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec anthias-nginx nginx -t

    if [ $? -eq 0 ]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec anthias-nginx nginx -s reload
        success "Nginx SSL configuration applied"
    else
        error "Nginx SSL configuration test failed"
    fi
}

# Test SSL configuration
test_ssl_configuration() {
    log "Testing SSL configuration..."

    local primary_domain=$(echo "$SSL_DOMAINS" | cut -d',' -f1 | xargs)

    # Wait for SSL to be ready
    sleep 10

    # Test HTTPS connectivity
    if curl -f -s "https://$primary_domain/health" > /dev/null; then
        success "HTTPS connectivity test passed"
    else
        warn "HTTPS connectivity test failed - this may be normal during initial setup"
    fi

    # Test SSL certificate
    local cert_info=$(echo | openssl s_client -servername "$primary_domain" -connect "$primary_domain:443" 2>/dev/null | openssl x509 -noout -dates)

    if [ -n "$cert_info" ]; then
        log "SSL certificate information:"
        echo "$cert_info" | tee -a "$LOG_FILE"
        success "SSL certificate test passed"
    else
        warn "Could not retrieve SSL certificate information"
    fi
}

# Setup automatic renewal
setup_auto_renewal() {
    log "Setting up automatic SSL certificate renewal..."

    # Create renewal script
    cat > "$PROJECT_ROOT/scripts/renew-ssl.sh" << 'EOF'
#!/bin/bash
# Automatic SSL certificate renewal script

set -euo pipefail

LOG_FILE="/opt/signate/logs/ssl-renewal.log"
COMPOSE_FILE="/opt/signate/docker/docker-compose.production.yml"
ENV_FILE="/opt/signate/.env.production"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting SSL certificate renewal check..."

# Run Certbot renewal
docker run --rm --name certbot-renew \
    -v "/opt/signate/data/ssl/certs:/etc/letsencrypt" \
    -v "/opt/signate/data/ssl/private:/etc/letsencrypt" \
    -v "/opt/signate/data/certbot:/var/www/certbot" \
    certbot/certbot renew \
    --webroot \
    --webroot-path=/var/www/certbot \
    --quiet

if [ $? -eq 0 ]; then
    log "Certificate renewal check completed"

    # Reload Nginx if certificates were renewed
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec anthias-nginx nginx -t; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec anthias-nginx nginx -s reload
        log "Nginx reloaded after certificate renewal"
    fi
else
    log "Certificate renewal failed"
    exit 1
fi
EOF

    chmod +x "$PROJECT_ROOT/scripts/renew-ssl.sh"

    # Create systemd timer (if systemd is available)
    if command -v systemctl &> /dev/null; then
        create_systemd_timer
    else
        # Create cron job as fallback
        create_cron_job
    fi

    success "Automatic renewal setup completed"
}

# Create systemd timer for renewal
create_systemd_timer() {
    log "Creating systemd timer for SSL renewal..."

    # Create service file
    sudo tee /etc/systemd/system/anthias-ssl-renewal.service > /dev/null << EOF
[Unit]
Description=Anthias SSL Certificate Renewal
After=network.target

[Service]
Type=oneshot
ExecStart=$PROJECT_ROOT/scripts/renew-ssl.sh
User=root
EOF

    # Create timer file
    sudo tee /etc/systemd/system/anthias-ssl-renewal.timer > /dev/null << EOF
[Unit]
Description=Run Anthias SSL renewal twice daily
Requires=anthias-ssl-renewal.service

[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Enable and start timer
    sudo systemctl daemon-reload
    sudo systemctl enable anthias-ssl-renewal.timer
    sudo systemctl start anthias-ssl-renewal.timer

    success "Systemd timer created and enabled"
}

# Create cron job for renewal
create_cron_job() {
    log "Creating cron job for SSL renewal..."

    # Add cron job to run twice daily
    (crontab -l 2>/dev/null || echo "") | grep -v "anthias-ssl-renewal" | \
    { cat; echo "0 0,12 * * * $PROJECT_ROOT/scripts/renew-ssl.sh"; } | crontab -

    success "Cron job created for SSL renewal"
}

# Renew existing certificates
renew_certificates() {
    log "Renewing SSL certificates..."

    docker run --rm --name certbot-renew \
        -v "$SSL_DIR/certs:/etc/letsencrypt" \
        -v "$SSL_DIR/private:/etc/letsencrypt" \
        -v "$PROJECT_ROOT/data/certbot:/var/www/certbot" \
        certbot/certbot renew \
        --webroot \
        --webroot-path=/var/www/certbot \
        --force-renewal

    if [ $? -eq 0 ]; then
        success "SSL certificates renewed successfully"
        copy_certificates
        configure_nginx_ssl
        test_ssl_configuration
    else
        error "SSL certificate renewal failed"
    fi
}

# Revoke existing certificates
revoke_certificates() {
    log "Revoking SSL certificates..."

    local primary_domain=$(echo "$SSL_DOMAINS" | cut -d',' -f1 | xargs)

    docker run --rm --name certbot-revoke \
        -v "$SSL_DIR/certs:/etc/letsencrypt" \
        -v "$SSL_DIR/private:/etc/letsencrypt" \
        certbot/certbot revoke \
        --cert-path "/etc/letsencrypt/live/$primary_domain/cert.pem"

    if [ $? -eq 0 ]; then
        success "SSL certificates revoked successfully"
    else
        error "SSL certificate revocation failed"
    fi
}

# Send SSL setup notification
send_notification() {
    local status="$1"

    local message="🔒 SSL Certificate Setup $status
Domains: $SSL_DOMAINS
Email: $SSL_EMAIL
Staging: $STAGING"

    # Slack notification
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local payload="{\"text\":\"$message\"}"
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK_URL" || true
    fi

    log "SSL setup notification sent"
}

# Main SSL setup function
main() {
    log "Starting Anthias SaaS SSL certificate setup..."

    # Load environment and validate parameters
    load_environment
    validate_parameters
    check_prerequisites

    # Execute action based on parameters
    case "${ACTION:-setup}" in
        "renew")
            renew_certificates
            ;;
        "revoke")
            revoke_certificates
            ;;
        *)
            # Full SSL setup
            generate_dhparams
            setup_nginx_acme
            obtain_certificates
            configure_nginx_ssl
            test_ssl_configuration
            setup_auto_renewal

            success "SSL certificate setup completed successfully!"
            send_notification "SUCCESS"
            ;;
    esac

    # Display summary
    echo ""
    echo "==================== SSL SETUP SUMMARY ===================="
    echo "Email: $SSL_EMAIL"
    echo "Domains: $SSL_DOMAINS"
    echo "Staging: $STAGING"
    echo "SSL Directory: $SSL_DIR"
    echo "Action: ${ACTION:-setup}"
    echo "============================================================="
}

# Parse arguments and execute
ACTION="setup"
parse_arguments "$@"
main