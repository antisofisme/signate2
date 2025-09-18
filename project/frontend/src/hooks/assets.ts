import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  Asset,
  CreateAssetRequest,
  UpdateAssetRequest,
  ShareAssetRequest,
  AssetFilters,
  PaginatedResponse,
  AnalyticsResponse,
  AnalyticsRequest
} from '../types/api';
import { apiClient } from '../api/client';
import { queryKeys, updateQueryData, invalidateQueries } from '../lib/react-query';
import { useAssetsStore, useAssets, useAssetActions } from '../stores/assets';

// Asset list query
export const useAssetsList = (filters: AssetFilters = {}) => {
  return useQuery({
    queryKey: queryKeys.assets.list(filters),
    queryFn: async (): Promise<PaginatedResponse<Asset>> => {
      return apiClient.get('/assets/', { params: filters });
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    placeholderData: (prevData) => prevData, // Keep showing previous data while loading new
  });
};

// Single asset query
export const useAsset = (assetId: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.assets.detail(assetId),
    queryFn: async (): Promise<Asset> => {
      return apiClient.get(`/assets/${assetId}/`);
    },
    enabled: enabled && !!assetId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Asset analytics query
export const useAssetAnalytics = (assetId: string, request: AnalyticsRequest) => {
  return useQuery({
    queryKey: [...queryKeys.assets.analytics(assetId), request],
    queryFn: async (): Promise<AnalyticsResponse> => {
      return apiClient.post(`/assets/${assetId}/analytics/`, request);
    },
    enabled: !!assetId && !!request.metrics.length,
    staleTime: 10 * 60 * 1000, // 10 minutes for analytics
  });
};

// Create asset mutation
export const useCreateAsset = () => {
  const queryClient = useQueryClient();
  const { createAsset } = useAssetActions();

  return useMutation({
    mutationFn: async (data: CreateAssetRequest): Promise<Asset> => {
      return createAsset(data);
    },
    onMutate: async (newAsset) => {
      // Optimistic update
      const tempId = `temp-${Date.now()}`;
      const optimisticAsset = {
        asset_id: tempId,
        name: newAsset.name,
        uri: newAsset.uri,
        is_enabled: newAsset.is_enabled ?? true,
        is_processing: true,
        is_active: false,
        is_shared: false,
        mimetype: 'unknown',
        metadata: newAsset.metadata || {},
        tags: newAsset.tags || [],
        created_by: { id: 0, username: 'current-user' },
        tenant_info: { id: 0, name: 'current-tenant', slug: 'current' },
        usage_stats: { play_count: 0, total_play_time: 0 },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      updateQueryData.addAssetToLists(optimisticAsset);

      return { tempId };
    },
    onSuccess: (newAsset, variables, context) => {
      // Replace temporary asset with real one
      if (context?.tempId) {
        updateQueryData.removeAssetFromLists(context.tempId);
      }
      updateQueryData.addAssetToLists(newAsset);

      invalidateQueries.assets();
    },
    onError: (error, variables, context) => {
      // Remove optimistic update on error
      if (context?.tempId) {
        updateQueryData.removeAssetFromLists(context.tempId);
      }
    },
  });
};

// Update asset mutation
export const useUpdateAsset = () => {
  const queryClient = useQueryClient();
  const { updateAsset } = useAssetActions();

  return useMutation({
    mutationFn: async ({
      assetId,
      data
    }: {
      assetId: string;
      data: UpdateAssetRequest
    }): Promise<Asset> => {
      return updateAsset(assetId, data);
    },
    onMutate: async ({ assetId, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.assets.detail(assetId) });

      // Snapshot previous value
      const previousAsset = queryClient.getQueryData(queryKeys.assets.detail(assetId));

      // Optimistically update
      updateQueryData.updateAssetInLists(assetId, data);

      return { previousAsset, assetId };
    },
    onError: (error, variables, context) => {
      // Revert optimistic update
      if (context?.previousAsset && context?.assetId) {
        queryClient.setQueryData(
          queryKeys.assets.detail(context.assetId),
          context.previousAsset
        );
      }
    },
    onSettled: (data, error, variables) => {
      // Always refetch after error or success
      queryClient.invalidateQueries({
        queryKey: queryKeys.assets.detail(variables.assetId)
      });
    },
  });
};

// Delete asset mutation
export const useDeleteAsset = () => {
  const queryClient = useQueryClient();
  const { deleteAsset } = useAssetActions();

  return useMutation({
    mutationFn: async (assetId: string): Promise<void> => {
      return deleteAsset(assetId);
    },
    onMutate: async (assetId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.assets.detail(assetId) });

      // Snapshot previous value
      const previousAsset = queryClient.getQueryData(queryKeys.assets.detail(assetId));

      // Optimistically remove from lists
      updateQueryData.removeAssetFromLists(assetId);

      return { previousAsset, assetId };
    },
    onError: (error, assetId, context) => {
      // Revert optimistic update
      if (context?.previousAsset) {
        updateQueryData.addAssetToLists(context.previousAsset);
      }
    },
    onSuccess: () => {
      invalidateQueries.assets();
    },
  });
};

// Delete multiple assets mutation
export const useDeleteAssets = () => {
  const queryClient = useQueryClient();
  const { deleteAssets } = useAssetActions();

  return useMutation({
    mutationFn: async (assetIds: string[]): Promise<void> => {
      return deleteAssets(assetIds);
    },
    onMutate: async (assetIds) => {
      // Store previous assets for potential rollback
      const previousAssets = assetIds.map(id => ({
        id,
        data: queryClient.getQueryData(queryKeys.assets.detail(id)),
      }));

      // Optimistically remove from lists
      assetIds.forEach(id => updateQueryData.removeAssetFromLists(id));

      return { previousAssets };
    },
    onError: (error, assetIds, context) => {
      // Revert optimistic updates
      context?.previousAssets.forEach(({ id, data }) => {
        if (data) {
          updateQueryData.addAssetToLists(data);
        }
      });
    },
    onSuccess: () => {
      invalidateQueries.assets();
    },
  });
};

