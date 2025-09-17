import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { apiClient } from '@/lib/api';
import { AuthState, User, Tenant, LoginForm, RegisterForm } from '@/types';

interface AuthActions {
  login: (credentials: LoginForm) => Promise<void>;
  register: (userData: RegisterForm) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  getProfile: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  updatePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

type AuthStore = AuthState & AuthActions;

const initialState: AuthState = {
  user: null,
  tenant: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      login: async (credentials: LoginForm) => {
        try {
          set({ isLoading: true, error: null });

          const response = await apiClient.login(credentials.email, credentials.password);

          // Store tokens in cookies via apiClient
          apiClient.setTokens(response.data.accessToken, response.data.refreshToken);

          set({
            user: response.data.user,
            tenant: response.data.tenant,
            token: response.data.accessToken,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Login failed',
          });
          throw error;
        }
      },

      register: async (userData: RegisterForm) => {
        try {
          set({ isLoading: true, error: null });

          const response = await apiClient.register({
            email: userData.email,
            password: userData.password,
            firstName: userData.firstName,
            lastName: userData.lastName,
            tenantName: userData.tenantName,
          });

          // Store tokens in cookies via apiClient
          apiClient.setTokens(response.data.accessToken, response.data.refreshToken);

          set({
            user: response.data.user,
            tenant: response.data.tenant,
            token: response.data.accessToken,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Registration failed',
          });
          throw error;
        }
      },

      logout: async () => {
        try {
          await apiClient.logout();
        } catch (error) {
          // Ignore logout errors and proceed with client-side cleanup
          console.error('Logout error:', error);
        } finally {
          set({
            ...initialState,
          });
        }
      },

      refreshAuth: async () => {
        try {
          set({ isLoading: true, error: null });
          await apiClient.getProfile();
          // Profile endpoint will trigger token refresh if needed via interceptor
          set({ isLoading: false });
        } catch (error: any) {
          set({
            ...initialState,
            error: error.message || 'Session refresh failed',
          });
          throw error;
        }
      },

      getProfile: async () => {
        try {
          set({ isLoading: true, error: null });

          const response = await apiClient.getProfile();

          set({
            user: response.data.user,
            tenant: response.data.tenant,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            ...initialState,
            error: error.message || 'Failed to load profile',
          });
          throw error;
        }
      },

      updateProfile: async (userData: Partial<User>) => {
        try {
          set({ isLoading: true, error: null });

          const { user } = get();
          if (!user) throw new Error('No user found');

          const response = await apiClient.put<User>(`/api/v3/users/${user.id}`, userData);

          set({
            user: response.data,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to update profile',
          });
          throw error;
        }
      },

      requestPasswordReset: async (email: string) => {
        try {
          set({ isLoading: true, error: null });

          await apiClient.requestPasswordReset(email);

          set({
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to request password reset',
          });
          throw error;
        }
      },

      resetPassword: async (token: string, newPassword: string) => {
        try {
          set({ isLoading: true, error: null });

          await apiClient.resetPassword(token, newPassword);

          set({
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to reset password',
          });
          throw error;
        }
      },

      updatePassword: async (currentPassword: string, newPassword: string) => {
        try {
          set({ isLoading: true, error: null });

          await apiClient.updatePassword(currentPassword, newPassword);

          set({
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to update password',
          });
          throw error;
        }
      },

      clearError: () => set({ error: null }),

      setLoading: (loading: boolean) => set({ isLoading: loading }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        tenant: state.tenant,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Hook to check if user has specific role
export const useHasRole = (requiredRole: string | string[]) => {
  const user = useAuthStore((state) => state.user);

  if (!user) return false;

  if (Array.isArray(requiredRole)) {
    return requiredRole.includes(user.role);
  }

  return user.role === requiredRole;
};

// Hook to check if user has admin privileges
export const useIsAdmin = () => {
  return useHasRole('admin');
};

// Hook to check if user has manager or admin privileges
export const useCanManage = () => {
  return useHasRole(['admin', 'manager']);
};