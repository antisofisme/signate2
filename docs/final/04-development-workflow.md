# Development Workflow - Enhancement Implementation

## Overview

This document defines the development workflow for implementing the Anthias SaaS enhancement using concurrent agent execution via Claude Code's Task tool, following SPARC methodology for systematic development.

## SPARC-TDD Integration

### Development Flow
```
Specification → Pseudocode → Architecture → Refinement → Completion
     ↓              ↓            ↓            ↓           ↓
   Requirements  Algorithm    System      TDD         Integration
   Analysis      Design       Design   Implementation   & Deploy
```

## Core Workflow Principles

### 1. Concurrent Execution Pattern

**GOLDEN RULE**: "1 MESSAGE = ALL RELATED OPERATIONS"

Every development task MUST follow this concurrent execution pattern:

```javascript
// Single Message - Parallel Agent Execution Pattern
[Phase Implementation Message]:
  // 1. Spawn ALL agents concurrently via Claude Code Task tool
  Task("Database Architect", "Design multi-tenant schema with RLS. Store decisions in memory.", "code-analyzer")
  Task("Backend Developer", "Implement Django models and API endpoints. Use hooks for coordination.", "backend-dev")
  Task("Frontend Developer", "Create React components for admin interface. Coordinate via memory.", "coder")
  Task("Security Engineer", "Implement authentication and RBAC. Document findings in memory.", "security-manager")
  Task("Test Engineer", "Write comprehensive test suite with >90% coverage.", "tester")
  Task("DevOps Engineer", "Setup Docker and CI/CD pipeline. Store configs in memory.", "cicd-engineer")

  // 2. Batch ALL todos in ONE call
  TodoWrite { todos: [...8-12 todos...] }

  // 3. Parallel file operations
  Read "existing-files-to-understand"
  Write "new-files-required"
  MultiEdit "files-needing-updates"

  // 4. Batch ALL bash operations
  Bash "mkdir -p app/{src,tests,docs,config}"
  Bash "pip install -r requirements/requirements.txt"
  Bash "python manage.py makemigrations"
```

### 2. Agent Coordination Protocol

Each agent spawned via Task tool MUST use these coordination hooks:

```bash
# BEFORE starting work
npx claude-flow@alpha hooks pre-task --description "Implementing multi-tenant authentication system"
npx claude-flow@alpha hooks session-restore --session-id "signage-enhancement-session"

# DURING work (after each significant step)
npx claude-flow@alpha hooks post-edit --file "backend/models.py" --memory-key "backend/models/tenant-isolation"
npx claude-flow@alpha hooks notify --message "Completed tenant model with RLS implementation"

# AFTER completing work
npx claude-flow@alpha hooks post-task --task-id "backend-auth-implementation"
npx claude-flow@alpha hooks session-end --export-metrics true
```

## Phase Implementation Examples

