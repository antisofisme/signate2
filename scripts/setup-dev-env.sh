#!/bin/bash

# Enhanced Development Environment Setup Script for Signate SaaS Platform
# This script sets up the complete development environment with PostgreSQL, Redis, and testing tools

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing_deps=()

    if ! command_exists docker; then
        missing_deps+=("docker")
    fi

    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi

    if ! command_exists git; then
        missing_deps+=("git")
    fi

    if ! command_exists curl; then
        missing_deps+=("curl")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Please install the missing dependencies and run this script again."
        exit 1
    fi

    # Check Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    log_success "All prerequisites are satisfied"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."

    local dirs=(
        "$DOCKER_DIR/data"
        "$DOCKER_DIR/data/postgres"
        "$DOCKER_DIR/data/redis-dev"
        "$DOCKER_DIR/data/anthias-dev"
        "$DOCKER_DIR/data/static-dev"
        "$DOCKER_DIR/data/media-dev"
        "$DOCKER_DIR/data/coverage"
        "$DOCKER_DIR/data/test-results"
        "$DOCKER_DIR/data/coverage-test"
        "$DOCKER_DIR/data/test-results-junit"
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/tmp"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    done

    # Set proper permissions
    chmod -R 755 "$DOCKER_DIR/data"

    log_success "Directory structure created"
}

# Create configuration files
create_config_files() {
    log_info "Creating configuration files..."

    # Redis development configuration
    cat > "$DOCKER_DIR/redis-dev.conf" << 'EOF'
# Redis Development Configuration
# Enhanced settings for development environment

# Basic Configuration
port 6379
bind 0.0.0.0
protected-mode no
timeout 300
tcp-keepalive 60

# Memory Management
maxmemory 512mb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence (for development data retention)
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

# Append Only File
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Logging
loglevel notice
logfile ""
syslog-enabled no

# Client Output Buffer Limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Advanced Config
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
EOF

    # Nginx test reports configuration
    cat > "$DOCKER_DIR/nginx-test-reports.conf" << 'EOF'
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }

    location /coverage/ {
        alias /usr/share/nginx/html/coverage/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }

    location /results/ {
        alias /usr/share/nginx/html/results/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

    # PostgreSQL test schemas
    cat > "$DOCKER_DIR/postgres-test-schemas.sql" << 'EOF'
-- Test-specific database initialization
-- This file is loaded after the main init script for test databases

-- Create test-specific extensions if not already present
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS test_shared;
CREATE SCHEMA IF NOT EXISTS test_tenant1;
CREATE SCHEMA IF NOT EXISTS test_tenant2;

-- Grant permissions
GRANT USAGE ON SCHEMA test_shared TO CURRENT_USER;
GRANT CREATE ON SCHEMA test_shared TO CURRENT_USER;
GRANT USAGE ON SCHEMA test_tenant1 TO CURRENT_USER;
GRANT CREATE ON SCHEMA test_tenant1 TO CURRENT_USER;
GRANT USAGE ON SCHEMA test_tenant2 TO CURRENT_USER;
GRANT CREATE ON SCHEMA test_tenant2 TO CURRENT_USER;

-- Create test data fixtures
INSERT INTO shared.tenants (schema_name, name, subdomain) VALUES
    ('test_tenant1', 'Test Tenant 1', 'test1'),
    ('test_tenant2', 'Test Tenant 2', 'test2')
ON CONFLICT (subdomain) DO NOTHING;
EOF

    log_success "Configuration files created"
}

# Set up environment file
setup_environment() {
    log_info "Setting up environment configuration..."

    local env_file="$DOCKER_DIR/.env.dev"

    # Check if .env.dev already exists
    if [ -f "$env_file" ]; then
        log_warning ".env.dev already exists. Creating backup..."
        cp "$env_file" "$env_file.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Copy from example or create new
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$env_file"
        log_info "Copied .env.example to .env.dev"
    else
        # Create minimal .env.dev
        cat > "$env_file" << 'EOF'
# Signate Development Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Database
POSTGRES_DB=signate_dev
POSTGRES_USER=signate
POSTGRES_PASSWORD=signate_dev_password
POSTGRES_TEST_DB=signate_test
POSTGRES_TEST_USER=signate_test
POSTGRES_TEST_PASSWORD=signate_test_password

# Redis
REDIS_MAX_MEMORY=512mb
REDIS_PORT=6379

# Application
SECRET_KEY=signate-development-secret-key-never-use-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,signate-server-dev,*.localhost

# Ports
NGINX_PORT=8000
SERVER_DEV_PORT=9000
POSTGRES_PORT=5432

# Celery
CELERY_WORKER_CONCURRENCY=2
CELERY_LOG_LEVEL=INFO

# Testing
PYTEST_WORKERS=auto
TEST_PARALLEL=true
COVERAGE_THRESHOLD=80

# Network
FRONTEND_SUBNET=172.20.0.0/16
BACKEND_SUBNET=172.21.0.0/16
EOF
        log_info "Created new .env.dev file"
    fi

    log_success "Environment configuration ready"
}

