#!/bin/bash

# Test Runner Script for Signate SaaS Platform
# Comprehensive testing automation with coverage reporting

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
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test configuration
TEST_COMPOSE_FILE="docker-compose.test.yml"
TEST_PROJECT_NAME="signate-test"
COVERAGE_THRESHOLD=${COVERAGE_THRESHOLD:-80}
PYTEST_WORKERS=${PYTEST_WORKERS:-auto}

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

log_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

# Check if Docker is available and running
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi

    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
}

# Clean up test environment
cleanup_test_env() {
    log_info "Cleaning up test environment..."

    cd "$DOCKER_DIR"

    # Stop and remove test containers
    docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" down -v --remove-orphans 2>/dev/null || true

    # Remove test volumes
    docker volume rm "${TEST_PROJECT_NAME}_postgres-test-data" 2>/dev/null || true
    docker volume rm "${TEST_PROJECT_NAME}_test-data" 2>/dev/null || true
    docker volume rm "${TEST_PROJECT_NAME}_test-cache" 2>/dev/null || true

    # Clean up test result directories
    rm -rf "$DOCKER_DIR/data/coverage-test"/*
    rm -rf "$DOCKER_DIR/data/test-results-junit"/*

    log_success "Test environment cleaned up"
}

# Setup test environment
setup_test_env() {
    log_info "Setting up test environment..."

    cd "$DOCKER_DIR"

    # Create necessary directories
    mkdir -p data/coverage-test
    mkdir -p data/test-results-junit

    # Build test services
    log_info "Building test containers..."
    docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" build --parallel

    # Start test infrastructure
    log_info "Starting test infrastructure..."
    docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" up -d postgres-test redis-test

    # Wait for databases to be ready
    log_info "Waiting for test databases to be ready..."
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T postgres-test pg_isready -U signate_test -d signate_test >/dev/null 2>&1; then
            break
        fi
        retries=$((retries - 1))
        sleep 2
    done

    if [ $retries -eq 0 ]; then
        log_error "Test database failed to start"
        cleanup_test_env
        exit 1
    fi

    # Start test application
    log_info "Starting test application..."
    docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" up -d anthias-test

    # Wait for test application to be ready
    sleep 10

    log_success "Test environment ready"
}

# Run database migrations for tests
run_test_migrations() {
    log_info "Running test database migrations..."

    cd "$DOCKER_DIR"

    # Run migrations
    if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test python manage.py migrate --noinput; then
        log_success "Test migrations completed"
    else
        log_error "Test migrations failed"
        return 1
    fi
}

# Run unit tests
run_unit_tests() {
    log_test "Running unit tests..."

    cd "$DOCKER_DIR"

    local test_cmd="python -m pytest tests/unit/ -v --tb=short --strict-markers --strict-config"

    if [ "$PYTEST_WORKERS" != "1" ]; then
        test_cmd="$test_cmd -n $PYTEST_WORKERS"
    fi

    test_cmd="$test_cmd --junitxml=/usr/src/app/test-results/unit-tests.xml"
    test_cmd="$test_cmd --cov=anthias_app --cov-branch --cov-report=html:/usr/src/app/htmlcov/unit"
    test_cmd="$test_cmd --cov-report=xml:/usr/src/app/test-results/unit-coverage.xml"
    test_cmd="$test_cmd --cov-report=term-missing"

    if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test bash -c "$test_cmd"; then
        log_success "Unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    log_test "Running integration tests..."

    cd "$DOCKER_DIR"

    # Start Celery for integration tests
    docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" up -d anthias-celery-test

    local test_cmd="python -m pytest tests/integration/ -v --tb=short --strict-markers --strict-config"

    if [ "$PYTEST_WORKERS" != "1" ]; then
        test_cmd="$test_cmd -n $PYTEST_WORKERS"
    fi

    test_cmd="$test_cmd --junitxml=/usr/src/app/test-results/integration-tests.xml"
    test_cmd="$test_cmd --cov=anthias_app --cov-branch --cov-report=html:/usr/src/app/htmlcov/integration"
    test_cmd="$test_cmd --cov-report=xml:/usr/src/app/test-results/integration-coverage.xml"
    test_cmd="$test_cmd --cov-report=term-missing"

    if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test bash -c "$test_cmd"; then
        log_success "Integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Run end-to-end tests
run_e2e_tests() {
    log_test "Running end-to-end tests..."

    cd "$DOCKER_DIR"

    # Start Selenium grid
    docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" up -d selenium-hub selenium-chrome selenium-firefox

    # Wait for Selenium to be ready
    log_info "Waiting for Selenium Grid to be ready..."
    sleep 15

    local test_cmd="python -m pytest tests/e2e/ -v --tb=short --strict-markers --strict-config"
    test_cmd="$test_cmd --junitxml=/usr/src/app/test-results/e2e-tests.xml"
    test_cmd="$test_cmd --html=/usr/src/app/test-results/e2e-report.html --self-contained-html"

    if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test bash -c "$test_cmd"; then
        log_success "End-to-end tests passed"
        return 0
    else
        log_error "End-to-end tests failed"
        return 1
    fi
}

# Run linting and code quality checks
run_code_quality() {
    log_test "Running code quality checks..."

    cd "$DOCKER_DIR"

    local quality_passed=true

    # Run flake8
    log_info "Running flake8..."
    if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test flake8 anthias_app/ --output-file=/usr/src/app/test-results/flake8.txt; then
        log_success "flake8 passed"
    else
        log_warning "flake8 found issues"
        quality_passed=false
    fi

    # Run black
    log_info "Running black..."
    if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test black --check anthias_app/; then
        log_success "black formatting check passed"
    else
        log_warning "black formatting issues found"
        quality_passed=false
    fi

    # Run isort
    log_info "Running isort..."
    if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test isort --check-only anthias_app/; then
        log_success "isort import sorting check passed"
    else
        log_warning "isort import sorting issues found"
        quality_passed=false
    fi

    # Run mypy
    log_info "Running mypy..."
    if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test mypy anthias_app/ --html-report /usr/src/app/test-results/mypy; then
        log_success "mypy type checking passed"
    else
        log_warning "mypy type checking issues found"
        quality_passed=false
    fi

    # Run bandit security checks
    log_info "Running bandit security scan..."
    if docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test bandit -r anthias_app/ -f json -o /usr/src/app/test-results/bandit.json; then
        log_success "bandit security scan passed"
    else
        log_warning "bandit security issues found"
        quality_passed=false
    fi

    if [ "$quality_passed" = true ]; then
        log_success "All code quality checks passed"
        return 0
    else
        log_warning "Some code quality checks failed"
        return 1
    fi
}

# Generate coverage report
generate_coverage_report() {
    log_info "Generating comprehensive coverage report..."

    cd "$DOCKER_DIR"

    # Combine coverage data
    docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test bash -c "
        cd /usr/src/app
        coverage combine
        coverage html -d htmlcov/combined
        coverage xml -o test-results/combined-coverage.xml
        coverage report --show-missing > test-results/coverage-summary.txt
    "

    # Check coverage threshold
    local coverage_percentage
    coverage_percentage=$(docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" exec -T anthias-test coverage report --show-missing | grep TOTAL | awk '{print $4}' | sed 's/%//')

    if [ -n "$coverage_percentage" ]; then
        log_info "Total coverage: ${coverage_percentage}%"

        if [ "${coverage_percentage%.*}" -ge "$COVERAGE_THRESHOLD" ]; then
            log_success "Coverage threshold ($COVERAGE_THRESHOLD%) met"
        else
            log_warning "Coverage threshold ($COVERAGE_THRESHOLD%) not met"
            return 1
        fi
    else
        log_warning "Could not determine coverage percentage"
    fi

    log_success "Coverage report generated"
}

# Start test report server
start_report_server() {
    log_info "Starting test report server..."

    cd "$DOCKER_DIR"

    docker-compose -f "$TEST_COMPOSE_FILE" -p "$TEST_PROJECT_NAME" up -d test-reports

    log_success "Test report server started at http://localhost:8090"
}

# Copy test results to host
copy_test_results() {
    log_info "Copying test results to host..."

    # Create timestamped results directory
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local results_dir="$PROJECT_ROOT/test-results-$timestamp"
    mkdir -p "$results_dir"

    # Copy from Docker volumes
    cp -r "$DOCKER_DIR/data/coverage-test/"* "$results_dir/" 2>/dev/null || true
    cp -r "$DOCKER_DIR/data/test-results-junit/"* "$results_dir/" 2>/dev/null || true

    log_success "Test results copied to: $results_dir"
}

# Initialize coordination hooks
init_test_hooks() {
    log_info "Initializing test coordination hooks..."

    if command -v npx >/dev/null 2>&1; then
        cd "$PROJECT_ROOT"
        npx claude-flow@alpha hooks post-edit --file "scripts/test-runner.sh" --memory-key "phase1/devops/testing" || log_warning "Coordination hook failed (non-critical)"
        npx claude-flow@alpha hooks notify --message "Testing infrastructure configured and executed" || log_warning "Coordination notification failed (non-critical)"
    fi
}

# Display test summary
show_test_summary() {
    echo
    echo "🧪 Test Execution Summary"
    echo "========================="
    echo
    echo "Test Results:"

    if [ -f "$DOCKER_DIR/data/test-results-junit/unit-tests.xml" ]; then
        echo "  ✅ Unit Tests: Results available"
    else
        echo "  ❌ Unit Tests: No results found"
    fi

    if [ -f "$DOCKER_DIR/data/test-results-junit/integration-tests.xml" ]; then
        echo "  ✅ Integration Tests: Results available"
    else
        echo "  ❌ Integration Tests: No results found"
    fi

    if [ -f "$DOCKER_DIR/data/test-results-junit/e2e-tests.xml" ]; then
        echo "  ✅ End-to-End Tests: Results available"
    else
        echo "  ❌ End-to-End Tests: No results found"
    fi

    echo
    echo "Coverage Reports:"
    echo "  📊 Combined Report: http://localhost:8090/coverage/combined/"
    echo "  📊 Unit Coverage: http://localhost:8090/coverage/unit/"
    echo "  📊 Integration Coverage: http://localhost:8090/coverage/integration/"
    echo
    echo "Additional Reports:"
    echo "  🔍 Code Quality: http://localhost:8090/results/"
    echo "  🛡️ Security Scan: http://localhost:8090/results/bandit.json"
    echo
    echo "Useful Commands:"
    echo "  📋 View test logs: docker-compose -f docker/docker-compose.test.yml -p signate-test logs anthias-test"
    echo "  🔄 Rerun tests: $0 --quick"
    echo "  🧹 Clean up: $0 --cleanup"
    echo
}

# Print usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Test Runner for Signate SaaS Platform"
    echo
    echo "Options:"
    echo "  --unit              Run only unit tests"
    echo "  --integration       Run only integration tests"
    echo "  --e2e               Run only end-to-end tests"
    echo "  --quality           Run only code quality checks"
    echo "  --coverage          Generate only coverage reports"
    echo "  --quick             Run unit and integration tests only"
    echo "  --all               Run all tests and checks (default)"
    echo "  --no-cleanup        Don't clean up test environment after running"
    echo "  --cleanup           Clean up test environment and exit"
    echo "  --report-server     Start only the test report server"
    echo "  --help              Show this help message"
    echo
    echo "Environment Variables:"
    echo "  COVERAGE_THRESHOLD  Minimum coverage percentage (default: 80)"
    echo "  PYTEST_WORKERS     Number of parallel workers (default: auto)"
    echo
}

# Main execution function
main() {
    echo "🧪 Signate SaaS Platform - Test Runner"
    echo "======================================"
    echo

    # Parse command line arguments
    local run_unit=false
    local run_integration=false
    local run_e2e=false
    local run_quality=false
    local run_coverage=false
    local cleanup_after=true
    local cleanup_only=false
    local report_server_only=false
    local run_all=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit)
                run_unit=true
                run_all=false
                shift
                ;;
            --integration)
                run_integration=true
                run_all=false
                shift
                ;;
            --e2e)
                run_e2e=true
                run_all=false
                shift
                ;;
            --quality)
                run_quality=true
                run_all=false
                shift
                ;;
            --coverage)
                run_coverage=true
                run_all=false
                shift
                ;;
            --quick)
                run_unit=true
                run_integration=true
                run_all=false
                shift
                ;;
            --all)
                run_all=true
                shift
                ;;
            --no-cleanup)
                cleanup_after=false
                shift
                ;;
            --cleanup)
                cleanup_only=true
                shift
                ;;
            --report-server)
                report_server_only=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Check prerequisites
    check_docker

    # Handle cleanup only
    if [ "$cleanup_only" = true ]; then
        cleanup_test_env
        exit 0
    fi

    # Handle report server only
    if [ "$report_server_only" = true ]; then
        start_report_server
        exit 0
    fi

    # Initialize coordination
    init_test_hooks

    # Set up test environment
    cleanup_test_env
    setup_test_env
    run_test_migrations

    # Track test results
    local tests_passed=true

    # Run selected tests
    if [ "$run_all" = true ] || [ "$run_unit" = true ]; then
        if ! run_unit_tests; then
            tests_passed=false
        fi
    fi

    if [ "$run_all" = true ] || [ "$run_integration" = true ]; then
        if ! run_integration_tests; then
            tests_passed=false
        fi
    fi

    if [ "$run_all" = true ] || [ "$run_e2e" = true ]; then
        if ! run_e2e_tests; then
            tests_passed=false
        fi
    fi

    if [ "$run_all" = true ] || [ "$run_quality" = true ]; then
        if ! run_code_quality; then
            tests_passed=false
        fi
    fi

    if [ "$run_all" = true ] || [ "$run_coverage" = true ]; then
        if ! generate_coverage_report; then
            tests_passed=false
        fi
    fi

    # Start report server
    start_report_server

    # Copy results to host
    copy_test_results

    # Show summary
    show_test_summary

    # Clean up if requested
    if [ "$cleanup_after" = true ]; then
        log_info "Test environment will remain running for report viewing"
        log_info "Run '$0 --cleanup' when you're done viewing reports"
    fi

    # Exit with appropriate code
    if [ "$tests_passed" = true ]; then
        log_success "All tests passed successfully!"
        exit 0
    else
        log_error "Some tests failed. Check the reports for details."
        exit 1
    fi
}

# Run main function with all arguments
main "$@"