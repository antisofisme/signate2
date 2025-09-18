import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface AppState {
  // Theme
  theme: 'light' | 'dark' | 'system';

  // Sidebar
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;

  // Loading states
  globalLoading: boolean;

  // Notifications
  notifications: Notification[];

  // Preferences
  preferences: UserPreferences;

  // Recent activity
  recentActivity: ActivityItem[];
}

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  timestamp: Date;
  read: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface UserPreferences {
  language: string;
  timezone: string;
  dateFormat: string;
  itemsPerPage: number;
  emailNotifications: boolean;
  pushNotifications: boolean;
  autoSave: boolean;
}

interface ActivityItem {
  id: string;
  type: 'content' | 'user' | 'system';
  action: string;
  description: string;
  timestamp: Date;
  userId?: string;
  userName?: string;
}

interface AppActions {
  // Theme actions
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  toggleTheme: () => void;

  // Sidebar actions
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebarCollapsed: () => void;

  // Loading actions
  setGlobalLoading: (loading: boolean) => void;

  // Notification actions
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  removeNotification: (id: string) => void;
  markNotificationAsRead: (id: string) => void;
  markAllNotificationsAsRead: () => void;
  clearNotifications: () => void;

  // Preferences actions
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  resetPreferences: () => void;

  // Activity actions
  addActivity: (activity: Omit<ActivityItem, 'id' | 'timestamp'>) => void;
  clearActivity: () => void;
}

type AppStore = AppState & AppActions;

const defaultPreferences: UserPreferences = {
  language: 'en',
  timezone: 'UTC',
  dateFormat: 'MM/dd/yyyy',
  itemsPerPage: 10,
  emailNotifications: true,
  pushNotifications: false,
  autoSave: true,
};

const initialState: AppState = {
  theme: 'system',
  sidebarOpen: true,
  sidebarCollapsed: false,
  globalLoading: false,
  notifications: [],
  preferences: defaultPreferences,
  recentActivity: [],
};