# Initialize hooks and coordination
init_coordination() {
    log_info "Initializing coordination hooks..."

    # Check if claude-flow is available
    if command_exists npx; then
        log_info "Setting up Claude Flow coordination..."

        # Run coordination hook
        cd "$PROJECT_ROOT"
        npx claude-flow@alpha hooks post-edit --file "docker/docker-compose.dev.yml" --memory-key "phase1/devops/docker-dev" || log_warning "Claude Flow hook failed (non-critical)"
        npx claude-flow@alpha hooks notify --message "DevOps development environment configured" || log_warning "Claude Flow notification failed (non-critical)"

        log_success "Coordination hooks initialized"
    else
        log_warning "npx not available, skipping coordination hooks"
    fi
}

# Build and start development environment
start_development() {
    log_info "Building and starting development environment..."

    cd "$DOCKER_DIR"

    # Use the development environment file
    export COMPOSE_FILE="docker-compose.dev.yml"
    export COMPOSE_PROJECT_NAME="signate-dev"

    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f docker-compose.dev.yml pull || log_warning "Some images could not be pulled"

    # Build services
    log_info "Building development services..."
    docker-compose -f docker-compose.dev.yml build --parallel

    # Start core services first
    log_info "Starting core services (PostgreSQL, Redis)..."
    docker-compose -f docker-compose.dev.yml up -d postgres redis-dev

    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    sleep 10

    # Start application services
    log_info "Starting application services..."
    docker-compose -f docker-compose.dev.yml up -d

    # Wait for services to start
    log_info "Waiting for services to start..."
    sleep 15

    log_success "Development environment started"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."

    cd "$DOCKER_DIR"

    # Check service health
    local services=("postgres" "redis-dev" "anthias-server-dev")

    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.dev.yml ps "$service" | grep -q "Up"; then
            log_success "$service is running"
        else
            log_error "$service is not running properly"
        fi
    done

    # Check if PostgreSQL is accessible
    if docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U signate -d signate_dev >/dev/null 2>&1; then
        log_success "PostgreSQL is accessible"
    else
        log_warning "PostgreSQL connection test failed"
    fi

    # Check if Redis is accessible
    if docker-compose -f docker-compose.dev.yml exec -T redis-dev redis-cli ping >/dev/null 2>&1; then
        log_success "Redis is accessible"
    else
        log_warning "Redis connection test failed"
    fi

    log_success "Installation verification completed"
}

# Display usage information
show_usage_info() {
    log_info "Development environment setup completed!"
    echo
    echo "🚀 Your Signate development environment is ready!"
    echo
    echo "Services available:"
    echo "  📊 Application: http://localhost:8000"
    echo "  🔧 Development Server: http://localhost:9000"
    echo "  📧 MailHog (Email testing): http://localhost:8025"
    echo "  📈 Test Reports: http://localhost:8090"
    echo
    echo "Database connections:"
    echo "  🐘 PostgreSQL: localhost:5432"
    echo "     - Database: signate_dev"
    echo "     - Username: signate"
    echo "     - Password: signate_dev_password"
    echo
    echo "  📡 Redis: localhost:6379"
    echo
    echo "Useful commands:"
    echo "  📋 View logs: docker-compose -f docker/docker-compose.dev.yml logs -f"
    echo "  🔄 Restart services: docker-compose -f docker/docker-compose.dev.yml restart"
    echo "  🛑 Stop services: docker-compose -f docker/docker-compose.dev.yml down"
    echo "  🧪 Run tests: ./scripts/test-runner.sh"
    echo
    echo "Next steps:"
    echo "  1. Run database migrations: docker-compose -f docker/docker-compose.dev.yml exec anthias-server-dev python manage.py migrate"
    echo "  2. Create a superuser: docker-compose -f docker/docker-compose.dev.yml exec anthias-server-dev python manage.py createsuperuser"
    echo "  3. Load sample data: docker-compose -f docker/docker-compose.dev.yml exec anthias-server-dev python manage.py loaddata fixtures/sample_data.json"
    echo
}

# Main execution
main() {
    echo "🔧 Signate SaaS Platform - Enhanced Development Environment Setup"
    echo "================================================================"
    echo

    # Parse command line arguments
    local force_rebuild=false
    local skip_build=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_rebuild=true
                shift
                ;;
            --skip-build)
                skip_build=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo
                echo "Options:"
                echo "  --force      Force rebuild of all containers"
                echo "  --skip-build Skip building and start existing containers"
                echo "  --help       Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Execute setup steps
    check_prerequisites
    create_directories
    create_config_files
    setup_environment
    init_coordination

    if [ "$skip_build" = false ]; then
        start_development
        verify_installation
    fi

    show_usage_info

    log_success "Development environment setup completed successfully!"
}

# Run main function with all arguments
main "$@"