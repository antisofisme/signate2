// API Client Compatibility Layer
// This file provides backward compatibility for imports

// Re-export the main API client
export { apiClient, ApiClient } from '../api/client';

// Re-export types for convenience
export type {
  ApiResponse,
  ApiError,
  ApiErrorCode,
  Asset,
  User,
  Tenant,
  CreateAssetRequest,
  UpdateAssetRequest,
  ShareAssetRequest,
  AssetFilters,
  PaginatedResponse,
  FileUpload,
  UploadProgress,
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  UserRole,
  SubscriptionTier,
  TenantSettings,
  QuotaUsage,
  AssetMetadata,
  UserInfo,
  TenantInfo,
  AssetUsageStats,
  SessionInfo,
  DeviceInfo,
  Session,
  AnalyticsRequest,
  AnalyticsMetric,
  AnalyticsResponse,
  AnalyticsData,
  ApiCallsMetric,
  AssetViewsMetric,
  UserActivityMetric,
  StorageUsageMetric,
  QuotaStatus,
  HealthResponse,
  VersionResponse,
  Permission,
  UserPermissions,
  WebSocketMessage,
  AssetUpdateMessage,
  NotificationMessage,
  RateLimitHeaders,
  ApiClientConfig,
  StoredRequest,
  OfflineQueueItem,
  UseApiQuery,
  UseApiMutation
} from '../types/api';

// Default export for compatibility
export default apiClient;