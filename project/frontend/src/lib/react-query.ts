import { QueryClient, DefaultOptions } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { ApiError, ApiErrorCode } from '../types/api';

// Default configuration for React Query
const defaultOptions: DefaultOptions = {
  queries: {
    // Time before data is considered stale (5 minutes)
    staleTime: 5 * 60 * 1000,

    // Time before inactive data is garbage collected (10 minutes)
    gcTime: 10 * 60 * 1000,

    // Retry failed requests
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors (client errors)
      if (error instanceof ApiError) {
        const noRetryErrors = [
          ApiErrorCode.VALIDATION_ERROR,
          ApiErrorCode.UNAUTHORIZED,
          ApiErrorCode.PERMISSION_DENIED,
          ApiErrorCode.NOT_FOUND,
        ];

        if (noRetryErrors.includes(error.code)) {
          return false;
        }
      }

      // Retry up to 3 times for other errors
      return failureCount < 3;
    },

    // Exponential backoff for retries
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

    // Refetch on window focus for important data
    refetchOnWindowFocus: true,

    // Refetch when coming back online
    refetchOnReconnect: true,

    // Error handling is now done at component level or with error boundaries
  },

  mutations: {
    // Retry mutations only for network/server errors
    retry: (failureCount, error) => {
      if (error instanceof ApiError) {
        const retryableErrors = [
          ApiErrorCode.NETWORK_ERROR,
          ApiErrorCode.TIMEOUT_ERROR,
          ApiErrorCode.SERVER_ERROR,
        ];

        if (retryableErrors.includes(error.code)) {
          return failureCount < 2;
        }
      }

      return false;
    },

    // Error handling for mutations is now done at component level
  },
};

// Create query client instance
export const queryClient = new QueryClient({
  defaultOptions,
});

// Query key factories for consistent key generation
export const queryKeys = {
  // Authentication
  auth: {
    profile: () => ['auth', 'profile'] as const,
    sessions: () => ['auth', 'sessions'] as const,
  },

  // Assets
  assets: {
    all: () => ['assets'] as const,
    lists: () => [...queryKeys.assets.all(), 'list'] as const,
    list: (filters: Record<string, any>) => [...queryKeys.assets.lists(), filters] as const,
    details: () => [...queryKeys.assets.all(), 'detail'] as const,
    detail: (id: string) => [...queryKeys.assets.details(), id] as const,
    analytics: (id: string) => [...queryKeys.assets.detail(id), 'analytics'] as const,
  },

  // Users
  users: {
    all: () => ['users'] as const,
    lists: () => [...queryKeys.users.all(), 'list'] as const,
    list: (filters: Record<string, any>) => [...queryKeys.users.lists(), filters] as const,
    details: () => [...queryKeys.users.all(), 'detail'] as const,
    detail: (id: string) => [...queryKeys.users.details(), id] as const,
  },

  // Tenants
  tenants: {
    all: () => ['tenants'] as const,
    current: () => [...queryKeys.tenants.all(), 'current'] as const,
    analytics: (period: string) => [...queryKeys.tenants.current(), 'analytics', period] as const,
  },

  // Search
  search: {
    all: () => ['search'] as const,
    global: (query: string, filters: Record<string, any>) =>
      [...queryKeys.search.all(), 'global', query, filters] as const,
    assets: (query: string, filters: Record<string, any>) =>
      [...queryKeys.search.all(), 'assets', query, filters] as const,
    suggestions: (partial: string) =>
      [...queryKeys.search.all(), 'suggestions', partial] as const,
  },

  // System
  system: {
    health: () => ['system', 'health'] as const,
    version: () => ['system', 'version'] as const,
  },
};

// Cache invalidation utilities
export const invalidateQueries = {
  // Invalidate all asset-related queries
  assets: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.assets.all() });
  },

  // Invalidate specific asset
  asset: (id: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.assets.detail(id) });
  },

  // Invalidate current user profile
  profile: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.auth.profile() });
  },

  // Invalidate tenant data
  tenant: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.tenants.current() });
  },

  // Invalidate search results
  search: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.search.all() });
  },

  // Invalidate all queries (nuclear option)
  all: () => {
    queryClient.invalidateQueries();
  },
};

