# Claude Code Concurrent Execution Guide - Digital Signage Enhancement

## Overview

This guide provides specific instructions for implementing the digital signage enhancement using Claude Code's Task tool for concurrent agent execution, following the CLAUDE.md guidelines for optimal coordination and efficiency.

## Core Execution Principles

### 1. Single Message = All Related Operations
**GOLDEN RULE**: Every development phase must be executed in a single message with all related operations batched together.

### 2. Concurrent Agent Orchestration Pattern
```javascript
[Single Message Pattern]:
  // 1. Spawn ALL agents concurrently via Claude Code Task tool
  Task("Agent Name", "Complete instructions with deliverables", "agent-type")
  Task("Agent Name", "Complete instructions with deliverables", "agent-type")
  // ... all agents spawned together

  // 2. Batch ALL todos in ONE call
  TodoWrite { todos: [...comprehensive todo list...] }

  // 3. Parallel file operations
  Read "files-to-understand"
  Write "new-files-needed"
  MultiEdit "files-to-update"

  // 4. Batch ALL bash operations
  Bash "command1; command2; command3"
```

## Phase-by-Phase Concurrent Execution Plans

### Phase 1: Multi-Tenant Foundation

#### Single Message Implementation:
```javascript
// Execute this ENTIRE block in ONE message:

Task("Database Architect", `
ROLE: Database Schema Designer
TASK: Design comprehensive multi-tenant PostgreSQL schema with Row-Level Security (RLS)

DELIVERABLES:
1. Complete PostgreSQL schema with tenant isolation
2. Migration scripts from SQLite to PostgreSQL
3. Performance indexes for multi-tenant queries
4. RLS policies for data isolation
5. Backup and restore procedures

COORDINATION HOOKS (CRITICAL):
# Before starting
npx claude-flow@alpha hooks pre-task --description "Designing multi-tenant PostgreSQL schema"
npx claude-flow@alpha hooks session-restore --session-id "signage-mt-foundation"

# During work
npx claude-flow@alpha hooks post-edit --file "migrations/0001_multi_tenant.sql" --memory-key "database/schema-design"
npx claude-flow@alpha hooks notify --message "Completed tenant isolation schema with RLS policies"

# After completion
npx claude-flow@alpha hooks post-task --task-id "database-schema-design"

MEMORY STORAGE:
- Store schema design in memory key 'database/mt-schema'
- Store migration strategy in memory key 'database/migration-plan'
- Share performance indexes in memory key 'database/indexes'

FILES TO CREATE:
- /migrations/0001_multi_tenant_schema.sql
- /scripts/migrate_sqlite_to_postgresql.py
- /backend/lib/database_utils.py
- /docs/database-schema.md

QUALITY REQUIREMENTS:
- Schema must support 10,000+ tenants
- RLS policies enforce strict data isolation
- Migration must handle existing data safely
- Performance indexes for sub-100ms queries
`, "code-analyzer")

Task("System Architect", `
ROLE: Multi-Tenant System Designer
TASK: Design tenant discovery, isolation middleware, and resource allocation

DELIVERABLES:
1. Tenant middleware for request routing
2. Subdomain/header-based tenant discovery
3. Resource allocation framework per tenant tier
4. Security isolation policies
5. API versioning strategy (v3)

COORDINATION HOOKS:
npx claude-flow@alpha hooks pre-task --description "Designing tenant middleware and isolation"
npx claude-flow@alpha hooks session-restore --session-id "signage-mt-foundation"
npx claude-flow@alpha hooks post-edit --file "middleware/tenant_middleware.py" --memory-key "middleware/tenant-isolation"
npx claude-flow@alpha hooks notify --message "Completed tenant discovery and isolation middleware"
npx claude-flow@alpha hooks post-task --task-id "system-architecture"

MEMORY INTEGRATION:
- Read database schema from memory key 'database/mt-schema'
- Store middleware patterns in memory key 'middleware/patterns'
- Share resource limits in memory key 'system/resource-limits'

FILES TO CREATE:
- /backend/middleware/tenant_middleware.py
- /backend/lib/tenant_discovery.py
- /backend/lib/resource_manager.py
- /backend/lib/tenant_utils.py
- /docs/tenant-architecture.md

REQUIREMENTS:
- Support subdomain and header-based discovery
- Enforce tenant resource limits
- Provide secure tenant isolation
- Handle 1000+ concurrent requests
`, "system-architect")

Task("Backend Lead Developer", `
ROLE: Django Backend Implementation Lead
TASK: Implement Django multi-tenant models and API foundation

