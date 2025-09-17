import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { devtools } from 'zustand/middleware';
import { toast } from 'react-hot-toast';
import {
  User,
  Tenant,
  LoginRequest,
  LoginResponse,
  TenantMembership,
  RefreshTokenResponse,
  ApiError,
  ApiErrorCode
} from '../types/api';
import { apiClient } from '../api/client';
import { getStorageItem, setStorageItem, removeStorageItem } from '../utils/storage';

export interface AuthState {
  // State
  user: User | null;
  currentTenant: Tenant | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  loginAttempts: number;
  lastLoginAttempt: number | null;

  // Auth tokens (handled by persistence)
  accessToken: string | null;
  refreshToken: string | null;
  tokenExpiresAt: number | null;

  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  switchTenant: (tenantSlug: string) => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;
  checkAuthStatus: () => Promise<void>;
  initializeAuth: () => Promise<void>;
  resetLoginAttempts: () => void;

  // Internal methods
  setUser: (user: User | null) => void;
  setTenant: (tenant: Tenant | null) => void;
  setTokens: (accessToken: string, refreshToken: string, expiresIn: number) => void;
  clearAuth: () => void;
}

const MAX_LOGIN_ATTEMPTS = 5;
const LOGIN_ATTEMPT_WINDOW = 15 * 60 * 1000; // 15 minutes

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        user: null,
        currentTenant: null,
        isAuthenticated: false,
        isLoading: false,
        isInitialized: false,
        loginAttempts: 0,
        lastLoginAttempt: null,
        accessToken: null,
        refreshToken: null,
        tokenExpiresAt: null,

        // Initialize authentication state
        initializeAuth: async () => {
          const state = get();
          if (state.isInitialized) return;

          set({ isLoading: true });

          try {
            // Check if we have stored tokens
            const accessToken = getStorageItem('access_token');
            const refreshToken = getStorageItem('refresh_token');

            if (accessToken && refreshToken) {
              // Validate current tokens and refresh if needed
              await state.checkAuthStatus();
            } else {
              // No tokens found, clear auth state
              state.clearAuth();
            }
          } catch (error) {
            console.error('Auth initialization failed:', error);
            state.clearAuth();
          } finally {
            set({ isLoading: false, isInitialized: true });
          }
        },

        // Check current authentication status
        checkAuthStatus: async () => {
          const state = get();
          const accessToken = state.accessToken || getStorageItem('access_token');

          if (!accessToken) {
            state.clearAuth();
            return;
          }

          try {
            // Try to get current user profile
            const user = await apiClient.get<User>('/auth/profile/');

            // If successful, user is authenticated
            set({
              user,
              isAuthenticated: true,
              currentTenant: user.current_tenant ? {
                id: user.current_tenant.tenant_id,
                name: user.current_tenant.tenant_name,
                slug: user.current_tenant.tenant_slug,
                is_active: true,
                subscription_tier: 'pro', // This should come from the API
                created_at: user.current_tenant.joined_at,
                settings: { timezone: 'UTC', date_format: 'YYYY-MM-DD' },
                user_count: 0,
                asset_count: 0,
                quota_usage: {
                  api_calls_this_month: 0,
                  storage_used_mb: 0,
                  users_count: 0,
                  assets_count: 0
                }
              } as Tenant : null
            });

            // Store current tenant slug
            if (user.current_tenant) {
              setStorageItem('current_tenant_slug', user.current_tenant.tenant_slug);
            }

          } catch (error) {
            console.error('Auth status check failed:', error);

            // If it's an auth error, try to refresh the token
            if (error instanceof ApiError && error.code === ApiErrorCode.UNAUTHORIZED) {
              try {
                await state.refreshAuth();
              } catch (refreshError) {
                console.error('Token refresh failed:', refreshError);
                state.clearAuth();
              }
            } else {
              state.clearAuth();
            }
          }
        },

        // Login user
        login: async (credentials: LoginRequest) => {
          const state = get();

          // Check rate limiting
          const now = Date.now();
          if (
            state.loginAttempts >= MAX_LOGIN_ATTEMPTS &&
            state.lastLoginAttempt &&
            now - state.lastLoginAttempt < LOGIN_ATTEMPT_WINDOW
          ) {
            const remainingTime = Math.ceil((LOGIN_ATTEMPT_WINDOW - (now - state.lastLoginAttempt)) / 60000);
            throw new ApiError(
              ApiErrorCode.RATE_LIMITED,
              `Too many login attempts. Please try again in ${remainingTime} minutes.`
            );
          }

          set({ isLoading: true });

          try {
            // Add device info to login request
            const deviceInfo = {
              user_agent: navigator.userAgent,
              platform: navigator.platform,
            };

            const response = await apiClient.post<LoginResponse>('/auth/login/', {
              ...credentials,
              device_info: deviceInfo,
            });

            // Store tokens and user data
            state.setTokens(
              response.access_token,
              response.refresh_token,
              response.expires_in
            );

            set({
              user: response.user,
              currentTenant: response.tenant || null,
              isAuthenticated: true,
              loginAttempts: 0,
              lastLoginAttempt: null,
            });

            // Store additional data
            setStorageItem('current_user', JSON.stringify(response.user));
            if (response.tenant) {
              setStorageItem('current_tenant', JSON.stringify(response.tenant));
              setStorageItem('current_tenant_slug', response.tenant.slug);
            }

            toast.success('Successfully logged in!');

          } catch (error) {
            console.error('Login failed:', error);

            // Increment login attempts
            set({
              loginAttempts: state.loginAttempts + 1,
              lastLoginAttempt: now,
            });

            if (error instanceof ApiError) {
              toast.error(error.message);
            } else {
              toast.error('Login failed. Please try again.');
            }

            throw error;
          } finally {
            set({ isLoading: false });
          }
        },

        // Refresh authentication tokens
        refreshAuth: async () => {
          const state = get();
          const refreshToken = state.refreshToken || getStorageItem('refresh_token');

          if (!refreshToken) {
            throw new ApiError(ApiErrorCode.UNAUTHORIZED, 'No refresh token available');
          }

          try {
            const response = await apiClient.post<RefreshTokenResponse>('/auth/refresh/', {
              refresh_token: refreshToken,
              device_info: {
                user_agent: navigator.userAgent,
                platform: navigator.platform,
              },
            });

            state.setTokens(
              response.access_token,
              response.refresh_token,
              response.expires_in
            );

            // Verify the refreshed authentication
            await state.checkAuthStatus();

          } catch (error) {
            console.error('Token refresh failed:', error);
            state.clearAuth();
            throw error;
          }
        },

        // Logout user
        logout: async () => {
          const state = get();
          set({ isLoading: true });

          try {
            // Attempt to revoke tokens on server
            if (state.refreshToken) {
              await apiClient.post('/auth/logout/', {
                refresh_token: state.refreshToken,
                revoke_all_sessions: false,
              });
            }
          } catch (error) {
            console.error('Logout API call failed:', error);
            // Continue with client-side logout even if server call fails
          } finally {
            state.clearAuth();
            set({ isLoading: false });
            toast.success('Successfully logged out!');
          }
        },

        // Switch tenant context
        switchTenant: async (tenantSlug: string) => {
          const state = get();
          set({ isLoading: true });

          try {
            // Check if user has access to this tenant
            const user = state.user;
            if (!user) {
              throw new ApiError(ApiErrorCode.UNAUTHORIZED, 'User not authenticated');
            }

            const targetTenant = user.tenant_memberships.find(
              membership => membership.tenant_slug === tenantSlug
            );

            if (!targetTenant) {
              throw new ApiError(
                ApiErrorCode.PERMISSION_DENIED,
                'You do not have access to this tenant'
              );
            }

            // Logout and login with new tenant context
            await state.logout();

            // Note: In a real implementation, you might want to store the user's
            // credentials temporarily or implement a different tenant switching mechanism
            toast.info('Please log in again to switch tenants.');

          } catch (error) {
            console.error('Tenant switch failed:', error);
            if (error instanceof ApiError) {
              toast.error(error.message);
            } else {
              toast.error('Failed to switch tenant');
            }
            throw error;
          } finally {
            set({ isLoading: false });
          }
        },

        // Update user profile
        updateProfile: async (updates: Partial<User>) => {
          const state = get();
          set({ isLoading: true });

          try {
            const updatedUser = await apiClient.patch<User>('/auth/profile/', updates);

            set({ user: updatedUser });
            setStorageItem('current_user', JSON.stringify(updatedUser));

            toast.success('Profile updated successfully!');
          } catch (error) {
            console.error('Profile update failed:', error);
            if (error instanceof ApiError) {
              toast.error(error.message);
            } else {
              toast.error('Failed to update profile');
            }
            throw error;
          } finally {
            set({ isLoading: false });
          }
        },

        // Reset login attempts (called after successful operations)
        resetLoginAttempts: () => {
          set({ loginAttempts: 0, lastLoginAttempt: null });
        },

        // Internal state setters
        setUser: (user: User | null) => set({ user }),

        setTenant: (tenant: Tenant | null) => set({ currentTenant: tenant }),

        setTokens: (accessToken: string, refreshToken: string, expiresIn: number) => {
          const expiresAt = Date.now() + (expiresIn * 1000);

          set({
            accessToken,
            refreshToken,
            tokenExpiresAt: expiresAt,
          });

          // Store in localStorage for persistence
          setStorageItem('access_token', accessToken);
          setStorageItem('refresh_token', refreshToken);
          setStorageItem('token_expires_at', expiresAt.toString());
        },

        clearAuth: () => {
          set({
            user: null,
            currentTenant: null,
            isAuthenticated: false,
            accessToken: null,
            refreshToken: null,
            tokenExpiresAt: null,
          });

          // Clear stored data
          removeStorageItem('access_token');
          removeStorageItem('refresh_token');
          removeStorageItem('token_expires_at');
          removeStorageItem('current_user');
          removeStorageItem('current_tenant');
          removeStorageItem('current_tenant_slug');
        },
      }),
      {
        name: 'auth-store',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          // Only persist essential data
          accessToken: state.accessToken,
          refreshToken: state.refreshToken,
          tokenExpiresAt: state.tokenExpiresAt,
          loginAttempts: state.loginAttempts,
          lastLoginAttempt: state.lastLoginAttempt,
        }),
        onRehydrateStorage: () => (state) => {
          // Initialize auth after rehydration
          if (state) {
            state.initializeAuth();
          }
        },
      }
    ),
    {
      name: 'auth-store',
      enabled: process.env.NODE_ENV === 'development',
    }
  )
);

