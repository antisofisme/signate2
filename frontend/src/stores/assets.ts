import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { toast } from 'react-hot-toast';
import {
  Asset,
  CreateAssetRequest,
  UpdateAssetRequest,
  ShareAssetRequest,
  AssetFilters,
  PaginatedResponse,
  FileUpload,
  UploadProgress,
  ApiError,
  ApiErrorCode
} from '../types/api';
import { apiClient } from '../api/client';

export interface AssetsState {
  // Data
  assets: Asset[];
  selectedAssets: Set<string>;
  currentAsset: Asset | null;

  // UI State
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  isUploading: boolean;

  // Pagination & Filtering
  currentPage: number;
  totalPages: number;
  totalAssets: number;
  perPage: number;
  hasNextPage: boolean;
  hasPrevPage: boolean;
  filters: AssetFilters;
  sortBy: string;
  sortOrder: 'asc' | 'desc';

  // Upload management
  uploadQueue: FileUpload[];
  uploadProgress: { [key: string]: UploadProgress };

  // Optimistic updates tracking
  optimisticUpdates: Map<string, Partial<Asset>>;

  // Actions
  fetchAssets: (filters?: AssetFilters) => Promise<void>;
  fetchAsset: (assetId: string) => Promise<Asset>;
  createAsset: (data: CreateAssetRequest) => Promise<Asset>;
  updateAsset: (assetId: string, data: UpdateAssetRequest) => Promise<Asset>;
  deleteAsset: (assetId: string) => Promise<void>;
  deleteAssets: (assetIds: string[]) => Promise<void>;
  shareAsset: (assetId: string, shareData: ShareAssetRequest) => Promise<void>;
  duplicateAsset: (assetId: string) => Promise<Asset>;

  // Upload actions
  uploadFile: (file: File, metadata?: Partial<CreateAssetRequest>) => Promise<Asset>;
  uploadFiles: (files: FileList, metadata?: Partial<CreateAssetRequest>) => Promise<Asset[]>;
  cancelUpload: (uploadId: string) => void;
  clearUploadQueue: () => void;

  // Selection actions
  selectAsset: (assetId: string) => void;
  selectAssets: (assetIds: string[]) => void;
  toggleAssetSelection: (assetId: string) => void;
  selectAllAssets: () => void;
  clearSelection: () => void;

  // Filtering & Pagination
  setFilters: (filters: Partial<AssetFilters>) => void;
  clearFilters: () => void;
  setPage: (page: number) => void;
  setSorting: (sortBy: string, sortOrder?: 'asc' | 'desc') => void;

  // Optimistic updates
  applyOptimisticUpdate: (assetId: string, update: Partial<Asset>) => void;
  revertOptimisticUpdate: (assetId: string) => void;

  // UI state management
  setCurrentAsset: (asset: Asset | null) => void;
  refreshAssets: () => Promise<void>;
}

const DEFAULT_FILTERS: AssetFilters = {
  page: 1,
  per_page: 20,
  ordering: '-created_at',
};

