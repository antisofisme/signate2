// TypeScript types generated from API v3 specifications
// Auto-generated from backend API schema

// Base Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
  request_id?: string;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  meta: {
    page: number;
    pages: number;
    per_page: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, string[]>;
  timestamp: string;
  request_id?: string;
}

// Authentication Types
export interface LoginRequest {
  username: string;
  password: string;
  tenant_slug?: string;
  remember_me?: boolean;
  device_info?: {
    user_agent: string;
    platform: string;
  };
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: 'Bearer';
  user: User;
  tenant?: Tenant;
  session_info: SessionInfo;
}

export interface RefreshTokenRequest {
  refresh_token: string;
  device_info?: {
    user_agent: string;
    platform: string;
  };
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: 'Bearer';
}

// User Types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  date_joined: string;
  last_login?: string;
  current_tenant?: TenantMembership;
  tenant_memberships: TenantMembership[];
}

export interface TenantMembership {
  tenant_id: number;
  tenant_name: string;
  tenant_slug: string;
  role: UserRole;
  joined_at: string;
}

export type UserRole = 'owner' | 'admin' | 'manager' | 'editor' | 'viewer' | 'guest';

// Tenant Types
export interface Tenant {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
  subscription_tier: SubscriptionTier;
  created_at: string;
  settings: TenantSettings;
  user_count: number;
  asset_count: number;
  quota_usage: QuotaUsage;
}

export type SubscriptionTier = 'free' | 'pro' | 'enterprise' | 'admin';

export interface TenantSettings {
  timezone: string;
  date_format: string;
  [key: string]: any;
}

export interface QuotaUsage {
  api_calls_this_month: number;
  storage_used_mb: number;
  users_count: number;
  assets_count: number;
}

// Asset Types
export interface Asset {
  asset_id: string;
  name: string;
  uri: string;
  md5?: string;
  start_date?: string;
  end_date?: string;
  duration?: number;
  mimetype: string;
  is_enabled: boolean;
  is_processing: boolean;
  is_active: boolean;
  is_shared: boolean;
  metadata: AssetMetadata;
  tags: string[];
  created_by: UserInfo;
  tenant_info: TenantInfo;
  usage_stats: AssetUsageStats;
  created_at: string;
  updated_at: string;
}

export interface AssetMetadata {
  resolution?: string;
  fps?: number;
  description?: string;
  [key: string]: any;
}

export interface UserInfo {
  id: number;
  username: string;
  full_name?: string;
}

export interface TenantInfo {
  id: number;
  name: string;
  slug: string;
}

export interface AssetUsageStats {
  play_count: number;
  total_play_time: number;
  last_played?: string;
}

export interface CreateAssetRequest {
  name: string;
  uri: string;
  start_date?: string;
  end_date?: string;
  duration?: number;
  is_enabled?: boolean;
  metadata?: AssetMetadata;
  tags?: string[];
}

export interface UpdateAssetRequest extends Partial<CreateAssetRequest> {}

export interface ShareAssetRequest {
  target_tenant_ids: number[];
  permission_level: 'view' | 'edit';
  message?: string;
  expires_at?: string;
}

// Asset Filters
export interface AssetFilters {
  page?: number;
  per_page?: number;
  status?: 'active' | 'inactive';
  mimetype?: string;
  tags?: string;
  search?: string;
  ordering?: 'name' | 'created_at' | 'start_date' | 'play_order' | '-name' | '-created_at' | '-start_date' | '-play_order';
  is_enabled?: boolean;
  created_at__gte?: string;
  created_at__lte?: string;
  is_shared?: boolean;
}

// Session Types
export interface SessionInfo {
  session_id: string;
  created_at: string;
  device_info?: DeviceInfo;
}

export interface DeviceInfo {
  user_agent: string;
  platform: string;
  ip_address?: string;
}

export interface Session {
  session_id: string;
  is_current: boolean;
  created_at: string;
  last_activity: string;
  device_info: DeviceInfo;
}

// Analytics Types
export interface AnalyticsRequest {
  period: 'day' | 'week' | 'month' | 'year';
  start_date?: string;
  end_date?: string;
  metrics: AnalyticsMetric[];
}

export type AnalyticsMetric = 'api_calls' | 'asset_views' | 'user_activity' | 'storage_usage';