DELIVERABLES:
1. Enhanced Django models with tenant relationships
2. API v3 foundation with tenant-aware endpoints
3. Database connection management with RLS
4. Basic CRUD operations with tenant isolation
5. API serializers and validators

COORDINATION HOOKS:
npx claude-flow@alpha hooks pre-task --description "Implementing Django multi-tenant backend"
npx claude-flow@alpha hooks session-restore --session-id "signage-mt-foundation"
npx claude-flow@alpha hooks post-edit --file "models_v3.py" --memory-key "backend/models"
npx claude-flow@alpha hooks post-edit --file "api/v3/views.py" --memory-key "backend/api-v3"
npx claude-flow@alpha hooks notify --message "Completed multi-tenant Django models and API v3"
npx claude-flow@alpha hooks post-task --task-id "backend-implementation"

MEMORY INTEGRATION:
- Use schema from memory key 'database/mt-schema'
- Follow middleware patterns from memory key 'middleware/patterns'
- Store API contracts in memory key 'api/v3/contracts'
- Share model patterns in memory key 'backend/model-patterns'

FILES TO CREATE:
- /backend/anthias_app/models_v3.py
- /backend/api/v3/__init__.py
- /backend/api/v3/views.py
- /backend/api/v3/serializers.py
- /backend/api/v3/urls.py
- /backend/api/v3/permissions.py

REQUIREMENTS:
- All models must be tenant-aware
- API endpoints enforce tenant isolation
- Support for 10,000+ tenants
- <200ms API response times
`, "backend-dev")

Task("Frontend Architecture Lead", `
ROLE: React Frontend Foundation Developer
TASK: Build React frontend foundation with tenant-aware components

DELIVERABLES:
1. React application structure with tenant context
2. Authentication and routing components
3. Tenant-aware API client
4. Base UI components and layouts
5. State management setup

COORDINATION HOOKS:
npx claude-flow@alpha hooks pre-task --description "Building React frontend foundation"
npx claude-flow@alpha hooks session-restore --session-id "signage-mt-foundation"
npx claude-flow@alpha hooks post-edit --file "src/contexts/TenantContext.jsx" --memory-key "frontend/tenant-context"
npx claude-flow@alpha hooks notify --message "Completed React frontend foundation with tenant support"
npx claude-flow@alpha hooks post-task --task-id "frontend-foundation"

MEMORY INTEGRATION:
- Use API contracts from memory key 'api/v3/contracts'
- Store UI patterns in memory key 'frontend/patterns'
- Share component library in memory key 'frontend/components'

FILES TO CREATE:
- /frontend/src/contexts/TenantContext.jsx
- /frontend/src/contexts/AuthContext.jsx
- /frontend/src/services/apiClient.js
- /frontend/src/components/layout/BaseLayout.jsx
- /frontend/src/hooks/useTenant.js
- /frontend/src/utils/apiUtils.js

REQUIREMENTS:
- Tenant context available throughout app
- API client handles tenant headers
- Responsive design for all screen sizes
- TypeScript support for type safety
`, "coder")

Task("Quality Assurance Engineer", `
ROLE: Test Infrastructure and Validation Lead
TASK: Create comprehensive test infrastructure for multi-tenant system

DELIVERABLES:
1. Unit test framework for models and API
2. Integration tests for tenant isolation
3. Performance tests for database queries
4. Security tests for data isolation
5. Test data factories and fixtures

COORDINATION HOOKS:
npx claude-flow@alpha hooks pre-task --description "Building comprehensive test infrastructure"
npx claude-flow@alpha hooks session-restore --session-id "signage-mt-foundation"
npx claude-flow@alpha hooks post-edit --file "tests/conftest.py" --memory-key "tests/infrastructure"
npx claude-flow@alpha hooks notify --message "Completed test infrastructure with >90% coverage setup"
npx claude-flow@alpha hooks post-task --task-id "test-infrastructure"

MEMORY INTEGRATION:
- Test API contracts from memory key 'api/v3/contracts'
- Validate database schema from memory key 'database/mt-schema'
- Store test patterns in memory key 'tests/patterns'

FILES TO CREATE:
- /tests/conftest.py
- /tests/factories.py
- /tests/unit/test_tenant_models.py
- /tests/integration/test_tenant_isolation.py
- /tests/performance/test_db_performance.py
- /tests/security/test_data_isolation.py

