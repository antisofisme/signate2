export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: 'admin' | 'user' | 'viewer'
  tenantId: string
  createdAt: string
  updatedAt: string
  lastLogin?: string
  isActive: boolean
}

export interface Tenant {
  id: string
  name: string
  slug: string
  logo?: string
  settings: TenantSettings
  createdAt: string
  updatedAt: string
  ownerId: string
  plan: 'free' | 'pro' | 'enterprise'
}

export interface TenantSettings {
  allowFileUpload: boolean
  maxFileSize: number
  allowedFileTypes: string[]
  brandingColor: string
  customDomain?: string
}

export interface Asset {
  id: string
  name: string
  type: 'image' | 'video' | 'document' | 'audio'
  url: string
  thumbnailUrl?: string
  size: number
  mimeType: string
  metadata: AssetMetadata
  tenantId: string
  uploadedBy: string
  createdAt: string
  updatedAt: string
  isPublic: boolean
  tags: string[]
}

export interface AssetMetadata {
  width?: number
  height?: number
  duration?: number
  description?: string
  altText?: string
  [key: string]: any
}

export interface Screen {
  id: string
  name: string
  deviceId: string
  resolution: {
    width: number
    height: number
  }
  location: string
  status: 'online' | 'offline' | 'error'
  lastSeen: string
  tenantId: string
  currentPlaylist?: string
  settings: ScreenSettings
}

export interface ScreenSettings {
  orientation: 'landscape' | 'portrait'
  sleepSchedule?: {
    enabled: boolean
    sleepTime: string
    wakeTime: string
  }
  volume: number
  brightness: number
}

export interface Playlist {
  id: string
  name: string
  description?: string
  assets: PlaylistAsset[]
  duration: number
  isActive: boolean
  tenantId: string
  createdBy: string
  createdAt: string
  updatedAt: string
  schedules: PlaylistSchedule[]
}

export interface PlaylistAsset {
  id: string
  assetId: string
  duration: number
  order: number
  transition?: 'fade' | 'slide' | 'none'
}

export interface PlaylistSchedule {
  id: string
  name: string
  startDate: string
  endDate: string
  startTime: string
  endTime: string
  daysOfWeek: number[]
  isActive: boolean
}

export interface DashboardStats {
  totalScreens: number
  onlineScreens: number
  totalAssets: number
  totalPlaylists: number
  storageUsed: number
  storageLimit: number
  recentActivity: Activity[]
}

export interface Activity {
  id: string
  type: 'asset_uploaded' | 'screen_connected' | 'playlist_created' | 'user_logged_in'
  description: string
  userId: string
  userName: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T = any> {
  data: T[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

export interface FileUploadProgress {
  id: string
  file: File
  progress: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
}

export interface SearchFilters {
  query?: string
  type?: string
  tags?: string[]
  dateFrom?: string
  dateTo?: string
  size?: {
    min?: number
    max?: number
  }
  user?: string
}

export interface TableColumn<T = any> {
  key: keyof T
  label: string
  sortable?: boolean
  width?: string
  render?: (value: any, row: T) => React.ReactNode
}

export interface DataTableProps<T = any> {
  data: T[]
  columns: TableColumn<T>[]
  loading?: boolean
  pagination?: {
    page: number
    limit: number
    total: number
    onPageChange: (page: number) => void
  }
  sorting?: {
    column: keyof T
    direction: 'asc' | 'desc'
    onSort: (column: keyof T, direction: 'asc' | 'desc') => void
  }
  selection?: {
    selectedIds: string[]
    onSelectionChange: (ids: string[]) => void
  }
}

export type Theme = 'light' | 'dark' | 'system'

// UI Component Types
export interface ErrorProps {
  title?: string;
  message?: string;
  error?: Error;
  onRetry?: () => void;
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
  children?: React.ReactNode;
}

// Re-export types from api.ts
export type { UserRole, NavigationItem } from './api'