### Phase 1: Foundation Setup
```javascript
[Phase 1 Implementation - Single Message]:
  // Analysis Team
  Task("Code Analyzer", `
    TASK: Complete Anthias backend analysis and dependency mapping
    DELIVERABLES:
    - Codebase structure analysis with model relationships
    - API endpoint inventory with versioning documentation
    - Dependency assessment and upgrade recommendations
    - Integration point identification for multi-tenancy

    COORDINATION HOOKS:
    - Store analysis results in memory key 'analysis/codebase'
    - Document API structure in memory key 'analysis/api-inventory'
    - Share upgrade recommendations with DevOps team

    FILES TO CREATE:
    - /docs/analysis/codebase-structure.md
    - /docs/analysis/api-endpoints.md
    - /docs/analysis/dependencies.md
    - /docs/analysis/integration-points.md

    EXECUTION STEPS:
    1. Analyze existing Django models and relationships
    2. Document all API endpoints (v1, v1.1, v1.2, v2)
    3. Assess dependencies for compatibility with multi-tenancy
    4. Identify integration points for tenant isolation
  `, "code-analyzer")

  Task("DevOps Engineer", `
    TASK: Setup enhanced development environment with testing infrastructure
    DELIVERABLES:
    - Docker development environment with PostgreSQL and Redis
    - Testing infrastructure with pytest and coverage reporting
    - CI/CD pipeline foundation with GitHub Actions
    - Environment configuration management

    COORDINATION:
    - Use analysis results from memory key 'analysis/codebase'
    - Store infrastructure configs in memory key 'devops/setup'
    - Coordinate with testing team for CI pipeline integration

    FILES TO CREATE:
    - /docker-compose.dev.yml
    - /docker-compose.test.yml
    - /.github/workflows/test.yml
    - /.github/workflows/build.yml
    - /scripts/setup-dev-env.sh
    - /scripts/run-tests.sh

    EXECUTION STEPS:
    1. Create Docker containers for development services
    2. Setup PostgreSQL with test database
    3. Configure Redis for caching and sessions
    4. Implement CI/CD pipeline with automated testing
  `, "cicd-engineer")

  Task("Quality Engineer", `
    TASK: Establish comprehensive testing framework and quality standards
    DELIVERABLES:
    - Testing strategy with unit, integration, and E2E tests
    - Code quality tools configuration (Black, flake8, mypy)
    - Coverage reporting and quality gates
    - Pre-commit hooks for automated checks

    COORDINATION:
    - Work with DevOps for CI integration
    - Store testing standards in memory key 'testing/standards'
    - Document quality gates for phase completion

    FILES TO CREATE:
    - /tests/conftest.py
    - /tests/fixtures/test_data.py
    - /.pre-commit-config.yaml
    - /pyproject.toml
    - /docs/testing/strategy.md

    EXECUTION STEPS:
    1. Setup pytest with Django integration
    2. Configure code quality tools
    3. Implement coverage reporting
    4. Create pre-commit hooks for quality checks
  `, "tester")

  // ALL todos batched together
  TodoWrite { todos: [
    {content: "Complete Anthias codebase analysis", status: "in_progress", activeForm: "Analyzing Anthias codebase"},
    {content: "Setup Docker development environment", status: "pending", activeForm: "Setting up Docker environment"},
    {content: "Configure PostgreSQL and Redis services", status: "pending", activeForm: "Configuring database services"},
    {content: "Implement CI/CD pipeline with GitHub Actions", status: "pending", activeForm: "Implementing CI/CD pipeline"},
    {content: "Establish testing framework with pytest", status: "pending", activeForm: "Establishing testing framework"},
    {content: "Configure code quality tools", status: "pending", activeForm: "Configuring quality tools"},
    {content: "Create development documentation", status: "pending", activeForm: "Creating development documentation"},
    {content: "Setup pre-commit hooks", status: "pending", activeForm: "Setting up pre-commit hooks"},
    {content: "Validate development environment", status: "pending", activeForm: "Validating environment setup"},
    {content: "Document API endpoint inventory", status: "pending", activeForm: "Documenting API endpoints"}
  ]}

  // Parallel file structure creation
  Bash "mkdir -p {docs/analysis,scripts,tests/{unit,integration,fixtures},.github/workflows}"
```