REQUIREMENTS:
- >90% code coverage for all modules
- Tenant isolation verification tests
- Performance benchmarks for <50ms DB queries
- Security tests for cross-tenant access prevention
`, "tester")

Task("DevOps Infrastructure Engineer", `
ROLE: Development and CI/CD Infrastructure Lead
TASK: Setup complete development and deployment infrastructure

DELIVERABLES:
1. Docker Compose development environment
2. PostgreSQL and Redis service configuration
3. CI/CD pipeline with GitHub Actions
4. Environment configuration management
5. Local development automation scripts

COORDINATION HOOKS:
npx claude-flow@alpha hooks pre-task --description "Setting up development and CI/CD infrastructure"
npx claude-flow@alpha hooks session-restore --session-id "signage-mt-foundation"
npx claude-flow@alpha hooks post-edit --file "docker-compose.yml" --memory-key "devops/docker-config"
npx claude-flow@alpha hooks notify --message "Completed development infrastructure with CI/CD pipeline"
npx claude-flow@alpha hooks post-task --task-id "devops-infrastructure"

MEMORY INTEGRATION:
- Use database requirements from memory key 'database/mt-schema'
- Store infrastructure configs in memory key 'devops/configs'
- Share deployment patterns in memory key 'devops/deployment'

FILES TO CREATE:
- /docker-compose.yml
- /docker-compose.override.yml
- /.github/workflows/ci.yml
- /.github/workflows/test.yml
- /scripts/setup-dev-env.sh
- /scripts/run-tests.sh
- /Dockerfile.backend
- /Dockerfile.frontend

REQUIREMENTS:
- One-command development setup
- Automated testing on every PR
- Environment parity between dev/staging/prod
- <5 minute CI/CD pipeline execution
`, "cicd-engineer")

// Batch ALL todos for Phase 1
TodoWrite({
  todos: [
    {content: "Design PostgreSQL multi-tenant schema with RLS", status: "in_progress", activeForm: "Designing PostgreSQL schema"},
    {content: "Create tenant discovery and isolation middleware", status: "in_progress", activeForm: "Creating tenant middleware"},
    {content: "Implement Django models with tenant relationships", status: "in_progress", activeForm: "Implementing Django models"},
    {content: "Build React frontend foundation with tenant context", status: "in_progress", activeForm: "Building React foundation"},
    {content: "Setup comprehensive test infrastructure", status: "in_progress", activeForm: "Setting up test infrastructure"},
    {content: "Configure Docker development environment", status: "in_progress", activeForm: "Configuring Docker environment"},
    {content: "Implement database migration scripts", status: "pending", activeForm: "Implementing migration scripts"},
    {content: "Create API v3 endpoint foundation", status: "pending", activeForm: "Creating API v3 endpoints"},
    {content: "Write unit tests for tenant models", status: "pending", activeForm: "Writing unit tests"},
    {content: "Setup CI/CD pipeline with GitHub Actions", status: "pending", activeForm: "Setting up CI/CD pipeline"},
    {content: "Configure PostgreSQL and Redis services", status: "pending", activeForm: "Configuring database services"},
    {content: "Implement tenant isolation security tests", status: "pending", activeForm: "Implementing security tests"}
  ]
})

// Parallel file structure creation
Bash "mkdir -p {backend/{api/v3,lib,middleware},frontend/src/{components,contexts,services,hooks,utils},tests/{unit,integration,performance,security},docs/{architecture,api,development},migrations,scripts}"

// Parallel dependency installation
Bash "cd backend && pip install -r requirements/requirements.txt && pip install -r requirements/requirements.dev.txt"
Bash "cd frontend && npm install"

// Initialize development environment
Bash "docker-compose up -d postgres redis"
Bash "cd backend && python manage.py makemigrations"
```

### Phase 2: Authentication & RBAC Implementation

#### Single Message Implementation:
```javascript
// Execute this ENTIRE block in ONE message:

Task("Security Architecture Lead", `
ROLE: Authentication and Security System Designer
TASK: Implement comprehensive authentication and RBAC system

DELIVERABLES:
1. JWT authentication with refresh token mechanism
2. Multi-factor authentication (MFA) support
3. Role-based permission system with granular controls
4. Session management and security
5. API authentication middleware

