#!/bin/bash

# Signate (Anthias) Digital Signage Platform - Deployment Script
# Production-ready deployment with comprehensive configuration
# Usage: ./deploy.sh [option]
# Options: start, stop, restart, logs, status, clean

set -e  # Exit on any error

# Configuration
COMPOSE_FILE="docker/docker-compose.yml"
ENV_FILE="docker/.env"
PROJECT_NAME="signate"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Change to root directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

log_info "Signate Digital Signage Platform Deployment"
log_info "Project root: $PROJECT_ROOT"

# Create data directories
create_directories() {
    log_info "Creating data directories..."
    mkdir -p data/anthias data/redis data/static data/media
    chmod 755 data/anthias data/redis data/static data/media
    log_success "Data directories created"
}

# Start services
start_services() {
    log_info "Starting Signate services..."
    create_directories

    # Load environment variables
    if [ -f "$ENV_FILE" ]; then
        log_info "Loading environment from $ENV_FILE"
        export $(grep -v '^#' $ENV_FILE | xargs)
    fi

    # Start all services
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d --build

    log_info "Waiting for services to initialize..."
    sleep 15

    # Check if server is ready
    log_info "Checking service health..."
    for i in {1..30}; do
        if docker-compose -f $COMPOSE_FILE exec -T anthias-server curl -f http://localhost:8000/ >/dev/null 2>&1; then
            break
        fi
        log_info "Waiting for server to be ready... ($i/30)"
        sleep 2
    done

    # Install Bootstrap dependency
    log_info "Installing Bootstrap dependency..."
    docker-compose -f $COMPOSE_FILE exec -T anthias-server npm install bootstrap@5.3.3

    # Restart server to rebuild assets
    log_info "Restarting server to rebuild assets..."
    docker-compose -f $COMPOSE_FILE restart anthias-server

    # Wait for webpack build
    log_info "Waiting for webpack build to complete..."
    for i in {1..60}; do
        if docker-compose -f $COMPOSE_FILE logs anthias-server | grep -q "compiled.*successfully"; then
            break
        fi
        log_info "Waiting for webpack build... ($i/60)"
        sleep 2
    done

    log_success "All services started successfully!"
}

# Stop services
stop_services() {
    log_info "Stopping Signate services..."
    docker-compose -f $COMPOSE_FILE down
    log_success "All services stopped"
}

# Restart services
restart_services() {
    log_info "Restarting Signate services..."
    stop_services
    start_services
}

# Show logs
show_logs() {
    docker-compose -f $COMPOSE_FILE logs -f --tail=100
}

# Show status
show_status() {
    log_info "Service Status:"
    docker-compose -f $COMPOSE_FILE ps
    echo ""

    log_info "Health Checks:"
    # Check server health
    if curl -f http://localhost:8000/ >/dev/null 2>&1; then
        log_success "✅ Web server is responding"
    else
        log_error "❌ Web server is not responding"
    fi

    # Check Redis
    if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "✅ Redis is responding"
    else
        log_error "❌ Redis is not responding"
    fi
}

# Clean up
clean_services() {
    log_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleaning up..."
        docker-compose -f $COMPOSE_FILE down -v --remove-orphans
        docker system prune -f
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        start_services
        show_status
        echo ""
        log_success "🌐 Dashboard available at: http://localhost:8000/"
        log_info "📋 Useful commands:"
        log_info "  Stop:     ./docker/deploy.sh stop"
        log_info "  Restart:  ./docker/deploy.sh restart"
        log_info "  Logs:     ./docker/deploy.sh logs"
        log_info "  Status:   ./docker/deploy.sh status"
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        show_status
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    clean)
        clean_services
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services (default)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show service logs"
        echo "  status  - Show service status"
        echo "  clean   - Remove all containers and volumes"
        exit 1
        ;;
esac