// Cache updating utilities for optimistic updates
export const updateQueryData = {
  // Update asset in asset lists
  updateAssetInLists: (assetId: string, updatedAsset: any) => {
    // Update all asset list queries
    queryClient.setQueriesData(
      { queryKey: queryKeys.assets.lists() },
      (oldData: any) => {
        if (!oldData?.data) return oldData;

        return {
          ...oldData,
          data: oldData.data.map((asset: any) =>
            asset.asset_id === assetId ? { ...asset, ...updatedAsset } : asset
          ),
        };
      }
    );

    // Update specific asset detail
    queryClient.setQueryData(
      queryKeys.assets.detail(assetId),
      (oldData: any) => oldData ? { ...oldData, ...updatedAsset } : oldData
    );
  },

  // Add new asset to lists
  addAssetToLists: (newAsset: any) => {
    queryClient.setQueriesData(
      { queryKey: queryKeys.assets.lists() },
      (oldData: any) => {
        if (!oldData?.data) return oldData;

        return {
          ...oldData,
          data: [newAsset, ...oldData.data],
          meta: {
            ...oldData.meta,
            total: oldData.meta.total + 1,
          },
        };
      }
    );
  },

  // Remove asset from lists
  removeAssetFromLists: (assetId: string) => {
    queryClient.setQueriesData(
      { queryKey: queryKeys.assets.lists() },
      (oldData: any) => {
        if (!oldData?.data) return oldData;

        return {
          ...oldData,
          data: oldData.data.filter((asset: any) => asset.asset_id !== assetId),
          meta: {
            ...oldData.meta,
            total: Math.max(0, oldData.meta.total - 1),
          },
        };
      }
    );

    // Remove from cache
    queryClient.removeQueries({ queryKey: queryKeys.assets.detail(assetId) });
  },

  // Update user profile
  updateProfile: (updates: any) => {
    queryClient.setQueryData(
      queryKeys.auth.profile(),
      (oldData: any) => oldData ? { ...oldData, ...updates } : oldData
    );
  },
};

// Prefetching utilities
export const prefetchQueries = {
  // Prefetch asset details when hovering over asset in list
  assetDetails: (assetId: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.assets.detail(assetId),
      queryFn: async () => {
        const { apiClient } = await import('../api/client');
        return apiClient.get(`/assets/${assetId}/`);
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
    });
  },

  // Prefetch next page of assets
  nextAssetPage: (currentFilters: Record<string, any>) => {
    const nextPageFilters = {
      ...currentFilters,
      page: (currentFilters.page || 1) + 1,
    };

    queryClient.prefetchQuery({
      queryKey: queryKeys.assets.list(nextPageFilters),
      queryFn: async () => {
        const { apiClient } = await import('../api/client');
        return apiClient.get('/assets/', { params: nextPageFilters });
      },
      staleTime: 2 * 60 * 1000, // 2 minutes
    });
  },
};

// Background sync utilities
export const backgroundSync = {
  // Sync critical data in background
  syncCriticalData: async () => {
    try {
      await Promise.allSettled([
        queryClient.refetchQueries({ queryKey: queryKeys.auth.profile() }),
        queryClient.refetchQueries({ queryKey: queryKeys.tenants.current() }),
      ]);
    } catch (error) {
      console.error('Background sync failed:', error);
    }
  },

  // Sync asset data
  syncAssets: async () => {
    try {
      await queryClient.refetchQueries({ queryKey: queryKeys.assets.lists() });
    } catch (error) {
      console.error('Asset sync failed:', error);
    }
  },
};

// Setup periodic background sync when online
if (typeof window !== 'undefined') {
  // Sync critical data every 5 minutes when tab is visible
  setInterval(() => {
    if (document.visibilityState === 'visible' && navigator.onLine) {
      backgroundSync.syncCriticalData();
    }
  }, 5 * 60 * 1000);

  // Sync when tab becomes visible
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && navigator.onLine) {
      backgroundSync.syncCriticalData();
    }
  });

  // Sync when coming back online
  window.addEventListener('online', () => {
    backgroundSync.syncCriticalData();
  });
}

export default queryClient;