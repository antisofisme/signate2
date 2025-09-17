import { http, HttpResponse } from 'msw'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const handlers = [
  // Authentication endpoints
  http.post(`${API_URL}/auth/login`, async ({ request }) => {
    const body = await request.json() as { email: string; password: string }

    if (body.email === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json({
        access_token: 'mock-jwt-token',
        refresh_token: 'mock-refresh-token',
        user: {
          id: 1,
          email: 'test@example.com',
          name: 'Test User',
          role: 'user',
          tenant_id: 1,
        },
      })
    }

    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    )
  }),

  http.post(`${API_URL}/auth/register`, async ({ request }) => {
    const body = await request.json() as any

    return HttpResponse.json({
      id: 1,
      email: body.email,
      name: body.name,
      role: 'user',
      tenant_id: 1,
    }, { status: 201 })
  }),

  http.post(`${API_URL}/auth/refresh`, () => {
    return HttpResponse.json({
      access_token: 'new-mock-jwt-token',
      refresh_token: 'new-mock-refresh-token',
    })
  }),

  http.get(`${API_URL}/auth/me`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    return HttpResponse.json({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      role: 'user',
      tenant_id: 1,
    })
  }),

  // User management endpoints
  http.get(`${API_URL}/users`, ({ request }) => {
    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1')
    const limit = parseInt(url.searchParams.get('limit') || '10')

    const users = Array.from({ length: 50 }, (_, i) => ({
      id: i + 1,
      email: `user${i + 1}@example.com`,
      name: `User ${i + 1}`,
      role: i % 3 === 0 ? 'admin' : 'user',
      tenant_id: Math.floor(i / 10) + 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }))

    const start = (page - 1) * limit
    const end = start + limit
    const paginatedUsers = users.slice(start, end)

    return HttpResponse.json({
      items: paginatedUsers,
      total: users.length,
      page,
      pages: Math.ceil(users.length / limit),
      per_page: limit,
    })
  }),

  http.post(`${API_URL}/users`, async ({ request }) => {
    const body = await request.json() as any

    return HttpResponse.json({
      id: Date.now(),
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }, { status: 201 })
  }),

  http.get(`${API_URL}/users/:id`, ({ params }) => {
    const id = parseInt(params.id as string)

    return HttpResponse.json({
      id,
      email: `user${id}@example.com`,
      name: `User ${id}`,
      role: 'user',
      tenant_id: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  }),

  http.put(`${API_URL}/users/:id`, async ({ params, request }) => {
    const id = parseInt(params.id as string)
    const body = await request.json() as any

    return HttpResponse.json({
      id,
      ...body,
      updated_at: new Date().toISOString(),
    })
  }),

  http.delete(`${API_URL}/users/:id`, ({ params }) => {
    return new HttpResponse(null, { status: 204 })
  }),

  // Tenant endpoints
  http.get(`${API_URL}/tenants`, () => {
    return HttpResponse.json({
      items: [
        {
          id: 1,
          name: 'Default Tenant',
          domain: 'default.signate.com',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 2,
          name: 'Enterprise Tenant',
          domain: 'enterprise.signate.com',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 2,
      page: 1,
      pages: 1,
      per_page: 10,
    })
  }),

  // Asset endpoints
  http.get(`${API_URL}/assets`, ({ request }) => {
    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1')
    const limit = parseInt(url.searchParams.get('limit') || '10')

    const assets = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      name: `Asset ${i + 1}`,
      type: ['image', 'video', 'document'][i % 3],
      size: Math.floor(Math.random() * 1000000),
      url: `https://example.com/assets/asset${i + 1}`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }))

    const start = (page - 1) * limit
    const end = start + limit
    const paginatedAssets = assets.slice(start, end)

    return HttpResponse.json({
      items: paginatedAssets,
      total: assets.length,
      page,
      pages: Math.ceil(assets.length / limit),
      per_page: limit,
    })
  }),

  http.post(`${API_URL}/assets/upload`, async ({ request }) => {
    return HttpResponse.json({
      id: Date.now(),
      name: 'uploaded-file.jpg',
      type: 'image',
      size: 1024000,
      url: 'https://example.com/assets/uploaded-file.jpg',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }, { status: 201 })
  }),

  // Dashboard statistics
  http.get(`${API_URL}/dashboard/stats`, () => {
    return HttpResponse.json({
      total_users: 1250,
      active_users: 892,
      total_assets: 3456,
      storage_used: '2.1TB',
      growth_rate: 12.5,
    })
  }),

  // Health check
  http.get(`${API_URL}/health`, () => {
    return HttpResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
    })
  }),
]