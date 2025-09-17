import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  LoginRequest,
  LoginResponse,
  User,
  Session,
  RefreshTokenResponse,
  ApiError,
  ApiErrorCode
} from '../types/api';
import { apiClient } from '../api/client';
import { useAuthStore, useAuth, useAuthActions, usePermissions } from '../stores/auth';
import { queryKeys, invalidateQueries } from '../lib/react-query';
import { webSocketClient } from '../utils/websocket';

// Authentication hooks using React Query + Zustand

export const useLogin = () => {
  const { login: storeLogin } = useAuthActions();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: LoginRequest): Promise<LoginResponse> => {
      return await storeLogin(credentials);
    },
    onSuccess: (data) => {
      // Invalidate and refetch relevant queries
      invalidateQueries.profile();
      invalidateQueries.tenant();

      // Connect WebSocket after successful login
      webSocketClient.updateAuth(data.access_token, data.tenant?.slug);
      webSocketClient.connect().catch(console.error);

      // Prefetch some data
      queryClient.prefetchQuery({
        queryKey: queryKeys.assets.list({}),
        queryFn: () => apiClient.get('/assets/'),
      });
    },
    onError: (error) => {
      console.error('Login failed:', error);
    },
  });
};

export const useLogout = () => {
  const { logout: storeLogout } = useAuthActions();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await storeLogout();
    },
    onSuccess: () => {
      // Clear all cached data
      queryClient.clear();

      // Disconnect WebSocket
      webSocketClient.disconnect();

      // Redirect to login page
      window.location.href = '/login';
    },
    onError: (error) => {
      console.error('Logout failed:', error);
      // Force clear even if logout API call failed
      queryClient.clear();
      webSocketClient.disconnect();
    },
  });
};

export const useRefreshAuth = () => {
  const { refreshAuth } = useAuthActions();

  return useMutation({
    mutationFn: async (): Promise<RefreshTokenResponse> => {
      await refreshAuth();
      return {} as RefreshTokenResponse; // Store handles the actual refresh
    },
    onSuccess: () => {
      invalidateQueries.profile();
    },
    onError: (error) => {
      console.error('Token refresh failed:', error);
      // Will be handled by auth store (redirect to login)
    },
  });
};

export const useProfile = () => {
  const { user, isAuthenticated } = useAuth();

  return useQuery({
    queryKey: queryKeys.auth.profile(),
    queryFn: async (): Promise<User> => {
      return apiClient.get('/auth/profile/');
    },
    enabled: isAuthenticated,
    initialData: user || undefined,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useUpdateProfile = () => {
  const { updateProfile } = useAuthActions();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: Partial<User>): Promise<User> => {
      return await updateProfile(updates);
    },
    onSuccess: (updatedUser) => {
      // Update cached profile data
      queryClient.setQueryData(queryKeys.auth.profile(), updatedUser);

      toast.success('Profile updated successfully!');
    },
    onError: (error) => {
      console.error('Profile update failed:', error);
    },
  });
};

export const useChangePassword = () => {
  return useMutation({
    mutationFn: async (data: {
      current_password: string;
      new_password: string;
      new_password_confirm: string;
    }) => {
      return apiClient.post('/auth/change-password/', data);
    },
    onSuccess: () => {
      toast.success('Password changed successfully!');
    },
    onError: (error) => {
      console.error('Password change failed:', error);
    },
  });
};

export const useSessions = () => {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: queryKeys.auth.sessions(),
    queryFn: async (): Promise<{ sessions: Session[] }> => {
      return apiClient.get('/auth/sessions/');
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useRevokeSession = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: string) => {
      return apiClient.delete(`/auth/sessions/?session_id=${sessionId}`);
    },
    onSuccess: () => {
      // Refresh sessions list
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.sessions() });
      toast.success('Session revoked successfully!');
    },
    onError: (error) => {
      console.error('Session revocation failed:', error);
    },
  });
};

// Custom hook for authentication state management
export const useAuthState = () => {
  const auth = useAuth();
  const actions = useAuthActions();
  const permissions = usePermissions();

  // Initialize auth on mount
  useEffect(() => {
    if (!auth.isInitialized) {
      actions.initializeAuth();
    }
  }, [auth.isInitialized, actions]);

  // Auto-refresh token when it's about to expire
  useEffect(() => {
    const checkTokenExpiry = () => {
      const store = useAuthStore.getState();
      const { tokenExpiresAt, isAuthenticated } = store;

      if (isAuthenticated && tokenExpiresAt) {
        const timeUntilExpiry = tokenExpiresAt - Date.now();
        const shouldRefresh = timeUntilExpiry < 5 * 60 * 1000; // 5 minutes

        if (shouldRefresh) {
          actions.refreshAuth().catch(console.error);
        }
      }
    };

    const interval = setInterval(checkTokenExpiry, 60 * 1000); // Check every minute
    return () => clearInterval(interval);
  }, [actions]);

  // Update WebSocket auth when tokens change
  useEffect(() => {
    const store = useAuthStore.getState();
    if (store.accessToken && store.currentTenant) {
      webSocketClient.updateAuth(store.accessToken, store.currentTenant.slug);
    }
  }, [auth.user, auth.tenant]);

  return {
    ...auth,
    ...actions,
    ...permissions,
  };
};

// Hook for protecting routes
export const useAuthGuard = (
  requiredPermission?: string,
  requiredRole?: string,
  redirectTo = '/login'
) => {
  const { isAuthenticated, isInitialized } = useAuth();
  const { hasPermission, hasRole } = usePermissions();

  useEffect(() => {
    if (!isInitialized) return;

    if (!isAuthenticated) {
      window.location.href = redirectTo;
      return;
    }

    if (requiredPermission && !hasPermission(requiredPermission)) {
      toast.error('You do not have permission to access this page');
      window.location.href = '/dashboard';
      return;
    }

    if (requiredRole && !hasRole(requiredRole)) {
      toast.error('You do not have the required role to access this page');
      window.location.href = '/dashboard';
      return;
    }
  }, [
    isAuthenticated,
    isInitialized,
    requiredPermission,
    requiredRole,
    redirectTo,
    hasPermission,
    hasRole,
  ]);

  return {
    isAuthenticated,
    isInitialized,
    isAllowed: isAuthenticated &&
               (!requiredPermission || hasPermission(requiredPermission)) &&
               (!requiredRole || hasRole(requiredRole)),
  };
};

// Hook for handling authentication errors globally
export const useAuthErrorHandler = () => {
  const { logout } = useAuthActions();

  useEffect(() => {
    const handleAuthError = (error: ApiError) => {
      if (error.code === ApiErrorCode.UNAUTHORIZED) {
        // Token might be expired or invalid
        logout();
      }
    };

    // This would be called by the API client when auth errors occur
    // You might want to set up a global error handler or event system

    return () => {
      // Cleanup if needed
    };
  }, [logout]);
};

// Hook for tenant switching
export const useTenantSwitch = () => {
  const { switchTenant } = useAuthActions();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (tenantSlug: string) => {
      await switchTenant(tenantSlug);
    },
    onSuccess: () => {
      // Clear all cached data since we're switching context
      queryClient.clear();

      // Will be redirected to login by the auth store
    },
    onError: (error) => {
      console.error('Tenant switch failed:', error);
    },
  });
};

// Export all hooks for easy importing
export {
  useAuth,
  useAuthActions,
  usePermissions,
};