### Phase 2: Database Migration & Multi-tenancy
```javascript
[Phase 2 Implementation - Single Message]:
  Task("Database Architect", `
    TASK: Design and implement PostgreSQL multi-tenant schema
    DELIVERABLES:
    - Complete PostgreSQL schema with Row-Level Security (RLS)
    - Tenant isolation mechanisms and data partitioning
    - Migration scripts from SQLite to PostgreSQL
    - Performance indexes for multi-tenant queries

    COORDINATION:
    - Use codebase analysis from memory key 'analysis/codebase'
    - Store schema design in memory key 'database/schema'
    - Share migration strategy with backend team

    FILES TO CREATE:
    - /migrations/0001_initial_tenant_schema.sql
    - /migrations/0002_rls_policies.sql
    - /scripts/migrate_sqlite_to_postgresql.py
    - /docs/database/schema-design.md
    - /docs/database/migration-strategy.md

    EXECUTION STEPS:
    1. Design tenant table with proper constraints
    2. Enhance Asset model for multi-tenancy
    3. Implement Row-Level Security policies
    4. Create migration scripts with rollback procedures
  `, "code-analyzer")

  Task("Backend Developer", `
    TASK: Implement Django multi-tenant models and middleware
    DELIVERABLES:
    - Enhanced Django models with tenant relationships
    - Tenant middleware for request isolation
    - Database router for multi-tenant queries
    - API foundation for tenant-aware endpoints

    COORDINATION:
    - Implement schema from memory key 'database/schema'
    - Store implementation details in memory key 'backend/models'
    - Coordinate with security team for isolation verification

    FILES TO CREATE:
    - /backend/models/tenant.py
    - /backend/models/enhanced_asset.py
    - /backend/middleware/tenant_middleware.py
    - /backend/utils/tenant_router.py
    - /backend/api/v3/__init__.py

    EXECUTION STEPS:
    1. Create Tenant and TenantUser models
    2. Enhance Asset model with tenant foreign key
    3. Implement tenant middleware for request context
    4. Create database router for tenant isolation
  `, "backend-dev")

  Task("Security Engineer", `
    TASK: Implement tenant isolation security measures
    DELIVERABLES:
    - Tenant data isolation verification
    - Security policies for multi-tenant access
    - Vulnerability assessment and mitigation
    - Security testing procedures

    COORDINATION:
    - Verify isolation using schema from memory key 'database/schema'
    - Test implementation from memory key 'backend/models'
    - Document security measures in memory key 'security/tenant-isolation'

    FILES TO CREATE:
    - /tests/security/test_tenant_isolation.py
    - /docs/security/tenant-isolation.md
    - /scripts/security_audit.py

    EXECUTION STEPS:
    1. Test tenant data isolation boundaries
    2. Verify RLS policy effectiveness
    3. Assess potential security vulnerabilities
    4. Create security testing procedures
  `, "security-manager")

  Task("Test Engineer", `
    TASK: Create comprehensive tests for multi-tenant functionality
    DELIVERABLES:
    - Unit tests for tenant models and middleware
    - Integration tests for database isolation
    - Performance tests for multi-tenant queries
    - Migration testing procedures

    COORDINATION:
    - Test schema from memory key 'database/schema'
    - Validate backend implementation from memory key 'backend/models'
    - Document test results in memory key 'testing/results'

    FILES TO CREATE:
    - /tests/unit/test_tenant_models.py
    - /tests/integration/test_tenant_isolation.py
    - /tests/performance/test_database_performance.py
    - /tests/migration/test_data_migration.py

    EXECUTION STEPS:
    1. Create unit tests for all tenant-related models
    2. Test database isolation between tenants
    3. Performance test multi-tenant queries
    4. Validate migration procedures
  `, "tester")
```

