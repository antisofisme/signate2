import { act } from '@testing-library/react'
import { useTenantStore } from '@/stores/tenant-store'

// Mock the API client
jest.mock('@/api/client', () => ({
  tenantApi: {
    getTenants: jest.fn(),
    getTenant: jest.fn(),
    createTenant: jest.fn(),
    updateTenant: jest.fn(),
    deleteTenant: jest.fn(),
  },
}))

const mockTenant = {
  id: 1,
  name: 'Test Tenant',
  domain: 'test.signate.com',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const mockTenants = [
  mockTenant,
  {
    id: 2,
    name: 'Another Tenant',
    domain: 'another.signate.com',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

describe('Tenant Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    act(() => {
      useTenantStore.getState().reset()
    })
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const {
        tenants,
        currentTenant,
        isLoading,
        error,
      } = useTenantStore.getState()

      expect(tenants).toEqual([])
      expect(currentTenant).toBeNull()
      expect(isLoading).toBe(false)
      expect(error).toBeNull()
    })
  })

  describe('Tenant Loading', () => {
    it('should fetch tenants successfully', async () => {
      const { tenantApi } = require('@/api/client')
      tenantApi.getTenants.mockResolvedValue({
        items: mockTenants,
        total: 2,
        page: 1,
        pages: 1,
      })

      const store = useTenantStore.getState()

      await act(async () => {
        await store.fetchTenants()
      })

      const { tenants, isLoading, error } = useTenantStore.getState()

      expect(tenants).toEqual(mockTenants)
      expect(isLoading).toBe(false)
      expect(error).toBeNull()
      expect(tenantApi.getTenants).toHaveBeenCalled()
    })

    it('should handle fetch tenants error', async () => {
      const mockError = new Error('Failed to fetch tenants')
      const { tenantApi } = require('@/api/client')
      tenantApi.getTenants.mockRejectedValue(mockError)

      const store = useTenantStore.getState()

      await act(async () => {
        await store.fetchTenants()
      })

      const { tenants, isLoading, error } = useTenantStore.getState()

      expect(tenants).toEqual([])
      expect(isLoading).toBe(false)
      expect(error).toBe('Failed to fetch tenants')
    })

    it('should set current tenant', async () => {
      const { tenantApi } = require('@/api/client')
      tenantApi.getTenant.mockResolvedValue(mockTenant)

      const store = useTenantStore.getState()

      await act(async () => {
        await store.setCurrentTenant(1)
      })

      const { currentTenant, isLoading, error } = useTenantStore.getState()

      expect(currentTenant).toEqual(mockTenant)
      expect(isLoading).toBe(false)
      expect(error).toBeNull()
      expect(tenantApi.getTenant).toHaveBeenCalledWith(1)
    })
  })

  describe('Tenant Management', () => {
    it('should create tenant successfully', async () => {
      const newTenantData = {
        name: 'New Tenant',
        domain: 'new.signate.com',
      }

      const createdTenant = {
        id: 3,
        ...newTenantData,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      const { tenantApi } = require('@/api/client')
      tenantApi.createTenant.mockResolvedValue(createdTenant)

      // Set initial tenants
      act(() => {
        useTenantStore.setState({ tenants: mockTenants })
      })

      const store = useTenantStore.getState()

      await act(async () => {
        await store.createTenant(newTenantData)
      })

      const { tenants, isLoading, error } = useTenantStore.getState()

      expect(tenants).toContainEqual(createdTenant)
      expect(tenants).toHaveLength(3)
      expect(isLoading).toBe(false)
      expect(error).toBeNull()
      expect(tenantApi.createTenant).toHaveBeenCalledWith(newTenantData)
    })

    it('should update tenant successfully', async () => {
      const updateData = {
        name: 'Updated Tenant',
        domain: 'updated.signate.com',
      }

      const updatedTenant = {
        ...mockTenant,
        ...updateData,
        updated_at: '2024-01-02T00:00:00Z',
      }

      const { tenantApi } = require('@/api/client')
      tenantApi.updateTenant.mockResolvedValue(updatedTenant)

      // Set initial tenants
      act(() => {
        useTenantStore.setState({ tenants: mockTenants })
      })

      const store = useTenantStore.getState()

      await act(async () => {
        await store.updateTenant(1, updateData)
      })

      const { tenants, isLoading, error } = useTenantStore.getState()

      expect(tenants.find(t => t.id === 1)).toEqual(updatedTenant)
      expect(isLoading).toBe(false)
      expect(error).toBeNull()
      expect(tenantApi.updateTenant).toHaveBeenCalledWith(1, updateData)
    })

    it('should delete tenant successfully', async () => {
      const { tenantApi } = require('@/api/client')
      tenantApi.deleteTenant.mockResolvedValue(undefined)

      // Set initial tenants
      act(() => {
        useTenantStore.setState({ tenants: mockTenants })
      })

      const store = useTenantStore.getState()

      await act(async () => {
        await store.deleteTenant(1)
      })

      const { tenants, isLoading, error } = useTenantStore.getState()

      expect(tenants.find(t => t.id === 1)).toBeUndefined()
      expect(tenants).toHaveLength(1)
      expect(isLoading).toBe(false)
      expect(error).toBeNull()
      expect(tenantApi.deleteTenant).toHaveBeenCalledWith(1)
    })
  })

  describe('Loading States', () => {
    it('should set loading state during fetch', async () => {
      const { tenantApi } = require('@/api/client')
      tenantApi.getTenants.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      )

      const store = useTenantStore.getState()

      // Start fetch (don't await)
      const fetchPromise = store.fetchTenants()

      // Check loading state
      expect(useTenantStore.getState().isLoading).toBe(true)

      // Wait for completion
      await act(async () => {
        await fetchPromise
      })

      expect(useTenantStore.getState().isLoading).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('should clear error when needed', () => {
      // Set error state
      act(() => {
        useTenantStore.setState({ error: 'Some error' })
      })

      expect(useTenantStore.getState().error).toBe('Some error')

      // Clear error
      act(() => {
        useTenantStore.getState().clearError()
      })

      expect(useTenantStore.getState().error).toBeNull()
    })

    it('should handle create tenant error', async () => {
      const mockError = new Error('Failed to create tenant')
      const { tenantApi } = require('@/api/client')
      tenantApi.createTenant.mockRejectedValue(mockError)

      const store = useTenantStore.getState()

      await act(async () => {
        await store.createTenant({
          name: 'New Tenant',
          domain: 'new.signate.com',
        })
      })

      const { isLoading, error } = useTenantStore.getState()

      expect(isLoading).toBe(false)
      expect(error).toBe('Failed to create tenant')
    })
  })

  describe('Tenant Context Switching', () => {
    it('should switch tenant context', () => {
      // Set initial tenants
      act(() => {
        useTenantStore.setState({ tenants: mockTenants })
      })

      const store = useTenantStore.getState()

      act(() => {
        store.switchTenant(2)
      })

      const { currentTenant } = useTenantStore.getState()

      expect(currentTenant).toEqual(mockTenants[1])
    })

    it('should handle switching to non-existent tenant', () => {
      // Set initial tenants
      act(() => {
        useTenantStore.setState({ tenants: mockTenants })
      })

      const store = useTenantStore.getState()

      act(() => {
        store.switchTenant(999)
      })

      const { currentTenant } = useTenantStore.getState()

      expect(currentTenant).toBeNull()
    })
  })

  describe('Tenant Filtering', () => {
    it('should filter tenants by domain', () => {
      // Set initial tenants
      act(() => {
        useTenantStore.setState({ tenants: mockTenants })
      })

      const store = useTenantStore.getState()
      const filteredTenants = store.getTenantsByDomain('test.signate.com')

      expect(filteredTenants).toHaveLength(1)
      expect(filteredTenants[0]).toEqual(mockTenant)
    })

    it('should return empty array for non-matching domain', () => {
      // Set initial tenants
      act(() => {
        useTenantStore.setState({ tenants: mockTenants })
      })

      const store = useTenantStore.getState()
      const filteredTenants = store.getTenantsByDomain('nonexistent.com')

      expect(filteredTenants).toHaveLength(0)
    })
  })
})