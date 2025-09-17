/**
 * Test data factories for generating consistent test data
 */

export interface User {
  id: number
  email: string
  name: string
  role: string
  tenant_id: number
  created_at: string
  updated_at: string
}

export interface Tenant {
  id: number
  name: string
  domain: string
  created_at: string
  updated_at: string
}

export interface Asset {
  id: number
  name: string
  type: string
  size: number
  url: string
  created_at: string
  updated_at: string
}

// User factory
export const userFactory = {
  build: (overrides: Partial<User> = {}): User => ({
    id: Math.floor(Math.random() * 1000),
    email: `user${Math.floor(Math.random() * 1000)}@example.com`,
    name: `Test User ${Math.floor(Math.random() * 100)}`,
    role: 'user',
    tenant_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  buildList: (count: number, overrides: Partial<User> = {}): User[] =>
    Array.from({ length: count }, (_, index) =>
      userFactory.build({ id: index + 1, ...overrides })
    ),

  admin: (overrides: Partial<User> = {}): User =>
    userFactory.build({ role: 'admin', ...overrides }),

  moderator: (overrides: Partial<User> = {}): User =>
    userFactory.build({ role: 'moderator', ...overrides }),
}

// Tenant factory
export const tenantFactory = {
  build: (overrides: Partial<Tenant> = {}): Tenant => ({
    id: Math.floor(Math.random() * 1000),
    name: `Test Tenant ${Math.floor(Math.random() * 100)}`,
    domain: `tenant${Math.floor(Math.random() * 1000)}.example.com`,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  buildList: (count: number, overrides: Partial<Tenant> = {}): Tenant[] =>
    Array.from({ length: count }, (_, index) =>
      tenantFactory.build({ id: index + 1, ...overrides })
    ),
}

// Asset factory
export const assetFactory = {
  build: (overrides: Partial<Asset> = {}): Asset => ({
    id: Math.floor(Math.random() * 1000),
    name: `test-asset-${Math.floor(Math.random() * 1000)}.jpg`,
    type: 'image',
    size: Math.floor(Math.random() * 1000000),
    url: `https://example.com/assets/asset-${Math.floor(Math.random() * 1000)}.jpg`,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  buildList: (count: number, overrides: Partial<Asset> = {}): Asset[] =>
    Array.from({ length: count }, (_, index) =>
      assetFactory.build({ id: index + 1, ...overrides })
    ),

  image: (overrides: Partial<Asset> = {}): Asset =>
    assetFactory.build({ type: 'image', ...overrides }),

  video: (overrides: Partial<Asset> = {}): Asset =>
    assetFactory.build({ type: 'video', ...overrides }),

  document: (overrides: Partial<Asset> = {}): Asset =>
    assetFactory.build({ type: 'document', ...overrides }),
}

// Pagination response factory
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pages: number
  per_page: number
}

export const paginatedResponseFactory = {
  build: <T>(
    items: T[],
    overrides: Partial<PaginatedResponse<T>> = {}
  ): PaginatedResponse<T> => ({
    items,
    total: items.length,
    page: 1,
    pages: Math.ceil(items.length / 10),
    per_page: 10,
    ...overrides,
  }),
}

// Auth response factory
export interface AuthResponse {
  access_token: string
  refresh_token: string
  user: User
}

export const authResponseFactory = {
  build: (overrides: Partial<AuthResponse> = {}): AuthResponse => ({
    access_token: 'mock-jwt-token',
    refresh_token: 'mock-refresh-token',
    user: userFactory.build(),
    ...overrides,
  }),
}

// Dashboard stats factory
export interface DashboardStats {
  total_users: number
  active_users: number
  total_assets: number
  storage_used: string
  growth_rate: number
}

export const dashboardStatsFactory = {
  build: (overrides: Partial<DashboardStats> = {}): DashboardStats => ({
    total_users: Math.floor(Math.random() * 10000),
    active_users: Math.floor(Math.random() * 5000),
    total_assets: Math.floor(Math.random() * 50000),
    storage_used: `${Math.floor(Math.random() * 100)}GB`,
    growth_rate: Math.floor(Math.random() * 50),
    ...overrides,
  }),
}

// Form data factories
export const loginFormFactory = {
  valid: () => ({
    email: 'test@example.com',
    password: 'password123',
  }),

  invalid: () => ({
    email: 'invalid-email',
    password: '123',
  }),

  empty: () => ({
    email: '',
    password: '',
  }),
}

export const registerFormFactory = {
  valid: () => ({
    name: 'Test User',
    email: 'newuser@example.com',
    password: 'password123',
    confirmPassword: 'password123',
  }),

  passwordMismatch: () => ({
    name: 'Test User',
    email: 'newuser@example.com',
    password: 'password123',
    confirmPassword: 'differentpassword',
  }),

  weakPassword: () => ({
    name: 'Test User',
    email: 'newuser@example.com',
    password: '123',
    confirmPassword: '123',
  }),
}

export const userFormFactory = {
  valid: () => ({
    name: 'New User',
    email: 'newuser@example.com',
    role: 'user',
    password: 'password123',
  }),

  admin: () => ({
    name: 'Admin User',
    email: 'admin@example.com',
    role: 'admin',
    password: 'password123',
  }),

  update: () => ({
    name: 'Updated User',
    role: 'moderator',
  }),
}

// Error response factory
export interface ErrorResponse {
  detail: string
  errors?: Record<string, string[]>
}

export const errorResponseFactory = {
  validation: (): ErrorResponse => ({
    detail: 'Validation error',
    errors: {
      email: ['This field is required'],
      password: ['Password is too short'],
    },
  }),

  unauthorized: (): ErrorResponse => ({
    detail: 'Not authenticated',
  }),

  forbidden: (): ErrorResponse => ({
    detail: 'Permission denied',
  }),

  notFound: (): ErrorResponse => ({
    detail: 'Resource not found',
  }),

  serverError: (): ErrorResponse => ({
    detail: 'Internal server error',
  }),
}

// Utility functions for test data
export const testUtils = {
  // Generate a unique email
  uniqueEmail: () => `test-${Date.now()}@example.com`,

  // Generate a random string
  randomString: (length = 10) =>
    Math.random().toString(36).substring(2, length + 2),

  // Generate a date range
  dateRange: (days = 30) => {
    const end = new Date()
    const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000)
    return { start: start.toISOString(), end: end.toISOString() }
  },

  // Generate file for upload testing
  mockFile: (name = 'test.jpg', type = 'image/jpeg', size = 1024) => {
    const file = new File(['test content'], name, { type })
    Object.defineProperty(file, 'size', { value: size })
    return file
  },
}