### Phase 5: Frontend Development
```javascript
[Phase 5 Implementation - Single Message]:
  Task("Frontend Architect", `
    TASK: Design Next.js 14 application architecture
    DELIVERABLES:
    - Next.js 14 application structure with App Router
    - Tenant-aware routing and middleware
    - Component architecture and design system
    - State management strategy

    COORDINATION:
    - Use API contracts from memory key 'api/v3/contracts'
    - Store frontend architecture in memory key 'frontend/architecture'
    - Coordinate with UI/UX for component design

    FILES TO CREATE:
    - /frontend/next.config.js
    - /frontend/middleware.ts
    - /frontend/app/layout.tsx
    - /frontend/components/architecture.md
    - /docs/frontend/architecture.md

    EXECUTION STEPS:
    1. Setup Next.js 14 with App Router
    2. Implement tenant-aware routing middleware
    3. Design component architecture
    4. Plan state management with Zustand
  `, "system-architect")

  Task("UI Developer", `
    TASK: Build core SaaS UI components and layouts
    DELIVERABLES:
    - shadcn/ui component library integration
    - Dashboard layout with sidebar navigation
    - Responsive design system
    - Authentication UI components

    COORDINATION:
    - Use architecture from memory key 'frontend/architecture'
    - Store UI patterns in memory key 'frontend/components'
    - Work with backend team for API integration

    FILES TO CREATE:
    - /frontend/components/ui/ (shadcn/ui components)
    - /frontend/components/layout/Sidebar.tsx
    - /frontend/components/layout/TopBar.tsx
    - /frontend/components/auth/LoginForm.tsx
    - /frontend/app/globals.css

    EXECUTION STEPS:
    1. Install and configure shadcn/ui
    2. Create responsive dashboard layout
    3. Build authentication components
    4. Implement dark/light theme support
  `, "coder")

  Task("Feature Developer", `
    TASK: Implement asset management and tenant features
    DELIVERABLES:
    - Asset management interface with upload
    - Tenant-aware data fetching
    - Real-time updates with WebSocket
    - Mobile-responsive interfaces

    COORDINATION:
    - Use API contracts from memory key 'api/v3/contracts'
    - Implement UI patterns from memory key 'frontend/components'
    - Store feature implementations in memory key 'frontend/features'

    FILES TO CREATE:
    - /frontend/app/[tenant]/assets/page.tsx
    - /frontend/components/assets/AssetGrid.tsx
    - /frontend/components/assets/AssetUpload.tsx
    - /frontend/hooks/useAssets.ts
    - /frontend/lib/api.ts

    EXECUTION STEPS:
    1. Create asset management pages
    2. Implement file upload with progress
    3. Add real-time asset updates
    4. Build mobile-responsive interface
  `, "coder")

  Task("Integration Specialist", `
    TASK: Integrate frontend with backend APIs
    DELIVERABLES:
    - API client with authentication
    - Error handling and validation
    - Loading states and optimistic updates
    - End-to-end feature testing

    COORDINATION:
    - Use API contracts from memory key 'api/v3/contracts'
    - Test integration with backend endpoints
    - Document integration patterns in memory key 'frontend/integration'

    FILES TO CREATE:
    - /frontend/lib/auth.ts
    - /frontend/lib/api-client.ts
    - /frontend/hooks/useAuth.ts
    - /tests/e2e/user-flows.spec.ts

    EXECUTION STEPS:
    1. Implement JWT authentication flow
    2. Create API client with error handling
    3. Add loading states and feedback
    4. Write end-to-end tests
  `, "tester")
```

## Quality Assurance Protocol

### Continuous Quality Checks
```bash
# Pre-commit hooks that run on every commit
pre-commit-hooks:
  - black --check .                    # Code formatting
  - flake8 .                          # Linting
  - mypy .                            # Type checking
  - pytest tests/unit/ --cov=90       # Unit tests with coverage
  - npm run lint                      # Frontend linting
  - npm run type-check                # TypeScript checking

# Integration quality checks
integration-checks:
  - pytest tests/integration/         # Integration tests
  - pytest tests/security/ -m security # Security tests
  - npm run test:e2e                  # End-to-end tests
  - docker-compose build              # Build verification

# Performance benchmarks
performance-checks:
  - pytest tests/performance/ --benchmark-only
  - npm run lighthouse                # Frontend performance
  - k6 run performance/load-test.js   # Load testing
```

### Code Review Process

1. **Automated Checks**: All quality gates must pass before review
2. **Security Review**: Security engineer reviews authentication/payment code
3. **Architecture Review**: System architect reviews major structural changes
4. **Peer Review**: At least 2 team members review each implementation
5. **Integration Testing**: Full test suite passes in CI environment
6. **Performance Validation**: Benchmarks remain within acceptable limits

## Risk Mitigation Workflow