export const useAppStore = create<AppStore>()(
  typeof window !== 'undefined' ? persist(
    (set, get) => ({
      ...initialState,

      // Theme actions
      setTheme: (theme) => {
        set({ theme });

        // Apply theme to document
        if (typeof window !== 'undefined') {
          const root = window.document.documentElement;
          root.classList.remove('light', 'dark');

          if (theme === 'system') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            root.classList.add(systemTheme);
          } else {
            root.classList.add(theme);
          }
        }
      },

      toggleTheme: () => {
        const { theme } = get();
        const newTheme = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light';
        get().setTheme(newTheme);
      },

      // Sidebar actions
      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      toggleSidebar: () => {
        const { sidebarOpen } = get();
        set({ sidebarOpen: !sidebarOpen });
      },

      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      toggleSidebarCollapsed: () => {
        const { sidebarCollapsed } = get();
        set({ sidebarCollapsed: !sidebarCollapsed });
      },

      // Loading actions
      setGlobalLoading: (loading) => set({ globalLoading: loading }),

      // Notification actions
      addNotification: (notification) => {
        const newNotification: Notification = {
          ...notification,
          id: `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
          read: false,
        };

        set((state) => ({
          notifications: [newNotification, ...state.notifications],
        }));

        // Auto-remove success notifications after 5 seconds
        if (notification.type === 'success') {
          setTimeout(() => {
            get().removeNotification(newNotification.id);
          }, 5000);
        }
      },

      removeNotification: (id) => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      },

      markNotificationAsRead: (id) => {
        set((state) => ({
          notifications: state.notifications.map((n) =>
            n.id === id ? { ...n, read: true } : n
          ),
        }));
      },

      markAllNotificationsAsRead: () => {
        set((state) => ({
          notifications: state.notifications.map((n) => ({ ...n, read: true })),
        }));
      },

      clearNotifications: () => set({ notifications: [] }),

      // Preferences actions
      updatePreferences: (newPreferences) => {
        set((state) => ({
          preferences: { ...state.preferences, ...newPreferences },
        }));
      },

      resetPreferences: () => set({ preferences: defaultPreferences }),

      // Activity actions
      addActivity: (activity) => {
        const newActivity: ActivityItem = {
          ...activity,
          id: `activity-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
        };

        set((state) => ({
          recentActivity: [newActivity, ...state.recentActivity.slice(0, 49)], // Keep only last 50 items
        }));
      },

      clearActivity: () => set({ recentActivity: [] }),
    }),
    {
      name: 'app-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        preferences: state.preferences,
      }),
    }
  ) : (set, get) => ({
    ...initialState,

    // Theme actions
    setTheme: (theme) => {
      set({ theme });
    },

    toggleTheme: () => {
      const { theme } = get();
      const newTheme = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light';
      get().setTheme(newTheme);
    },

    // Sidebar actions
    setSidebarOpen: (open) => set({ sidebarOpen: open }),
    toggleSidebar: () => {
      const { sidebarOpen } = get();
      set({ sidebarOpen: !sidebarOpen });
    },
    setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    toggleSidebarCollapsed: () => {
      const { sidebarCollapsed } = get();
      set({ sidebarCollapsed: !sidebarCollapsed });
    },

    // Loading actions
    setGlobalLoading: (loading) => set({ globalLoading: loading }),

    // Notification actions
    addNotification: (notification) => {
      const newNotification: Notification = {
        ...notification,
        id: `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
        read: false,
      };

      set((state) => ({
        notifications: [newNotification, ...state.notifications],
      }));
    },

    removeNotification: (id) => {
      set((state) => ({
        notifications: state.notifications.filter((n) => n.id !== id),
      }));
    },

    markNotificationAsRead: (id) => {
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, read: true } : n
        ),
      }));
    },

    markAllNotificationsAsRead: () => {
      set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, read: true })),
      }));
    },

    clearNotifications: () => set({ notifications: [] }),

    // Preferences actions
    updatePreferences: (newPreferences) => {
      set((state) => ({
        preferences: { ...state.preferences, ...newPreferences },
      }));
    },

    resetPreferences: () => set({ preferences: defaultPreferences }),

    // Activity actions
    addActivity: (activity) => {
      const newActivity: ActivityItem = {
        ...activity,
        id: `activity-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
      };

      set((state) => ({
        recentActivity: [newActivity, ...state.recentActivity.slice(0, 49)],
      }));
    },

    clearActivity: () => set({ recentActivity: [] }),
  })
);

// Utility hooks
export const useTheme = () => {
  const theme = useAppStore((state) => state.theme);
  const setTheme = useAppStore((state) => state.setTheme);
  const toggleTheme = useAppStore((state) => state.toggleTheme);

  return { theme, setTheme, toggleTheme };
};

export const useSidebar = () => {
  const sidebarOpen = useAppStore((state) => state.sidebarOpen);
  const sidebarCollapsed = useAppStore((state) => state.sidebarCollapsed);
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);
  const toggleSidebar = useAppStore((state) => state.toggleSidebar);
  const setSidebarCollapsed = useAppStore((state) => state.setSidebarCollapsed);
  const toggleSidebarCollapsed = useAppStore((state) => state.toggleSidebarCollapsed);

  return {
    sidebarOpen,
    sidebarCollapsed,
    setSidebarOpen,
    toggleSidebar,
    setSidebarCollapsed,
    toggleSidebarCollapsed,
  };
};

export const useNotifications = () => {
  const notifications = useAppStore((state) => state.notifications);
  const addNotification = useAppStore((state) => state.addNotification);
  const removeNotification = useAppStore((state) => state.removeNotification);
  const markNotificationAsRead = useAppStore((state) => state.markNotificationAsRead);
  const markAllNotificationsAsRead = useAppStore((state) => state.markAllNotificationsAsRead);
  const clearNotifications = useAppStore((state) => state.clearNotifications);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return {
    notifications,
    unreadCount,
    addNotification,
    removeNotification,
    markNotificationAsRead,
    markAllNotificationsAsRead,
    clearNotifications,
  };
};