/**
 * Notification Store
 * Zustand store for notifications, alerts, and real-time updates
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient } from '@/lib/api';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
  actionText?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  metadata?: Record<string, any>;
}

export interface Alert {
  id: string;
  type: 'device' | 'system' | 'security' | 'performance';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  status: 'active' | 'acknowledged' | 'resolved';
  deviceId?: string;
  deviceName?: string;
  timestamp: string;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  metadata?: Record<string, any>;
}

export interface NotificationSettings {
  emailNotifications: boolean;
  smsNotifications: boolean;
  pushNotifications: boolean;
  slackNotifications: boolean;
  notificationTypes: {
    deviceOffline: boolean;
    deviceWarning: boolean;
    systemAlerts: boolean;
    securityAlerts: boolean;
    performanceAlerts: boolean;
    contentUpdates: boolean;
    userActivity: boolean;
  };
  quietHours: {
    enabled: boolean;
    startTime: string;
    endTime: string;
  };
  alertThresholds: {
    deviceOfflineMinutes: number;
    cpuUsagePercent: number;
    memoryUsagePercent: number;
    storageUsagePercent: number;
  };
}

interface NotificationStore {
  // State
  notifications: Notification[];
  alerts: Alert[];
  settings: NotificationSettings | null;
  unreadCount: number;
  loading: boolean;
  error: string | null;

  // WebSocket connection
  connected: boolean;
  reconnecting: boolean;

  // Notification Management
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  deleteNotification: (id: string) => Promise<void>;
  clearAllNotifications: () => Promise<void>;

  // Alert Management
  fetchAlerts: () => Promise<void>;
  acknowledgeAlert: (id: string) => Promise<void>;
  resolveAlert: (id: string) => Promise<void>;
  createAlert: (alertData: Partial<Alert>) => Promise<Alert>;

  // Settings Management
  fetchSettings: () => Promise<void>;
  updateSettings: (settings: Partial<NotificationSettings>) => Promise<void>;
  testNotification: (type: string) => Promise<void>;

  // Real-time Updates
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  addNotification: (notification: Notification) => void;
  addAlert: (alert: Alert) => void;
  updateAlert: (id: string, updates: Partial<Alert>) => void;

  // Local Notifications
  showToast: (type: 'info' | 'success' | 'warning' | 'error', title: string, message: string) => void;

  // Utility
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

export const useNotificationStore = create<NotificationStore>()(
  persist(
    (set, get) => ({
      // Initial state
      notifications: [],
      alerts: [],
      settings: null,
      unreadCount: 0,
      loading: false,
      error: null,
      connected: false,
      reconnecting: false,

      // Notification Management
      fetchNotifications: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.get('/api/v3/notifications/');
          const notifications = response.data.results || response.data;
          set({
            notifications,
            unreadCount: notifications.filter((n: Notification) => !n.read).length,
            loading: false
          });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to fetch notifications' });
        } finally {
          set({ loading: false });
        }
      },

      markAsRead: async (id) => {
        try {
          await apiClient.patch(`/api/v3/notifications/${id}/`, { read: true });
          set(state => ({
            notifications: state.notifications.map(n =>
              n.id === id ? { ...n, read: true } : n
            ),
            unreadCount: Math.max(0, state.unreadCount - 1)
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to mark notification as read' });
        }
      },

      markAllAsRead: async () => {
        try {
          await apiClient.post('/api/v3/notifications/mark-all-read/');
          set(state => ({
            notifications: state.notifications.map(n => ({ ...n, read: true })),
            unreadCount: 0
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to mark all notifications as read' });
        }
      },

      deleteNotification: async (id) => {
        try {
          await apiClient.delete(`/api/v3/notifications/${id}/`);
          set(state => {
            const notification = state.notifications.find(n => n.id === id);
            const newNotifications = state.notifications.filter(n => n.id !== id);
            return {
              notifications: newNotifications,
              unreadCount: notification && !notification.read
                ? Math.max(0, state.unreadCount - 1)
                : state.unreadCount
            };
          });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to delete notification' });
        }
      },

      clearAllNotifications: async () => {
        try {
          await apiClient.delete('/api/v3/notifications/clear-all/');
          set({ notifications: [], unreadCount: 0 });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to clear notifications' });
        }
      },

      // Alert Management
      fetchAlerts: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.get('/api/v3/alerts/');
          set({ alerts: response.data.results || response.data });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to fetch alerts' });
        } finally {
          set({ loading: false });
        }
      },

      acknowledgeAlert: async (id) => {
        try {
          await apiClient.post(`/api/v3/alerts/${id}/acknowledge/`);
          set(state => ({
            alerts: state.alerts.map(a =>
              a.id === id
                ? {
                    ...a,
                    status: 'acknowledged',
                    acknowledgedAt: new Date().toISOString()
                  }
                : a
            )
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to acknowledge alert' });
        }
      },

      resolveAlert: async (id) => {
        try {
          await apiClient.post(`/api/v3/alerts/${id}/resolve/`);
          set(state => ({
            alerts: state.alerts.map(a =>
              a.id === id
                ? {
                    ...a,
                    status: 'resolved',
                    resolvedAt: new Date().toISOString()
                  }
                : a
            )
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to resolve alert' });
        }
      },

      createAlert: async (alertData) => {
        try {
          const response = await apiClient.post('/api/v3/alerts/', alertData);
          const newAlert = response.data;
          set(state => ({
            alerts: [newAlert, ...state.alerts]
          }));
          return newAlert;
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to create alert';
          set({ error: errorMessage });
          throw new Error(errorMessage);
        }
      },

      // Settings Management
      fetchSettings: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.get('/api/v3/notification-settings/');
          set({ settings: response.data });
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to fetch notification settings' });
        } finally {
          set({ loading: false });
        }
      },

      updateSettings: async (settingsUpdate) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.patch('/api/v3/notification-settings/', settingsUpdate);
          set({ settings: response.data, loading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to update settings';
          set({ error: errorMessage, loading: false });
          throw new Error(errorMessage);
        }
      },

      testNotification: async (type) => {
        try {
          await apiClient.post('/api/v3/notifications/test/', { type });
          get().showToast('success', 'Test Notification', `Test ${type} notification sent successfully`);
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Failed to send test notification';
          set({ error: errorMessage });
          throw new Error(errorMessage);
        }
      },

      // Real-time Updates
      connectWebSocket: () => {
        // WebSocket connection logic would go here
        // This is a simplified implementation
        set({ connected: true, reconnecting: false });
      },

      disconnectWebSocket: () => {
        set({ connected: false });
      },

      addNotification: (notification) => {
        set(state => ({
          notifications: [notification, ...state.notifications],
          unreadCount: notification.read ? state.unreadCount : state.unreadCount + 1
        }));
      },

      addAlert: (alert) => {
        set(state => ({
          alerts: [alert, ...state.alerts]
        }));
      },

      updateAlert: (id, updates) => {
        set(state => ({
          alerts: state.alerts.map(a =>
            a.id === id ? { ...a, ...updates } : a
          )
        }));
      },

      // Local Notifications
      showToast: (type, title, message) => {
        // This would integrate with a toast library like react-hot-toast
        const toast = {
          id: Date.now().toString(),
          type,
          title,
          message,
          timestamp: new Date().toISOString(),
          read: false,
          priority: 'medium' as const,
          category: 'system'
        };

        get().addNotification(toast);
      },

      // Utility
      clearError: () => set({ error: null }),
      setLoading: (loading) => set({ loading }),
    }),
    {
      name: 'notification-store',
      partialize: (state) => ({
        settings: state.settings,
        notifications: state.notifications.slice(0, 50), // Keep only recent notifications
      }),
    }
  )
);