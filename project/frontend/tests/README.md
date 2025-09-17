# Frontend Testing Suite

This directory contains comprehensive testing infrastructure for the Signate Phase 5 frontend application built with Next.js 14, ShadCN UI, Zustand, and TypeScript.

## Testing Strategy

### Test Pyramid

```
         /\
        /E2E\      <- Few, high-value (Playwright)
       /------\
      /Integr.\ <- Moderate coverage (API + Components)
     /----------\
    /   Unit     \ <- Many, fast, focused (Jest + Testing Library)
   /--------------\
```

### Coverage Goals

- **Statements**: >90%
- **Branches**: >85%
- **Functions**: >90%
- **Lines**: >90%

## Test Types

### 1. Unit Tests (`tests/`)

**Location**: `tests/stores/`, `tests/api/`, `tests/utils/`

**Tools**: Jest + Testing Library + MSW

**Purpose**: Test individual functions, hooks, stores, and utilities in isolation.

**Examples**:
- Zustand store actions and state management
- API client methods and error handling
- Utility functions and data transformations
- Custom hooks behavior

**Run Command**: `npm test`

### 2. Component Tests (`tests/components/`)

**Tools**: Jest + Testing Library + jest-axe

**Purpose**: Test React components with user interactions, accessibility, and integration with stores.

**Features**:
- User interaction testing
- Accessibility validation with jest-axe
- Mock API responses with MSW
- Custom render functions with providers

**Run Command**: `npm test -- --testPathPattern=components`

### 3. Integration Tests

**Purpose**: Test API integration, authentication flows, and multi-tenant functionality.

**Coverage**:
- Authentication flows (login, logout, refresh)
- API error handling and retry logic
- Multi-tenant context switching
- Form validation and submission

### 4. E2E Tests (`tests/e2e/`)

**Tool**: Playwright

**Purpose**: Test complete user journeys across the application.

**Test Scenarios**:
- Authentication flows
- Dashboard navigation
- User management (CRUD operations)
- Asset management
- Multi-tenant workflows
- Mobile responsiveness

**Run Commands**:
- `npm run test:e2e` - Run all E2E tests
- `npm run test:e2e:ui` - Run with Playwright UI

### 5. Visual Regression Tests

**Tool**: Chromatic (Storybook)

**Purpose**: Detect unexpected visual changes in components.

**Features**:
- Component snapshot testing
- Cross-browser visual testing
- Design system validation
- Automated visual reviews in CI

**Run Command**: `npm run test:visual`

### 6. Performance Tests

**Tool**: Lighthouse CI

**Purpose**: Monitor and enforce performance standards.

**Metrics Tracked**:
- Core Web Vitals (LCP, FID, CLS)
- Performance score (>80%)
- Accessibility score (>90%)
- Best practices score (>80%)
- SEO score (>80%)

**Run Command**: `npm run test:performance`

## Configuration Files

### Jest Configuration
- `jest.config.js` - Main Jest configuration
- `tests/setup.ts` - Global test setup and mocks

### Playwright Configuration
- `playwright.config.ts` - E2E test configuration
- `tests/e2e/global-setup.ts` - Global E2E setup
- `tests/e2e/global-teardown.ts` - Global E2E cleanup

### Performance Testing
- `lighthouserc.js` - Lighthouse CI configuration
- `tests/performance/lighthouse.config.js` - Custom Lighthouse config

### Visual Testing
- `.github/workflows/chromatic.yml` - Chromatic CI workflow

## Test Utilities

### Mock Service Worker (MSW)
- `tests/mocks/handlers.ts` - API mock handlers
- `tests/mocks/server.ts` - MSW server setup

### Test Utilities
- `tests/utils/test-utils.tsx` - Custom render functions and utilities
- `tests/utils/factories.ts` - Test data factories

### Mock Files
- `tests/__mocks__/fileMock.js` - Static file mocks

## Running Tests

### Development Workflow

```bash
# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test -- auth.test.ts

# Run tests with coverage
npm run test:coverage

# Run E2E tests in UI mode
npm run test:e2e:ui
```

### CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

1. **Lint and Type Check**
2. **Unit and Integration Tests** with coverage reporting
3. **E2E Tests** across multiple browsers
4. **Performance Tests** with Lighthouse CI
5. **Security Audit** with npm audit and CodeQL
6. **Visual Regression Tests** with Chromatic

### Quality Gates

Tests must pass these criteria:

- ✅ All unit tests pass
- ✅ Code coverage >90%
- ✅ All E2E tests pass
- ✅ No accessibility violations
- ✅ Performance score >80%
- ✅ No security vulnerabilities
- ✅ No visual regressions

## Best Practices

### Test Structure

```typescript
describe('Component/Feature Name', () => {
  describe('Specific Behavior', () => {
    it('should do something specific', () => {
      // Arrange - Set up test data and conditions
      // Act - Perform the action being tested
      // Assert - Verify the expected outcome
    })
  })
})
```

### Accessibility Testing

```typescript
import { render } from '@/tests/utils/test-utils'

it('should be accessible', async () => {
  const { container } = render(<Component />)
  const axe = await import('jest-axe')
  const results = await axe.default(container)
  expect(results).toHaveNoViolations()
})
```

### Async Testing

```typescript
import { waitFor, screen } from '@testing-library/react'

it('should handle async operations', async () => {
  render(<AsyncComponent />)

  await waitFor(() => {
    expect(screen.getByText('Loaded data')).toBeInTheDocument()
  })
})
```

### User Interaction Testing

```typescript
import { userEvent } from '@testing-library/user-event'

it('should handle user interactions', async () => {
  const user = userEvent.setup()
  render(<InteractiveComponent />)

  await user.click(screen.getByRole('button'))
  await user.type(screen.getByLabelText('Email'), 'test@example.com')
})
```

## Debugging Tests

### Debug Tools

```bash
# Run Jest in debug mode
node --inspect-brk node_modules/.bin/jest --runInBand

# Debug Playwright tests
npx playwright test --debug

# Visual debugging with Playwright
npx playwright test --headed --slowMo=1000
```

### Common Issues

1. **Flaky E2E Tests**: Use proper waits and stable selectors
2. **Memory Leaks**: Clean up timers, subscriptions, and event listeners
3. **Async Issues**: Always await async operations in tests
4. **Mock Issues**: Reset mocks between tests with `jest.clearAllMocks()`

## Continuous Improvement

### Test Metrics Dashboard

Monitor test health with:
- Test execution time trends
- Flaky test identification
- Coverage trends over time
- Performance regression detection

### Regular Maintenance

- Review and update test data factories monthly
- Audit test coverage for new features
- Update E2E tests for UI changes
- Review and optimize slow tests

## Contributing

### Adding New Tests

1. Follow the existing file structure
2. Use appropriate test type (unit vs integration vs E2E)
3. Include accessibility tests for UI components
4. Add performance tests for new pages/features
5. Update test documentation

### Test Review Checklist

- [ ] Tests are focused and test one thing
- [ ] Test names clearly describe what is being tested
- [ ] Proper use of arrange-act-assert pattern
- [ ] Accessibility considerations included
- [ ] Performance implications considered
- [ ] Mock data is realistic and reusable
- [ ] Tests are deterministic (not flaky)

For questions or issues with testing, please refer to the team documentation or create an issue in the project repository.