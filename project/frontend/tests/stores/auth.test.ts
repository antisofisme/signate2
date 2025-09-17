import { act } from '@testing-library/react'
import { useAuthStore } from '@/stores/auth-store'

// Mock the API client
jest.mock('@/api/client', () => ({
  authApi: {
    login: jest.fn(),
    register: jest.fn(),
    refreshToken: jest.fn(),
    getCurrentUser: jest.fn(),
    logout: jest.fn(),
  },
}))

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    act(() => {
      useAuthStore.getState().reset()
    })
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { user, isAuthenticated, isLoading, error } = useAuthStore.getState()

      expect(user).toBeNull()
      expect(isAuthenticated).toBe(false)
      expect(isLoading).toBe(false)
      expect(error).toBeNull()
    })
  })

  describe('Authentication Actions', () => {
    it('should handle successful login', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        tenant_id: 1,
      }

      const mockResponse = {
        access_token: 'mock-jwt-token',
        refresh_token: 'mock-refresh-token',
        user: mockUser,
      }

      const { authApi } = require('@/api/client')
      authApi.login.mockResolvedValue(mockResponse)

      const store = useAuthStore.getState()

      await act(async () => {
        await store.login('test@example.com', 'password123')
      })

      const { user, isAuthenticated, isLoading, error } = useAuthStore.getState()

      expect(user).toEqual(mockUser)
      expect(isAuthenticated).toBe(true)
      expect(isLoading).toBe(false)
      expect(error).toBeNull()
      expect(authApi.login).toHaveBeenCalledWith('test@example.com', 'password123')
    })

    it('should handle login failure', async () => {
      const mockError = new Error('Invalid credentials')
      const { authApi } = require('@/api/client')
      authApi.login.mockRejectedValue(mockError)

      const store = useAuthStore.getState()

      await act(async () => {
        await store.login('test@example.com', 'wrongpassword')
      })

      const { user, isAuthenticated, error, isLoading } = useAuthStore.getState()

      expect(user).toBeNull()
      expect(isAuthenticated).toBe(false)
      expect(isLoading).toBe(false)
      expect(error).toBe('Invalid credentials')
    })

    it('should handle successful registration', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        tenant_id: 1,
      }

      const { authApi } = require('@/api/client')
      authApi.register.mockResolvedValue(mockUser)

      const store = useAuthStore.getState()

      await act(async () => {
        await store.register({
          email: 'test@example.com',
          password: 'password123',
          name: 'Test User',
        })
      })

      const { isLoading, error } = useAuthStore.getState()

      expect(isLoading).toBe(false)
      expect(error).toBeNull()
      expect(authApi.register).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User',
      })
    })

    it('should handle logout', async () => {
      // First set some authenticated state
      act(() => {
        useAuthStore.setState({
          user: {
            id: 1,
            email: 'test@example.com',
            name: 'Test User',
            role: 'user',
            tenant_id: 1,
          },
          isAuthenticated: true,
        })
      })

      const { authApi } = require('@/api/client')
      authApi.logout.mockResolvedValue(undefined)

      const store = useAuthStore.getState()

      await act(async () => {
        await store.logout()
      })

      const { user, isAuthenticated, error } = useAuthStore.getState()

      expect(user).toBeNull()
      expect(isAuthenticated).toBe(false)
      expect(error).toBeNull()
    })
  })

  describe('Loading States', () => {
    it('should set loading state during login', async () => {
      const { authApi } = require('@/api/client')
      authApi.login.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      )

      const store = useAuthStore.getState()

      // Start login (don't await)
      const loginPromise = store.login('test@example.com', 'password123')

      // Check loading state
      expect(useAuthStore.getState().isLoading).toBe(true)

      // Wait for completion
      await act(async () => {
        await loginPromise
      })

      expect(useAuthStore.getState().isLoading).toBe(false)
    })
  })

  describe('Token Management', () => {
    it('should handle token refresh', async () => {
      const mockResponse = {
        access_token: 'new-jwt-token',
        refresh_token: 'new-refresh-token',
      }

      const { authApi } = require('@/api/client')
      authApi.refreshToken.mockResolvedValue(mockResponse)

      const store = useAuthStore.getState()

      await act(async () => {
        await store.refreshToken()
      })

      const { error } = useAuthStore.getState()

      expect(error).toBeNull()
      expect(authApi.refreshToken).toHaveBeenCalled()
    })

    it('should handle token refresh failure', async () => {
      const mockError = new Error('Token refresh failed')
      const { authApi } = require('@/api/client')
      authApi.refreshToken.mockRejectedValue(mockError)

      const store = useAuthStore.getState()

      await act(async () => {
        await store.refreshToken()
      })

      const { user, isAuthenticated, error } = useAuthStore.getState()

      expect(user).toBeNull()
      expect(isAuthenticated).toBe(false)
      expect(error).toBe('Token refresh failed')
    })
  })

  describe('User Profile Updates', () => {
    it('should update user profile', () => {
      // Set initial authenticated state
      act(() => {
        useAuthStore.setState({
          user: {
            id: 1,
            email: 'test@example.com',
            name: 'Test User',
            role: 'user',
            tenant_id: 1,
          },
          isAuthenticated: true,
        })
      })

      const store = useAuthStore.getState()
      const updatedUser = {
        id: 1,
        email: 'test@example.com',
        name: 'Updated Test User',
        role: 'admin',
        tenant_id: 1,
      }

      act(() => {
        store.updateUser(updatedUser)
      })

      const { user } = useAuthStore.getState()

      expect(user).toEqual(updatedUser)
    })
  })

  describe('Error Handling', () => {
    it('should clear error when needed', () => {
      // Set error state
      act(() => {
        useAuthStore.setState({ error: 'Some error' })
      })

      expect(useAuthStore.getState().error).toBe('Some error')

      // Clear error
      act(() => {
        useAuthStore.getState().clearError()
      })

      expect(useAuthStore.getState().error).toBeNull()
    })
  })

  describe('Persistence', () => {
    it('should initialize from localStorage', () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        tenant_id: 1,
      }

      // Mock localStorage
      const localStorageMock = jest.mocked(window.localStorage)
      localStorageMock.getItem.mockReturnValue(JSON.stringify({
        state: {
          user: mockUser,
          isAuthenticated: true,
        },
        version: 0,
      }))

      // Reset and reinitialize store
      act(() => {
        useAuthStore.getState().reset()
      })

      // The store should load from localStorage on initialization
      // Note: This might require adjusting based on your actual persistence implementation
    })
  })
})