export const useAssetsStore = create<AssetsState>()(
  devtools(
    (set, get) => ({
      // Initial state
      assets: [],
      selectedAssets: new Set(),
      currentAsset: null,

      isLoading: false,
      isCreating: false,
      isUpdating: false,
      isDeleting: false,
      isUploading: false,

      currentPage: 1,
      totalPages: 0,
      totalAssets: 0,
      perPage: 20,
      hasNextPage: false,
      hasPrevPage: false,
      filters: DEFAULT_FILTERS,
      sortBy: 'created_at',
      sortOrder: 'desc',

      uploadQueue: [],
      uploadProgress: {},
      optimisticUpdates: new Map(),

      // Fetch assets with pagination and filtering
      fetchAssets: async (filters = {}) => {
        set({ isLoading: true });

        try {
          const state = get();
          const mergedFilters = { ...state.filters, ...filters };

          const response = await apiClient.get<PaginatedResponse<Asset>>('/assets/', {
            params: mergedFilters,
          });

          set({
            assets: response.data,
            currentPage: response.meta.page,
            totalPages: response.meta.pages,
            totalAssets: response.meta.total,
            perPage: response.meta.per_page,
            hasNextPage: response.meta.has_next,
            hasPrevPage: response.meta.has_prev,
            filters: mergedFilters,
            isLoading: false,
          });

        } catch (error) {
          console.error('Failed to fetch assets:', error);
          set({ isLoading: false });

          if (error instanceof ApiError) {
            toast.error(`Failed to load assets: ${error.message}`);
          } else {
            toast.error('Failed to load assets');
          }

          throw error;
        }
      },

      // Fetch single asset
      fetchAsset: async (assetId: string) => {
        try {
          const asset = await apiClient.get<Asset>(`/assets/${assetId}/`);

          // Update asset in list if it exists
          const state = get();
          const updatedAssets = state.assets.map(a =>
            a.asset_id === assetId ? asset : a
          );

          set({
            assets: updatedAssets,
            currentAsset: asset,
          });

          return asset;
        } catch (error) {
          console.error('Failed to fetch asset:', error);
          throw error;
        }
      },

      // Create new asset
      createAsset: async (data: CreateAssetRequest) => {
        set({ isCreating: true });

        try {
          const newAsset = await apiClient.post<Asset>('/assets/', data);

          const state = get();

          // Add to beginning of assets list
          set({
            assets: [newAsset, ...state.assets],
            totalAssets: state.totalAssets + 1,
            isCreating: false,
          });

          toast.success('Asset created successfully!');
          return newAsset;

        } catch (error) {
          console.error('Failed to create asset:', error);
          set({ isCreating: false });

          if (error instanceof ApiError) {
            toast.error(`Failed to create asset: ${error.message}`);
          } else {
            toast.error('Failed to create asset');
          }

          throw error;
        }
      },

      // Update asset with optimistic updates
      updateAsset: async (assetId: string, data: UpdateAssetRequest) => {
        const state = get();

        // Apply optimistic update
        state.applyOptimisticUpdate(assetId, data);
        set({ isUpdating: true });

        try {
          const updatedAsset = await apiClient.patch<Asset>(`/assets/${assetId}/`, data);

          // Replace optimistic update with real data
          const updatedAssets = state.assets.map(asset =>
            asset.asset_id === assetId ? updatedAsset : asset
          );

          set({
            assets: updatedAssets,
            currentAsset: state.currentAsset?.asset_id === assetId ? updatedAsset : state.currentAsset,
            isUpdating: false,
          });

          // Remove optimistic update
          state.revertOptimisticUpdate(assetId);

          toast.success('Asset updated successfully!');
          return updatedAsset;

        } catch (error) {
          console.error('Failed to update asset:', error);

          // Revert optimistic update
          state.revertOptimisticUpdate(assetId);
          set({ isUpdating: false });

          if (error instanceof ApiError) {
            toast.error(`Failed to update asset: ${error.message}`);
          } else {
            toast.error('Failed to update asset');
          }

          throw error;
        }
      },

      // Delete single asset
      deleteAsset: async (assetId: string) => {
        set({ isDeleting: true });

        try {
          await apiClient.delete(`/assets/${assetId}/`);

          const state = get();

          // Remove from assets list
          const updatedAssets = state.assets.filter(asset => asset.asset_id !== assetId);

          // Remove from selection
          const updatedSelection = new Set(state.selectedAssets);
          updatedSelection.delete(assetId);

          set({
            assets: updatedAssets,
            selectedAssets: updatedSelection,
            currentAsset: state.currentAsset?.asset_id === assetId ? null : state.currentAsset,
            totalAssets: state.totalAssets - 1,
            isDeleting: false,
          });

          toast.success('Asset deleted successfully!');

        } catch (error) {
          console.error('Failed to delete asset:', error);
          set({ isDeleting: false });

          if (error instanceof ApiError) {
            toast.error(`Failed to delete asset: ${error.message}`);
          } else {
            toast.error('Failed to delete asset');
          }

          throw error;
        }
      },

      // Delete multiple assets
      deleteAssets: async (assetIds: string[]) => {
        set({ isDeleting: true });

        try {
          // Delete assets in parallel
          await Promise.all(
            assetIds.map(id => apiClient.delete(`/assets/${id}/`))
          );

          const state = get();

          // Remove from assets list
          const updatedAssets = state.assets.filter(
            asset => !assetIds.includes(asset.asset_id)
          );

          // Clear selection
          set({
            assets: updatedAssets,
            selectedAssets: new Set(),
            totalAssets: state.totalAssets - assetIds.length,
            isDeleting: false,
          });

          toast.success(`${assetIds.length} assets deleted successfully!`);

        } catch (error) {
          console.error('Failed to delete assets:', error);
          set({ isDeleting: false });

          if (error instanceof ApiError) {
            toast.error(`Failed to delete assets: ${error.message}`);
          } else {
            toast.error('Failed to delete assets');
          }

          throw error;
        }
      },

      // Share asset with other tenants
      shareAsset: async (assetId: string, shareData: ShareAssetRequest) => {
        try {
          await apiClient.post(`/assets/${assetId}/share/`, shareData);

          // Update asset's sharing status
          const state = get();
          const updatedAssets = state.assets.map(asset =>
            asset.asset_id === assetId
              ? { ...asset, is_shared: true }
              : asset
          );

          set({ assets: updatedAssets });

          toast.success('Asset shared successfully!');

        } catch (error) {
          console.error('Failed to share asset:', error);

          if (error instanceof ApiError) {
            toast.error(`Failed to share asset: ${error.message}`);
          } else {
            toast.error('Failed to share asset');
          }

          throw error;
        }
      },

      // Duplicate asset
      duplicateAsset: async (assetId: string) => {
        try {
          const duplicatedAsset = await apiClient.post<Asset>(`/assets/${assetId}/duplicate/`);

          const state = get();

          // Add to beginning of assets list
          set({
            assets: [duplicatedAsset, ...state.assets],
            totalAssets: state.totalAssets + 1,
          });

          toast.success('Asset duplicated successfully!');
          return duplicatedAsset;

        } catch (error) {
          console.error('Failed to duplicate asset:', error);

          if (error instanceof ApiError) {
            toast.error(`Failed to duplicate asset: ${error.message}`);
          } else {
            toast.error('Failed to duplicate asset');
          }

          throw error;
        }
      },

      // Upload single file
      uploadFile: async (file: File, metadata = {}) => {
        const uploadId = `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        const fileUpload: FileUpload = {
          file,
          progress: { loaded: 0, total: file.size, percentage: 0 },
          status: 'pending',
        };

        const state = get();
        set({
          uploadQueue: [...state.uploadQueue, fileUpload],
          isUploading: true,
        });

        try {
          const asset = await apiClient.uploadFile<Asset>(
            '/assets/upload/',
            file,
            (progress) => {
              const state = get();
              set({
                uploadProgress: {
                  ...state.uploadProgress,
                  [uploadId]: progress,
                },
              });
            },
            {
              name: metadata.name || file.name,
              ...metadata,
            }
          );

          // Update upload status
          const updatedQueue = state.uploadQueue.map(upload =>
            upload.file === file
              ? { ...upload, status: 'success' as const, asset_id: asset.asset_id }
              : upload
          );

          // Add to assets list
          set({
            uploadQueue: updatedQueue,
            assets: [asset, ...state.assets],
            totalAssets: state.totalAssets + 1,
          });

          toast.success(`File "${file.name}" uploaded successfully!`);
          return asset;

        } catch (error) {
          console.error('Failed to upload file:', error);

          // Update upload status
          const state = get();
          const updatedQueue = state.uploadQueue.map(upload =>
            upload.file === file
              ? { ...upload, status: 'error' as const, error: error instanceof Error ? error.message : 'Upload failed' }
              : upload
          );

          set({ uploadQueue: updatedQueue });

          if (error instanceof ApiError) {
            toast.error(`Failed to upload "${file.name}": ${error.message}`);
          } else {
            toast.error(`Failed to upload "${file.name}"`);
          }

          throw error;
        } finally {
          // Check if all uploads are complete
          const state = get();
          const hasActiveUploads = state.uploadQueue.some(
            upload => upload.status === 'pending' || upload.status === 'uploading'
          );

          if (!hasActiveUploads) {
            set({ isUploading: false });
          }
        }
      },

      // Upload multiple files
      uploadFiles: async (files: FileList, metadata = {}) => {
        const fileArray = Array.from(files);

        try {
          const uploadPromises = fileArray.map(file =>
            get().uploadFile(file, metadata)
          );

          const assets = await Promise.all(uploadPromises);

          toast.success(`${assets.length} files uploaded successfully!`);
          return assets;

        } catch (error) {
          console.error('Failed to upload files:', error);
          throw error;
        }
      },

      // Cancel upload (if supported by the API)
      cancelUpload: (uploadId: string) => {
        const state = get();
        const updatedQueue = state.uploadQueue.filter(
          upload => upload.file.name !== uploadId
        );

        set({ uploadQueue: updatedQueue });

        delete state.uploadProgress[uploadId];
        set({ uploadProgress: { ...state.uploadProgress } });
      },

      // Clear upload queue
      clearUploadQueue: () => {
        set({ uploadQueue: [], uploadProgress: {} });
      },

      // Selection management
      selectAsset: (assetId: string) => {
        set({ selectedAssets: new Set([assetId]) });
      },

      selectAssets: (assetIds: string[]) => {
        set({ selectedAssets: new Set(assetIds) });
      },

      toggleAssetSelection: (assetId: string) => {
        const state = get();
        const newSelection = new Set(state.selectedAssets);

        if (newSelection.has(assetId)) {
          newSelection.delete(assetId);
        } else {
          newSelection.add(assetId);
        }

        set({ selectedAssets: newSelection });
      },

      selectAllAssets: () => {
        const state = get();
        const allAssetIds = state.assets.map(asset => asset.asset_id);
        set({ selectedAssets: new Set(allAssetIds) });
      },

      clearSelection: () => {
        set({ selectedAssets: new Set() });
      },

      // Filtering and pagination
      setFilters: (newFilters: Partial<AssetFilters>) => {
        const state = get();
        const updatedFilters = { ...state.filters, ...newFilters, page: 1 };

        set({ filters: updatedFilters });

        // Automatically fetch assets with new filters
        state.fetchAssets(updatedFilters);
      },

      clearFilters: () => {
        set({ filters: DEFAULT_FILTERS });
        get().fetchAssets(DEFAULT_FILTERS);
      },

      setPage: (page: number) => {
        const state = get();
        const updatedFilters = { ...state.filters, page };

        set({ filters: updatedFilters });
        state.fetchAssets(updatedFilters);
      },

      setSorting: (sortBy: string, sortOrder = 'desc') => {
        const state = get();
        const ordering = sortOrder === 'desc' ? `-${sortBy}` : sortBy;
        const updatedFilters = { ...state.filters, ordering, page: 1 };

        set({
          filters: updatedFilters,
          sortBy,
          sortOrder,
        });

        state.fetchAssets(updatedFilters);
      },

      // Optimistic updates
      applyOptimisticUpdate: (assetId: string, update: Partial<Asset>) => {
        const state = get();
        const currentUpdate = state.optimisticUpdates.get(assetId) || {};
        const newUpdate = { ...currentUpdate, ...update };

        // Apply update to assets list
        const updatedAssets = state.assets.map(asset =>
          asset.asset_id === assetId
            ? { ...asset, ...newUpdate }
            : asset
        );

        const newOptimisticUpdates = new Map(state.optimisticUpdates);
        newOptimisticUpdates.set(assetId, newUpdate);

        set({
          assets: updatedAssets,
          optimisticUpdates: newOptimisticUpdates,
        });
      },

      revertOptimisticUpdate: (assetId: string) => {
        const state = get();
        const newOptimisticUpdates = new Map(state.optimisticUpdates);
        newOptimisticUpdates.delete(assetId);

        set({ optimisticUpdates: newOptimisticUpdates });
      },

      // UI state management
      setCurrentAsset: (asset: Asset | null) => {
        set({ currentAsset: asset });
      },

      refreshAssets: async () => {
        const state = get();
        return state.fetchAssets(state.filters);
      },
    }),
    {
      name: 'assets-store',
      enabled: process.env.NODE_ENV === 'development',
    }
  )
);

// Selectors for easy access
export const useAssets = () => {
  const store = useAssetsStore();
  return {
    assets: store.assets,
    selectedAssets: Array.from(store.selectedAssets),
    currentAsset: store.currentAsset,
    isLoading: store.isLoading,
    totalAssets: store.totalAssets,
    currentPage: store.currentPage,
    totalPages: store.totalPages,
    hasNextPage: store.hasNextPage,
    hasPrevPage: store.hasPrevPage,
  };
};

export const useAssetActions = () => {
  const store = useAssetsStore();
  return {
    fetchAssets: store.fetchAssets,
    createAsset: store.createAsset,
    updateAsset: store.updateAsset,
    deleteAsset: store.deleteAsset,
    deleteAssets: store.deleteAssets,
    shareAsset: store.shareAsset,
    duplicateAsset: store.duplicateAsset,
    uploadFile: store.uploadFile,
    uploadFiles: store.uploadFiles,
    refreshAssets: store.refreshAssets,
  };
};

export const useAssetSelection = () => {
  const store = useAssetsStore();
  return {
    selectedAssets: Array.from(store.selectedAssets),
    selectAsset: store.selectAsset,
    selectAssets: store.selectAssets,
    toggleAssetSelection: store.toggleAssetSelection,
    selectAllAssets: store.selectAllAssets,
    clearSelection: store.clearSelection,
  };
};

export const useAssetFilters = () => {
  const store = useAssetsStore();
  return {
    filters: store.filters,
    sortBy: store.sortBy,
    sortOrder: store.sortOrder,
    setFilters: store.setFilters,
    clearFilters: store.clearFilters,
    setPage: store.setPage,
    setSorting: store.setSorting,
  };
};

export default useAssetsStore;