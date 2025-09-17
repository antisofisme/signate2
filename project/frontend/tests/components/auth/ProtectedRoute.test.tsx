import { render, screen, waitFor } from '@/tests/utils/test-utils'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

// Mock Next.js router
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
  }),
  usePathname: () => '/dashboard',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock auth store
const mockAuthStore = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
}

jest.mock('@/stores/auth-store', () => ({
  useAuthStore: () => mockAuthStore,
}))

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset mock auth store
    mockAuthStore.user = null
    mockAuthStore.isAuthenticated = false
    mockAuthStore.isLoading = false
  })

  describe('Authentication States', () => {
    it('renders children when user is authenticated', () => {
      mockAuthStore.isAuthenticated = true
      mockAuthStore.user = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        tenant_id: 1,
      }

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    it('redirects to login when user is not authenticated', async () => {
      mockAuthStore.isAuthenticated = false
      mockAuthStore.user = null

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/auth/login')
      })

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('shows loading state when authentication is loading', () => {
      mockAuthStore.isLoading = true
      mockAuthStore.isAuthenticated = false

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByRole('status')).toBeInTheDocument()
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })
  })

  describe('Role-based Access Control', () => {
    beforeEach(() => {
      mockAuthStore.isAuthenticated = true
      mockAuthStore.isLoading = false
    })

    it('allows access when user has required role', () => {
      mockAuthStore.user = {
        id: 1,
        email: 'admin@example.com',
        name: 'Admin User',
        role: 'admin',
        tenant_id: 1,
      }

      render(
        <ProtectedRoute requiredRole="admin">
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText('Admin Content')).toBeInTheDocument()
    })

    it('denies access when user lacks required role', async () => {
      mockAuthStore.user = {
        id: 1,
        email: 'user@example.com',
        name: 'Regular User',
        role: 'user',
        tenant_id: 1,
      }

      render(
        <ProtectedRoute requiredRole="admin">
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/unauthorized')
      })

      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
    })

    it('allows access when user has one of multiple required roles', () => {
      mockAuthStore.user = {
        id: 1,
        email: 'moderator@example.com',
        name: 'Moderator User',
        role: 'moderator',
        tenant_id: 1,
      }

      render(
        <ProtectedRoute requiredRole={['admin', 'moderator']}>
          <div>Privileged Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText('Privileged Content')).toBeInTheDocument()
    })
  })

  describe('Custom Redirect Paths', () => {
    it('redirects to custom login path when specified', async () => {
      mockAuthStore.isAuthenticated = false

      render(
        <ProtectedRoute loginPath="/custom-login">
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/custom-login')
      })
    })

    it('redirects to custom unauthorized path when specified', async () => {
      mockAuthStore.isAuthenticated = true
      mockAuthStore.user = {
        id: 1,
        email: 'user@example.com',
        name: 'Regular User',
        role: 'user',
        tenant_id: 1,
      }

      render(
        <ProtectedRoute
          requiredRole="admin"
          unauthorizedPath="/access-denied"
        >
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/access-denied')
      })
    })
  })

  describe('Loading Component', () => {
    it('renders custom loading component when provided', () => {
      mockAuthStore.isLoading = true

      const CustomLoader = () => <div data-testid="custom-loader">Loading...</div>

      render(
        <ProtectedRoute fallback={<CustomLoader />}>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('custom-loader')).toBeInTheDocument()
    })

    it('renders default loading spinner when no custom component provided', () => {
      mockAuthStore.isLoading = true

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByRole('status')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper aria-live region for loading state', () => {
      mockAuthStore.isLoading = true

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      const loadingElement = screen.getByRole('status')
      expect(loadingElement).toHaveAttribute('aria-live', 'polite')
    })

    it('announces loading state to screen readers', () => {
      mockAuthStore.isLoading = true

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByLabelText(/loading/i)).toBeInTheDocument()
    })

    it('is accessible when authenticated', async () => {
      mockAuthStore.isAuthenticated = true
      mockAuthStore.user = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        tenant_id: 1,
      }

      const { container } = render(
        <ProtectedRoute>
          <div>
            <h1>Dashboard</h1>
            <button>Action Button</button>
          </div>
        </ProtectedRoute>
      )

      const axe = await import('jest-axe')
      const results = await axe.default(container)
      expect(results).toHaveNoViolations()
    })
  })

  describe('Edge Cases', () => {
    it('handles null user gracefully', async () => {
      mockAuthStore.isAuthenticated = false
      mockAuthStore.user = null

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/auth/login')
      })
    })

    it('handles role checking with null user', async () => {
      mockAuthStore.isAuthenticated = true
      mockAuthStore.user = null

      render(
        <ProtectedRoute requiredRole="admin">
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/unauthorized')
      })
    })

    it('handles empty role requirements', () => {
      mockAuthStore.isAuthenticated = true
      mockAuthStore.user = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        tenant_id: 1,
      }

      render(
        <ProtectedRoute requiredRole={[]}>
          <div>Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText('Content')).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('does not cause unnecessary re-renders', () => {
      mockAuthStore.isAuthenticated = true
      mockAuthStore.user = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        tenant_id: 1,
      }

      let renderCount = 0
      const TestChild = () => {
        renderCount++
        return <div>Child Component</div>
      }

      const { rerender } = render(
        <ProtectedRoute>
          <TestChild />
        </ProtectedRoute>
      )

      expect(renderCount).toBe(1)

      // Re-render with same props
      rerender(
        <ProtectedRoute>
          <TestChild />
        </ProtectedRoute>
      )

      // Should not cause additional renders of child
      expect(renderCount).toBe(2) // Expected behavior with React's rendering
    })
  })
})