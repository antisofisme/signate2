/**
 * User Management Store
 * Zustand store for user, role, and tenant management
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient } from '@/lib/api';

export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  isActive: boolean;
  lastLogin: string | null;
  dateJoined: string;
  roles: Role[];
  tenants: Tenant[];
  avatar?: string;
  timezone?: string;
  language?: string;
  twoFactorEnabled: boolean;
}

export interface Role {
  id: string;
  name: string;
  codename: string;
  description: string;
  level: number;
  permissions: Permission[];
  userCount?: number;
  isSystemRole: boolean;
}

export interface Permission {
  id: string;
  name: string;
  codename: string;
  category: string;
  action: string;
  description: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  isActive: boolean;
  planType: string;
  storageUsed: number;
  storageLimit: number;
  userCount: number;
  deviceCount: number;
  settings: Record<string, any>;
}

export interface UserStats {
  totalUsers: number;
  activeUsers: number;
  newUsersThisMonth: number;
  activeUsersChange: number;
  totalRoles: number;
  tenantUsage: string;
}

export interface ActivityLogEntry {
  id: string;
  user: string;
  action: string;
  description: string;
  ipAddress: string;
  userAgent: string;
  timestamp: string;
  metadata: Record<string, any>;
}

interface UserStore {
  // State
  users: User[];
  roles: Role[];
  permissions: Permission[];
  currentTenant: Tenant | null;
  stats: UserStats | null;
  activityLog: ActivityLogEntry[];
  loading: boolean;
  error: string | null;

  // User Management
  fetchUsers: () => Promise<void>;
  createUser: (userData: Partial<User>) => Promise<User>;
  updateUser: (id: string, userData: Partial<User>) => Promise<User>;
  deleteUser: (id: string) => Promise<void>;
  toggleUserStatus: (id: string) => Promise<void>;
  resetUserPassword: (id: string) => Promise<void>;

  // Role Management
  fetchRoles: () => Promise<void>;
  createRole: (roleData: Partial<Role>) => Promise<Role>;
  updateRole: (id: string, roleData: Partial<Role>) => Promise<Role>;
  deleteRole: (id: string) => Promise<void>;
  assignRole: (userId: string, roleId: string) => Promise<void>;
  removeRole: (userId: string, roleId: string) => Promise<void>;

  // Permission Management
  fetchPermissions: () => Promise<void>;
  assignPermission: (roleId: string, permissionId: string) => Promise<void>;
  removePermission: (roleId: string, permissionId: string) => Promise<void>;

  // Tenant Management
  fetchTenantSettings: () => Promise<void>;
  updateTenantSettings: (settings: Record<string, any>) => Promise<void>;

  // Statistics and Monitoring
  fetchUserStats: () => Promise<void>;
  fetchActivityLog: (filters?: Record<string, any>) => Promise<void>;

  // Utility
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

export const useUserStore = create<UserStore>()(
  persist(
    (set, get) => ({
      // Initial state
      users: [],
      roles: [],
      permissions: [],
      currentTenant: null,
      stats: null,
      activityLog: [],
      loading: false,
      error: null,

      // User Management
      fetchUsers: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.get('/api/v3/users/');
          set({ users: response.data.results || response.data });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to fetch users' });
        } finally {
          set({ loading: false });
        }
      },

      createUser: async (userData) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.post('/api/v3/users/', userData);
          const newUser = response.data;
          set(state => ({
            users: [...state.users, newUser],
            loading: false
          }));
          return newUser;
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to create user';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      updateUser: async (id, userData) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.patch(`/api/v3/users/${id}/`, userData);
          const updatedUser = response.data;
          set(state => ({
            users: state.users.map(user =>
              user.id === id ? updatedUser : user
            ),
            loading: false
          }));
          return updatedUser;
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to update user';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      deleteUser: async (id) => {
        set({ loading: true, error: null });
        try {
          await apiClient.delete(`/api/v3/users/${id}/`);
          set(state => ({
            users: state.users.filter(user => user.id !== id),
            loading: false
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to delete user';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      toggleUserStatus: async (id) => {
        const user = get().users.find(u => u.id === id);
        if (!user) return;

        try {
          await get().updateUser(id, { isActive: !user.isActive });
        } catch (error) {
          throw error;
        }
      },

      resetUserPassword: async (id) => {
        set({ loading: true, error: null });
        try {
          await apiClient.post(`/api/v3/users/${id}/reset-password/`);
          set({ loading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to reset password';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      // Role Management
      fetchRoles: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.get('/api/v3/roles/');
          set({ roles: response.data.results || response.data });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to fetch roles' });
        } finally {
          set({ loading: false });
        }
      },

      createRole: async (roleData) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.post('/api/v3/roles/', roleData);
          const newRole = response.data;
          set(state => ({
            roles: [...state.roles, newRole],
            loading: false
          }));
          return newRole;
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to create role';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      updateRole: async (id, roleData) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.patch(`/api/v3/roles/${id}/`, roleData);
          const updatedRole = response.data;
          set(state => ({
            roles: state.roles.map(role =>
              role.id === id ? updatedRole : role
            ),
            loading: false
          }));
          return updatedRole;
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to update role';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      deleteRole: async (id) => {
        set({ loading: true, error: null });
        try {
          await apiClient.delete(`/api/v3/roles/${id}/`);
          set(state => ({
            roles: state.roles.filter(role => role.id !== id),
            loading: false
          }));
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to delete role';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      assignRole: async (userId, roleId) => {
        set({ loading: true, error: null });
        try {
          await apiClient.post(`/api/v3/users/${userId}/assign-role/`, { roleId });
          // Refresh users to get updated role assignments
          await get().fetchUsers();
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to assign role';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      removeRole: async (userId, roleId) => {
        set({ loading: true, error: null });
        try {
          await apiClient.post(`/api/v3/users/${userId}/remove-role/`, { roleId });
          // Refresh users to get updated role assignments
          await get().fetchUsers();
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to remove role';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      // Permission Management
      fetchPermissions: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.get('/api/v3/permissions/');
          set({ permissions: response.data.results || response.data });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to fetch permissions' });
        } finally {
          set({ loading: false });
        }
      },

      assignPermission: async (roleId, permissionId) => {
        set({ loading: true, error: null });
        try {
          await apiClient.post(`/api/v3/roles/${roleId}/assign-permission/`, { permissionId });
          // Refresh roles to get updated permissions
          await get().fetchRoles();
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to assign permission';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      removePermission: async (roleId, permissionId) => {
        set({ loading: true, error: null });
        try {
          await apiClient.post(`/api/v3/roles/${roleId}/remove-permission/`, { permissionId });
          // Refresh roles to get updated permissions
          await get().fetchRoles();
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to remove permission';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      // Tenant Management
      fetchTenantSettings: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.get('/api/v3/tenant/settings/');
          set({ currentTenant: response.data });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to fetch tenant settings' });
        } finally {
          set({ loading: false });
        }
      },

      updateTenantSettings: async (settings) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.patch('/api/v3/tenant/settings/', { settings });
          set({ currentTenant: response.data, loading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to update tenant settings';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      // Statistics and Monitoring
      fetchUserStats: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.get('/api/v3/users/stats/');
          set({ stats: response.data });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to fetch user stats' });
        } finally {
          set({ loading: false });
        }
      },

      fetchActivityLog: async (filters = {}) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.get('/api/v3/users/activity-log/', { params: filters });
          set({ activityLog: response.data.results || response.data });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to fetch activity log' });
        } finally {
          set({ loading: false });
        }
      },

      // Utility
      clearError: () => set({ error: null }),
      setLoading: (loading) => set({ loading }),
    }),
    {
      name: 'user-store',
      partialize: (state) => ({
        currentTenant: state.currentTenant,
      }),
    }
  )
);