### Phase Risk Assessment
```python
# Risk matrix for each phase
PHASE_RISKS = {
    'phase_1': {'probability': 'low', 'impact': 'medium'},      # Foundation
    'phase_2': {'probability': 'medium', 'impact': 'high'},    # Database migration
    'phase_3': {'probability': 'medium', 'impact': 'high'},    # Authentication
    'phase_5': {'probability': 'medium', 'impact': 'medium'},  # Frontend
    'phase_7': {'probability': 'low', 'impact': 'high'},       # Payment integration
    'phase_8': {'probability': 'medium', 'impact': 'high'},    # Performance
    'phase_10': {'probability': 'high', 'impact': 'critical'}, # Production deployment
}
```

### Rollback Procedures
```bash
# Emergency rollback template for any phase
echo "=== EMERGENCY ROLLBACK PROCEDURE ==="

# Step 1: Stop services
sudo systemctl stop anthias 2>/dev/null || echo "Service not running"
pkill -f "python manage.py runserver" 2>/dev/null

# Step 2: Database rollback
if [ -f "backups/pre_phase_backup.sql" ]; then
    echo "Restoring database backup..."
    psql anthias_db < backups/pre_phase_backup.sql
fi

# Step 3: Code rollback
git log --oneline -5
echo "Enter rollback commit hash:"
read rollback_hash
git reset --hard $rollback_hash

# Step 4: Verify rollback
python manage.py check
python manage.py test --keepdb

echo "Rollback completed. System restored to working state."
```

## Performance Monitoring

### Key Metrics to Track
```python
PERFORMANCE_METRICS = {
    'api_response_time': {
        'target': '<200ms',
        'critical': '>500ms',
        'tool': 'Django debug toolbar + APM'
    },
    'database_query_time': {
        'target': '<50ms',
        'critical': '>200ms',
        'tool': 'PostgreSQL query analysis'
    },
    'frontend_load_time': {
        'target': '<2s',
        'critical': '>5s',
        'tool': 'Lighthouse CI'
    },
    'memory_usage': {
        'target': '<512MB per process',
        'critical': '>1GB per process',
        'tool': 'Memory profiling'
    }
}
```

### Monitoring Implementation
```bash
# Performance monitoring hooks (run after each phase)
echo "=== PERFORMANCE VALIDATION ==="

# API performance test
python manage.py test tests.performance.test_api_performance

# Database performance
python manage.py test tests.performance.test_database_queries

# Frontend performance
npm run lighthouse:ci

# Memory usage analysis
python -m memory_profiler manage.py test

echo "Performance validation completed"
```

## Team Coordination

### Weekly Development Rhythm
- **Monday**: Phase planning and dependency review
- **Wednesday**: Progress checkpoint and blocker resolution
- **Friday**: Phase completion review and next phase preparation

### Communication Protocol
```bash
# Daily progress updates via hooks
npx claude-flow@alpha hooks notify --message "Completed tenant middleware implementation"
npx claude-flow@alpha hooks progress --phase "2" --completion "75%"

# Blocker escalation
npx claude-flow@alpha hooks escalate --issue "Database migration performance concern" --priority "high"

# Knowledge sharing
npx claude-flow@alpha hooks knowledge-share --topic "tenant-isolation-patterns" --content "file://docs/patterns.md"
```

### Phase Handoff Protocol
```bash
# Phase completion checklist
echo "=== PHASE COMPLETION CHECKLIST ==="

# 1. All deliverables completed
[ -f "phase_deliverables.md" ] && echo "✓ Deliverables documented"

# 2. Tests passing
pytest tests/ --tb=short && echo "✓ All tests passing"

# 3. Code review approved
git log --grep="Approved-by" -1 && echo "✓ Code review approved"

# 4. Documentation updated
[ -d "docs/phase_X" ] && echo "✓ Documentation updated"

# 5. Performance benchmarks met
python scripts/validate_performance.py && echo "✓ Performance targets met"

# 6. Security review passed (if applicable)
[ -f "security_audit_passed.txt" ] && echo "✓ Security review passed"

echo "Phase ready for handoff to next team"
```

This development workflow ensures systematic, high-quality implementation of the Anthias SaaS enhancement while leveraging concurrent agent execution for maximum efficiency and maintaining strict quality standards throughout the development process.