COORDINATION HOOKS:
npx claude-flow@alpha hooks pre-task --description "Implementing authentication and RBAC system"
npx claude-flow@alpha hooks session-restore --session-id "signage-auth-system"
npx claude-flow@alpha hooks post-edit --file "lib/auth_v3.py" --memory-key "auth/system-design"
npx claude-flow@alpha hooks notify --message "Completed JWT authentication with RBAC system"
npx claude-flow@alpha hooks post-task --task-id "auth-system"

MEMORY INTEGRATION:
- Use tenant middleware from memory key 'middleware/patterns'
- Store auth patterns in memory key 'auth/jwt-rbac'
- Share permission matrix in memory key 'auth/permissions'

FILES TO CREATE:
- /backend/lib/auth_v3.py
- /backend/lib/permissions.py
- /backend/lib/mfa.py
- /backend/lib/jwt_utils.py
- /backend/api/v3/auth_views.py
- /backend/api/v3/auth_serializers.py

REQUIREMENTS:
- JWT tokens with 1-hour access, 7-day refresh
- MFA support (TOTP, SMS, Email)
- Granular role-based permissions
- Account lockout after 5 failed attempts
- Session hijacking prevention
`, "security-manager")

Task("Backend Authentication Developer", `
ROLE: Django Authentication Integration Specialist
TASK: Integrate authentication system with existing tenant-aware backend

DELIVERABLES:
1. Authentication middleware integration
2. Permission decorators for API endpoints
3. User-tenant relationship management
4. Password security and validation
5. API authentication flow implementation

COORDINATION HOOKS:
npx claude-flow@alpha hooks pre-task --description "Integrating authentication with tenant backend"
npx claude-flow@alpha hooks session-restore --session-id "signage-auth-system"
npx claude-flow@alpha hooks post-edit --file "api/v3/auth_views.py" --memory-key "backend/auth-integration"
npx claude-flow@alpha hooks notify --message "Completed authentication integration with tenant system"
npx claude-flow@alpha hooks post-task --task-id "backend-auth-integration"

MEMORY INTEGRATION:
- Use auth patterns from memory key 'auth/jwt-rbac'
- Update API contracts in memory key 'api/v3/contracts'
- Use tenant patterns from memory key 'middleware/patterns'

FILES TO UPDATE:
- /backend/api/v3/views.py
- /backend/api/v3/serializers.py
- /backend/middleware/tenant_middleware.py
- /backend/anthias_app/models_v3.py

FILES TO CREATE:
- /backend/decorators/auth_decorators.py
- /backend/api/v3/user_views.py
- /backend/lib/password_utils.py

REQUIREMENTS:
- All API endpoints require proper authentication
- Tenant isolation maintained in auth system
- Password complexity enforcement
- Rate limiting on auth endpoints
`, "backend-dev")

Task("Frontend Authentication Developer", `
ROLE: React Authentication UI Specialist
TASK: Build comprehensive authentication and user management interfaces

DELIVERABLES:
1. Login/logout components with MFA support
2. User management dashboard for tenant admins
3. Role assignment and permission management UI
4. Password reset and change functionality
5. Authentication state management

COORDINATION HOOKS:
npx claude-flow@alpha hooks pre-task --description "Building authentication UI components"
npx claude-flow@alpha hooks session-restore --session-id "signage-auth-system"
npx claude-flow@alpha hooks post-edit --file "components/auth/LoginForm.jsx" --memory-key "frontend/auth-components"
npx claude-flow@alpha hooks notify --message "Completed authentication UI with user management"
npx claude-flow@alpha hooks post-task --task-id "frontend-auth"

MEMORY INTEGRATION:
- Use API contracts from memory key 'api/v3/contracts'
- Use auth patterns from memory key 'auth/jwt-rbac'
- Store UI components in memory key 'frontend/auth-ui'

FILES TO CREATE:
- /frontend/src/components/auth/LoginForm.jsx
- /frontend/src/components/auth/MFASetup.jsx
- /frontend/src/components/user/UserManagement.jsx
- /frontend/src/components/user/RoleAssignment.jsx
- /frontend/src/components/auth/PasswordReset.jsx
- /frontend/src/hooks/useAuth.js
- /frontend/src/services/authService.js

REQUIREMENTS:
- Responsive design for all devices
- Accessible form components
- Real-time validation feedback
- Secure token storage and management
`, "coder")

Task("Security Test Engineer", `
ROLE: Authentication Security Testing Specialist
TASK: Comprehensive security testing for authentication system

DELIVERABLES:
1. Authentication flow security tests
2. Permission boundary validation tests
3. JWT token security and tampering tests
4. Brute force protection tests
5. Session security and hijacking prevention tests