export interface AnalyticsResponse {
  tenant_id: number;
  period: string;
  metrics: AnalyticsData;
  quota_status: QuotaStatus;
}

export interface AnalyticsData {
  api_calls?: ApiCallsMetric;
  asset_views?: AssetViewsMetric;
  user_activity?: UserActivityMetric;
  storage_usage?: StorageUsageMetric;
}

export interface ApiCallsMetric {
  total: number;
  by_endpoint: Record<string, number>;
  by_day: Array<{ date: string; count: number }>;
}

export interface AssetViewsMetric {
  total: number;
  by_asset: Record<string, number>;
  by_day: Array<{ date: string; count: number }>;
}

export interface UserActivityMetric {
  active_users: number;
  new_users: number;
  login_frequency: Record<string, number>;
}

export interface StorageUsageMetric {
  total_mb: number;
  by_type: Record<string, number>;
  growth_trend: Array<{ date: string; usage_mb: number }>;
}

export interface QuotaStatus {
  api_calls_used: number;
  api_calls_limit: number;
  storage_used_mb: number;
  storage_limit_mb: number;
}

// Health Check Types
export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  features: {
    tenant_isolation: boolean;
    asset_sharing: boolean;
    advanced_permissions: boolean;
    rate_limiting: boolean;
    analytics: boolean;
  };
}

export interface VersionResponse {
  current_version: string;
  supported_versions: string[];
  deprecated_versions: string[];
  sunset_date?: string;
}

// Permission Types
export interface Permission {
  name: string;
  description: string;
  resource: string;
  action: string;
}

export interface UserPermissions {
  user_id: number;
  tenant_id: number;
  role: UserRole;
  permissions: string[];
  effective_permissions: string[];
}

// Upload Types
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface FileUpload {
  file: File;
  progress: UploadProgress;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  asset_id?: string;
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

export interface AssetUpdateMessage extends WebSocketMessage {
  type: 'asset_updated';
  payload: {
    asset_id: string;
    changes: Partial<Asset>;
    tenant_id: number;
  };
}

export interface NotificationMessage extends WebSocketMessage {
  type: 'notification';
  payload: {
    message: string;
    level: 'info' | 'warning' | 'error' | 'success';
    persistent?: boolean;
  };
}

// Rate Limiting Types
export interface RateLimitHeaders {
  'x-ratelimit-limit': number;
  'x-ratelimit-remaining': number;
  'x-ratelimit-reset': number;
  'x-ratelimit-tier': SubscriptionTier;
}

// API Client Configuration
export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  enableOfflineSupport?: boolean;
  enableWebSockets?: boolean;
  websocketURL?: string;
}

// Storage Types (for offline support)
export interface StoredRequest {
  id: string;
  method: string;
  url: string;
  data?: any;
  headers?: Record<string, string>;
  timestamp: string;
  retryCount: number;
  maxRetries: number;
}

export interface OfflineQueueItem extends StoredRequest {
  priority: 'low' | 'medium' | 'high';
  dependencies?: string[];
}

// Custom Hook Types
export interface UseApiQuery<T> {
  data: T | undefined;
  error: Error | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  refetch: () => Promise<T>;
}

export interface UseApiMutation<TData, TVariables> {
  mutate: (variables: TVariables) => Promise<TData>;
  mutateAsync: (variables: TVariables) => Promise<TData>;
  data: TData | undefined;
  error: Error | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  reset: () => void;
}

// Error Types
export enum ApiErrorCode {
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNAUTHORIZED = 'UNAUTHORIZED',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  NOT_FOUND = 'NOT_FOUND',
  RATE_LIMITED = 'RATE_LIMITED',
  QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',
  SERVER_ERROR = 'SERVER_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
}

export class ApiError extends Error {
  constructor(
    public code: ApiErrorCode,
    message: string,
    public status?: number,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Type Guards
export const isApiResponse = (data: any): data is ApiResponse => {
  return data && typeof data === 'object' && 'success' in data && 'timestamp' in data;
};

export const isPaginatedResponse = (data: any): data is PaginatedResponse => {
  return data && typeof data === 'object' && 'data' in data && 'meta' in data;
};

export const isErrorResponse = (data: any): data is ErrorResponse => {
  return data && typeof data === 'object' && 'error' in data && 'message' in data;
};