// Share asset mutation
export const useShareAsset = () => {
  const queryClient = useQueryClient();
  const { shareAsset } = useAssetActions();

  return useMutation({
    mutationFn: async ({
      assetId,
      shareData
    }: {
      assetId: string;
      shareData: ShareAssetRequest
    }): Promise<void> => {
      return shareAsset(assetId, shareData);
    },
    onSuccess: (data, { assetId }) => {
      // Update asset's sharing status
      updateQueryData.updateAssetInLists(assetId, { is_shared: true });
      queryClient.invalidateQueries({ queryKey: queryKeys.assets.detail(assetId) });
    },
  });
};

// Duplicate asset mutation
export const useDuplicateAsset = () => {
  const queryClient = useQueryClient();
  const { duplicateAsset } = useAssetActions();

  return useMutation({
    mutationFn: async (assetId: string): Promise<Asset> => {
      return duplicateAsset(assetId);
    },
    onSuccess: (newAsset) => {
      updateQueryData.addAssetToLists(newAsset);
      invalidateQueries.assets();
    },
  });
};

// File upload mutation
export const useUploadFile = () => {
  const queryClient = useQueryClient();
  const { uploadFile } = useAssetActions();

  return useMutation({
    mutationFn: async ({
      file,
      metadata,
      onProgress
    }: {
      file: File;
      metadata?: Partial<CreateAssetRequest>;
      onProgress?: (progress: { loaded: number; total: number; percentage: number }) => void;
    }): Promise<Asset> => {
      return uploadFile(file, metadata);
    },
    onSuccess: (newAsset) => {
      updateQueryData.addAssetToLists(newAsset);
      invalidateQueries.assets();
    },
  });
};

// Bulk upload mutation
export const useUploadFiles = () => {
  const queryClient = useQueryClient();
  const { uploadFiles } = useAssetActions();

  return useMutation({
    mutationFn: async ({
      files,
      metadata
    }: {
      files: FileList;
      metadata?: Partial<CreateAssetRequest>;
    }): Promise<Asset[]> => {
      return uploadFiles(files, metadata);
    },
    onSuccess: (newAssets) => {
      newAssets.forEach(asset => updateQueryData.addAssetToLists(asset));
      invalidateQueries.assets();
    },
  });
};

// Hook for infinite loading (pagination)
export const useInfiniteAssets = (filters: AssetFilters = {}) => {
  return useInfiniteQuery({
    queryKey: [...queryKeys.assets.lists(), 'infinite', filters],
    queryFn: async ({ pageParam = 1 }): Promise<PaginatedResponse<Asset>> => {
      return apiClient.get('/assets/', {
        params: { ...filters, page: pageParam },
      });
    },
    getNextPageParam: (lastPage) => {
      return lastPage.meta.has_next ? lastPage.meta.page + 1 : undefined;
    },
    staleTime: 2 * 60 * 1000,
    initialPageParam: 1,
  });
};

// Hook for prefetching next page
export const usePrefetchNextPage = (filters: AssetFilters = {}) => {
  const queryClient = useQueryClient();

  const prefetchNext = (currentPage: number) => {
    const nextPageFilters = { ...filters, page: currentPage + 1 };

    queryClient.prefetchQuery({
      queryKey: queryKeys.assets.list(nextPageFilters),
      queryFn: () => apiClient.get('/assets/', { params: nextPageFilters }),
      staleTime: 2 * 60 * 1000,
    });
  };

  return { prefetchNext };
};

// Hook for asset operations with the store
export const useAssetOperations = () => {
  const {
    selectedAssets,
    selectAsset,
    selectAssets,
    toggleAssetSelection,
    selectAllAssets,
    clearSelection,
  } = useAssetsStore();

  const deleteAssetMutation = useDeleteAsset();
  const deleteAssetsMutation = useDeleteAssets();
  const shareAssetMutation = useShareAsset();
  const duplicateAssetMutation = useDuplicateAsset();

  const handleBulkDelete = async () => {
    if (selectedAssets.size === 0) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedAssets.size} asset(s)? This action cannot be undone.`
    );

    if (confirmed) {
      try {
        await deleteAssetsMutation.mutateAsync(Array.from(selectedAssets));
        clearSelection();
        toast.success('Assets deleted successfully!');
      } catch (error) {
        console.error('Bulk delete failed:', error);
      }
    }
  };

  const handleBulkShare = async (shareData: ShareAssetRequest) => {
    if (selectedAssets.size === 0) return;

    try {
      await Promise.all(
        Array.from(selectedAssets).map(assetId =>
          shareAssetMutation.mutateAsync({ assetId, shareData })
        )
      );
      clearSelection();
      toast.success('Assets shared successfully!');
    } catch (error) {
      console.error('Bulk share failed:', error);
    }
  };

  return {
    selectedAssets: Array.from(selectedAssets),
    selectAsset,
    selectAssets,
    toggleAssetSelection,
    selectAllAssets,
    clearSelection,
    handleBulkDelete,
    handleBulkShare,
    isDeleting: deleteAssetsMutation.isPending,
    isSharing: shareAssetMutation.isPending,
  };
};

export default {
  useAssetsList,
  useAsset,
  useAssetAnalytics,
  useCreateAsset,
  useUpdateAsset,
  useDeleteAsset,
  useDeleteAssets,
  useShareAsset,
  useDuplicateAsset,
  useUploadFile,
  useUploadFiles,
  useInfiniteAssets,
  useAssetOperations,
};