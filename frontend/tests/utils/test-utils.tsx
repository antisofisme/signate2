import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/contexts/auth-context'
import { TenantProvider } from '@/contexts/tenant-context'

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TenantProvider>
          {children}
        </TenantProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }

// Custom render for components that need authenticated state
export const renderWithAuth = (
  ui: ReactElement,
  options?: {
    user?: {
      id: number
      email: string
      name: string
      role: string
      tenant_id: number
    }
    isAuthenticated?: boolean
  } & Omit<RenderOptions, 'wrapper'>
) => {
  const { user = mockUser, isAuthenticated = true, ...renderOptions } = options || {}

  const AuthenticatedProvider = ({ children }: { children: React.ReactNode }) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    })

    return (
      <QueryClientProvider client={queryClient}>
        <AuthProvider initialState={{ user: isAuthenticated ? user : null, isAuthenticated }}>
          <TenantProvider>
            {children}
          </TenantProvider>
        </AuthProvider>
      </QueryClientProvider>
    )
  }

  return render(ui, { wrapper: AuthenticatedProvider, ...renderOptions })
}

// Mock user data
export const mockUser = {
  id: 1,
  email: 'test@example.com',
  name: 'Test User',
  role: 'user',
  tenant_id: 1,
}

// Mock tenant data
export const mockTenant = {
  id: 1,
  name: 'Test Tenant',
  domain: 'test.signate.com',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

// Custom matcher for accessibility testing
export const toBeAccessible = async (container: HTMLElement) => {
  const { default: axe } = await import('jest-axe')
  const results = await axe(container)

  return {
    pass: results.violations.length === 0,
    message: () => {
      if (results.violations.length === 0) {
        return 'Expected element to have accessibility violations'
      }

      const violations = results.violations
        .map(violation => `${violation.help} (${violation.impact})`)
        .join('\\n')

      return `Expected element to be accessible, but found violations:\\n${violations}`
    },
  }
}

// Extend Jest matchers
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeAccessible(): Promise<R>
    }
  }
}

// Create query client for testing
export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })

// Utility to wait for loading states
export const waitForLoadingToFinish = () =>
  new Promise(resolve => setTimeout(resolve, 0))

// Mock API responses
export const mockApiResponse = <T>(data: T, delay = 0) =>
  new Promise<T>(resolve => setTimeout(() => resolve(data), delay))

export const mockApiError = (message: string, status = 400, delay = 0) =>
  new Promise((_, reject) =>
    setTimeout(() => reject(new Error(message)), delay)
  )