// Selectors for easy access to auth state
export const useAuth = () => {
  const store = useAuthStore();
  return {
    user: store.user,
    tenant: store.currentTenant,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    isInitialized: store.isInitialized,
  };
};

export const useAuthActions = () => {
  const store = useAuthStore();
  return {
    login: store.login,
    logout: store.logout,
    refreshAuth: store.refreshAuth,
    switchTenant: store.switchTenant,
    updateProfile: store.updateProfile,
    checkAuthStatus: store.checkAuthStatus,
    initializeAuth: store.initializeAuth,
    resetLoginAttempts: store.resetLoginAttempts,
  };
};

// Hook for checking specific permissions
export const usePermissions = () => {
  const { user, tenant } = useAuth();

  const hasPermission = (permission: string): boolean => {
    if (!user || !tenant) return false;

    // Get user's role in current tenant
    const membership = user.tenant_memberships.find(
      m => m.tenant_slug === tenant.slug
    );

    if (!membership) return false;

    // Define role-based permissions
    const rolePermissions: Record<string, string[]> = {
      owner: ['*'], // All permissions
      admin: [
        'tenant.manage', 'user.manage', 'asset.manage', 'layout.manage',
        'settings.manage', 'analytics.view'
      ],
      manager: [
        'asset.manage', 'layout.manage', 'user.invite', 'analytics.view'
      ],
      editor: [
        'asset.create', 'asset.edit', 'layout.create', 'layout.edit'
      ],
      viewer: [
        'asset.view', 'layout.view'
      ],
      guest: [
        'asset.view'
      ],
    };

    const userPermissions = rolePermissions[membership.role] || [];

    // Check for wildcard permission (owner)
    if (userPermissions.includes('*')) return true;

    // Check for specific permission
    return userPermissions.includes(permission);
  };

  const hasRole = (role: string): boolean => {
    if (!user || !tenant) return false;

    const membership = user.tenant_memberships.find(
      m => m.tenant_slug === tenant.slug
    );

    return membership?.role === role;
  };

  const hasAnyRole = (roles: string[]): boolean => {
    if (!user || !tenant) return false;

    const membership = user.tenant_memberships.find(
      m => m.tenant_slug === tenant.slug
    );

    return membership ? roles.includes(membership.role) : false;
  };

  return {
    hasPermission,
    hasRole,
    hasAnyRole,
  };
};

// Auto-refresh token when it's about to expire
let refreshTimer: NodeJS.Timeout | null = null;

useAuthStore.subscribe((state) => {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }

  if (state.tokenExpiresAt && state.isAuthenticated) {
    const timeUntilExpiry = state.tokenExpiresAt - Date.now();
    const refreshTime = timeUntilExpiry - (5 * 60 * 1000); // Refresh 5 minutes before expiry

    if (refreshTime > 0) {
      refreshTimer = setTimeout(() => {
        state.refreshAuth().catch(console.error);
      }, refreshTime);
    }
  }
});

export default useAuthStore;