COORDINATION HOOKS:
npx claude-flow@alpha hooks pre-task --description "Testing authentication security"
npx claude-flow@alpha hooks session-restore --session-id "signage-auth-system"
npx claude-flow@alpha hooks post-edit --file "tests/security/test_auth_security.py" --memory-key "tests/auth-security"
npx claude-flow@alpha hooks notify --message "Completed comprehensive authentication security testing"
npx claude-flow@alpha hooks post-task --task-id "auth-security-testing"

MEMORY INTEGRATION:
- Test auth patterns from memory key 'auth/jwt-rbac'
- Validate API security from memory key 'api/v3/contracts'
- Store test results in memory key 'tests/security-results'

FILES TO CREATE:
- /tests/security/test_authentication.py
- /tests/security/test_authorization.py
- /tests/security/test_jwt_security.py
- /tests/security/test_brute_force_protection.py
- /tests/integration/test_auth_flow.py
- /tests/performance/test_auth_performance.py

REQUIREMENTS:
- Comprehensive security vulnerability testing
- Performance testing for auth endpoints
- Cross-tenant access prevention validation
- MFA security testing
`, "tester")

// Continue with similar patterns for other phases...
```

## Best Practices for Concurrent Execution

### 1. Agent Instruction Quality
Each Task instruction MUST include:
- **ROLE**: Clear role definition
- **TASK**: Specific task description
- **DELIVERABLES**: Concrete, measurable outputs
- **COORDINATION HOOKS**: Exact hook commands to run
- **MEMORY INTEGRATION**: How to use/store shared information
- **FILES TO CREATE/UPDATE**: Specific file paths
- **REQUIREMENTS**: Quality and performance criteria

### 2. Memory Coordination Patterns
```javascript
// Memory key naming convention
MEMORY_KEYS = {
  'database/schema-design': 'Database schema and migration plans',
  'middleware/tenant-isolation': 'Tenant middleware patterns',
  'api/v3/contracts': 'API endpoint specifications',
  'auth/jwt-rbac': 'Authentication and permission patterns',
  'frontend/components': 'React component patterns',
  'tests/patterns': 'Testing strategies and fixtures',
  'devops/configs': 'Infrastructure configurations'
}
```

### 3. File Organization Rules
- **NEVER save to root folder**
- Use appropriate subdirectories:
  - `/backend/` - Django backend code
  - `/frontend/` - React frontend code
  - `/tests/` - All test files
  - `/docs/` - Documentation
  - `/scripts/` - Utility scripts
  - `/migrations/` - Database migrations

### 4. Quality Gates
Every agent must ensure:
- Code follows project standards (Black, ESLint)
- Tests achieve >90% coverage
- Documentation is updated
- Security requirements met
- Performance benchmarks achieved

## Troubleshooting Concurrent Execution

### Common Issues and Solutions

1. **Memory Key Conflicts**:
   ```bash
   # If memory key doesn't exist, create it
   npx claude-flow@alpha hooks memory-store --key "new-key" --value "initial-data"
   ```

2. **Hook Execution Failures**:
   ```bash
   # Check hook status
   npx claude-flow@alpha hooks status

   # Restart session if needed
   npx claude-flow@alpha hooks session-start --session-id "new-session"
   ```

3. **Agent Coordination Issues**:
   - Ensure all agents use same session-id
   - Verify memory keys are consistent
   - Check that all agents complete pre-task hooks

### Success Validation

After each phase, verify:
- [ ] All agents completed successfully
- [ ] Memory keys contain expected data
- [ ] Files created in correct locations
- [ ] Tests pass with required coverage
- [ ] Documentation updated
- [ ] Quality gates satisfied

## Performance Optimization

### Concurrent Execution Tips

1. **Batch Operations**: Always group related operations
2. **Memory Efficiency**: Use memory keys to avoid redundant work
3. **Parallel File Ops**: Read/Write/Edit files in parallel
4. **Hook Coordination**: Use hooks for real-time coordination
5. **Quality Gates**: Run tests concurrently where possible

### Timeline Optimization

Following this concurrent execution pattern should achieve:
- **84.8% faster development** (vs sequential)
- **32.3% token reduction** (vs multiple messages)
- **2.8-4.4x speed improvement** (vs traditional approaches)
- **90%+ quality compliance** (through automation)

This guide ensures maximum efficiency and coordination when implementing the digital signage enhancement using Claude Code's Task tool for concurrent agent execution.