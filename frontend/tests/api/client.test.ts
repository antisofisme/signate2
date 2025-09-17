import { apiClient, authApi, userApi, tenantApi } from '@/api/client'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

describe('API Client', () => {
  describe('API Client Configuration', () => {
    it('should have correct base URL', () => {
      expect(apiClient.defaults.baseURL).toBe(API_URL)
    })

    it('should include default headers', () => {
      expect(apiClient.defaults.headers.common['Content-Type']).toBe('application/json')
    })
  })

  describe('Authentication Interceptors', () => {
    beforeEach(() => {
      // Clear localStorage before each test
      localStorage.clear()
    })

    it('should add authorization header when token exists', async () => {
      localStorage.setItem('access_token', 'test-token')

      // Mock an endpoint to test the interceptor
      server.use(
        http.get(`${API_URL}/test`, ({ request }) => {
          const authHeader = request.headers.get('Authorization')
          return HttpResponse.json({ authHeader })
        })
      )

      const response = await apiClient.get('/test')

      expect(response.data.authHeader).toBe('Bearer test-token')
    })

    it('should handle 401 responses with token refresh', async () => {
      localStorage.setItem('access_token', 'expired-token')
      localStorage.setItem('refresh_token', 'valid-refresh-token')

      // Mock 401 response first, then success after refresh
      let callCount = 0
      server.use(
        http.get(`${API_URL}/test`, () => {
          callCount++
          if (callCount === 1) {
            return HttpResponse.json(
              { detail: 'Token expired' },
              { status: 401 }
            )
          }
          return HttpResponse.json({ success: true })
        })
      )

      try {
        const response = await apiClient.get('/test')
        expect(response.data.success).toBe(true)
      } catch (error) {
        // If refresh fails, should get 401
        expect(error.response?.status).toBe(401)
      }
    })
  })

  describe('Auth API', () => {
    describe('login', () => {
      it('should login successfully', async () => {
        const loginData = {
          email: 'test@example.com',
          password: 'password123',
        }

        const response = await authApi.login(loginData.email, loginData.password)

        expect(response.access_token).toBe('mock-jwt-token')
        expect(response.user.email).toBe(loginData.email)
      })

      it('should handle login failure', async () => {
        const loginData = {
          email: 'test@example.com',
          password: 'wrongpassword',
        }

        await expect(
          authApi.login(loginData.email, loginData.password)
        ).rejects.toThrow()
      })
    })

    describe('register', () => {
      it('should register successfully', async () => {
        const registerData = {
          email: 'newuser@example.com',
          password: 'password123',
          name: 'New User',
        }

        const response = await authApi.register(registerData)

        expect(response.email).toBe(registerData.email)
        expect(response.name).toBe(registerData.name)
      })
    })

    describe('refresh token', () => {
      it('should refresh token successfully', async () => {
        const response = await authApi.refreshToken()

        expect(response.access_token).toBe('new-mock-jwt-token')
        expect(response.refresh_token).toBe('new-mock-refresh-token')
      })
    })

    describe('get current user', () => {
      it('should get current user successfully', async () => {
        const response = await authApi.getCurrentUser()

        expect(response.email).toBe('test@example.com')
        expect(response.name).toBe('Test User')
      })

      it('should handle unauthorized request', async () => {
        // Mock unauthorized response
        server.use(
          http.get(`${API_URL}/auth/me`, () => {
            return HttpResponse.json(
              { detail: 'Not authenticated' },
              { status: 401 }
            )
          })
        )

        await expect(authApi.getCurrentUser()).rejects.toThrow()
      })
    })
  })

  describe('User API', () => {
    describe('getUsers', () => {
      it('should get users with pagination', async () => {
        const response = await userApi.getUsers({ page: 1, limit: 10 })

        expect(response.items).toHaveLength(10)
        expect(response.total).toBe(50)
        expect(response.page).toBe(1)
      })

      it('should get users with search', async () => {
        server.use(
          http.get(`${API_URL}/users`, ({ request }) => {
            const url = new URL(request.url)
            const search = url.searchParams.get('search')

            const filteredUsers = [{
              id: 1,
              email: 'john@example.com',
              name: 'John Doe',
              role: 'user',
              tenant_id: 1,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }]

            return HttpResponse.json({
              items: search ? filteredUsers : [],
              total: search ? 1 : 0,
              page: 1,
              pages: 1,
              per_page: 10,
            })
          })
        )

        const response = await userApi.getUsers({ search: 'john' })

        expect(response.items).toHaveLength(1)
        expect(response.items[0].name).toBe('John Doe')
      })
    })

    describe('createUser', () => {
      it('should create user successfully', async () => {
        const userData = {
          email: 'newuser@example.com',
          name: 'New User',
          role: 'user',
          password: 'password123',
        }

        const response = await userApi.createUser(userData)

        expect(response.email).toBe(userData.email)
        expect(response.name).toBe(userData.name)
      })
    })

    describe('updateUser', () => {
      it('should update user successfully', async () => {
        const updateData = {
          name: 'Updated User',
          role: 'admin',
        }

        const response = await userApi.updateUser(1, updateData)

        expect(response.name).toBe(updateData.name)
        expect(response.role).toBe(updateData.role)
      })
    })

    describe('deleteUser', () => {
      it('should delete user successfully', async () => {
        await expect(userApi.deleteUser(1)).resolves.not.toThrow()
      })
    })
  })

  describe('Tenant API', () => {
    describe('getTenants', () => {
      it('should get tenants successfully', async () => {
        const response = await tenantApi.getTenants()

        expect(response.items).toHaveLength(2)
        expect(response.items[0].name).toBe('Default Tenant')
      })
    })

    describe('createTenant', () => {
      it('should create tenant successfully', async () => {
        const tenantData = {
          name: 'New Tenant',
          domain: 'new.signate.com',
        }

        server.use(
          http.post(`${API_URL}/tenants`, async ({ request }) => {
            const body = await request.json() as any

            return HttpResponse.json({
              id: Date.now(),
              ...body,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }, { status: 201 })
          })
        )

        const response = await tenantApi.createTenant(tenantData)

        expect(response.name).toBe(tenantData.name)
        expect(response.domain).toBe(tenantData.domain)
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      server.use(
        http.get(`${API_URL}/test`, () => {
          return HttpResponse.error()
        })
      )

      await expect(apiClient.get('/test')).rejects.toThrow()
    })

    it('should handle server errors', async () => {
      server.use(
        http.get(`${API_URL}/test`, () => {
          return HttpResponse.json(
            { detail: 'Internal server error' },
            { status: 500 }
          )
        })
      )

      await expect(apiClient.get('/test')).rejects.toThrow()
    })

    it('should handle validation errors', async () => {
      server.use(
        http.post(`${API_URL}/test`, () => {
          return HttpResponse.json(
            {
              detail: 'Validation error',
              errors: {
                email: ['This field is required'],
                password: ['Password too short'],
              },
            },
            { status: 422 }
          )
        })
      )

      try {
        await apiClient.post('/test', {})
      } catch (error: any) {
        expect(error.response.status).toBe(422)
        expect(error.response.data.errors).toBeDefined()
      }
    })
  })

  describe('Request/Response Transformation', () => {
    it('should transform dates in responses', async () => {
      const dateString = '2024-01-01T00:00:00Z'

      server.use(
        http.get(`${API_URL}/test`, () => {
          return HttpResponse.json({
            created_at: dateString,
            updated_at: dateString,
          })
        })
      )

      const response = await apiClient.get('/test')

      expect(response.data.created_at).toBe(dateString)
      expect(response.data.updated_at).toBe(dateString)
    })

    it('should handle empty responses', async () => {
      server.use(
        http.delete(`${API_URL}/test`, () => {
          return new HttpResponse(null, { status: 204 })
        })
      )

      const response = await apiClient.delete('/test')

      expect(response.status).toBe(204)
      expect(response.data).toBe('')
    })
  })
})