# Anthias Frontend Architecture Design

## System Overview

This document outlines the modern frontend architecture for the Anthias digital signage management system using Next.js 14+ with App Router, ShadCN UI components, and TypeScript.

## Backend Analysis Summary

Based on the backend analysis, Anthias provides the following core capabilities:

### Core Features Identified:
1. **Asset Management**: Upload, edit, delete digital assets (images, videos, web content)
2. **Playlist Management**: Order and schedule content playback
3. **Device Management**: System information, settings, and control
4. **Authentication**: User authentication and authorization
5. **System Control**: Reboot, shutdown, backup, recovery operations
6. **Real-time Updates**: WebSocket support for live content updates
7. **Integrations**: Balena and other platform integrations

### API Endpoints (v2):
- `/v2/assets` - Asset CRUD operations
- `/v2/assets/order` - Playlist management
- `/v2/assets/control` - Asset playback control
- `/v2/device_settings` - Device configuration
- `/v2/info` - System information
- `/v2/integrations` - Platform integrations
- `/v2/backup` - Backup operations

## Frontend Architecture Design

### Technology Stack

- **Framework**: Next.js 14+ with App Router
- **UI Components**: ShadCN UI with Radix UI primitives
- **Styling**: Tailwind CSS
- **Type Safety**: TypeScript
- **State Management**: Zustand (lightweight) + React Query (server state)
- **Real-time**: Socket.IO client for WebSocket connections
- **Form Handling**: React Hook Form with Zod validation
- **API Client**: Axios with TypeScript interfaces

### Project Structure

```
anthias-frontend/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (auth)/                   # Route groups
│   │   │   ├── login/
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/              # Protected routes
│   │   │   ├── dashboard/
│   │   │   │   ├── page.tsx
│   │   │   │   └── loading.tsx
│   │   │   ├── assets/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── [id]/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── edit/page.tsx
│   │   │   │   └── upload/page.tsx
│   │   │   ├── playlists/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── devices/
│   │   │   │   ├── page.tsx
│   │   │   │   └── settings/page.tsx
│   │   │   ├── system/
│   │   │   │   ├── info/page.tsx
│   │   │   │   ├── backup/page.tsx
│   │   │   │   └── integrations/page.tsx
│   │   │   └── layout.tsx
│   │   ├── api/                      # API routes (if needed)
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   ├── loading.tsx
│   │   ├── error.tsx
│   │   └── not-found.tsx
│   ├── components/                   # Reusable components
│   │   ├── ui/                       # ShadCN UI components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── form.tsx
│   │   │   ├── input.tsx
│   │   │   ├── table.tsx
│   │   │   └── ...
│   │   ├── layout/                   # Layout components
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   ├── breadcrumb.tsx
│   │   │   └── navigation.tsx
│   │   ├── features/                 # Feature-specific components
│   │   │   ├── assets/
│   │   │   │   ├── asset-list.tsx
│   │   │   │   ├── asset-card.tsx
│   │   │   │   ├── asset-upload.tsx
│   │   │   │   ├── asset-preview.tsx
│   │   │   │   └── asset-form.tsx
│   │   │   ├── playlists/
│   │   │   │   ├── playlist-manager.tsx
│   │   │   │   ├── playlist-item.tsx
│   │   │   │   └── playlist-reorder.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── stats-cards.tsx
│   │   │   │   ├── recent-activity.tsx
│   │   │   │   └── system-status.tsx
│   │   │   ├── devices/
│   │   │   │   ├── device-info.tsx
│   │   │   │   ├── device-settings.tsx
│   │   │   │   └── device-controls.tsx
│   │   │   └── auth/
│   │   │       ├── login-form.tsx
│   │   │       └── auth-guard.tsx
│   │   └── common/                   # Common components
│   │       ├── loading-spinner.tsx
│   │       ├── error-boundary.tsx
│   │       ├── confirm-dialog.tsx
│   │       └── status-badge.tsx
│   ├── lib/                          # Utilities and configuration
│   │   ├── api/                      # API layer
│   │   │   ├── client.ts
│   │   │   ├── endpoints.ts
│   │   │   ├── types.ts
│   │   │   └── queries/
│   │   │       ├── assets.ts
│   │   │       ├── playlists.ts
│   │   │       ├── devices.ts
│   │   │       └── system.ts
│   │   ├── auth/
│   │   │   ├── config.ts
│   │   │   └── middleware.ts
│   │   ├── store/                    # State management
│   │   │   ├── auth-store.ts
│   │   │   ├── ui-store.ts
│   │   │   └── websocket-store.ts
│   │   ├── hooks/                    # Custom hooks
│   │   │   ├── use-auth.ts
│   │   │   ├── use-websocket.ts
│   │   │   ├── use-assets.ts
│   │   │   └── use-debounce.ts
│   │   ├── utils/
│   │   │   ├── cn.ts                 # Class name utility
│   │   │   ├── format.ts
│   │   │   ├── validation.ts
│   │   │   └── constants.ts
│   │   ├── websocket/
│   │   │   ├── client.ts
│   │   │   └── handlers.ts
│   │   └── types/                    # TypeScript definitions
│   │       ├── api.ts
│   │       ├── auth.ts
│   │       ├── assets.ts
│   │       ├── devices.ts
│   │       └── global.ts
│   ├── styles/
│   │   └── globals.css
│   └── middleware.ts                 # Next.js middleware
├── public/
│   ├── icons/
│   └── images/
├── docs/
├── .env.local
├── .env.example
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── package.json
└── README.md
```

## Component Architecture

### 1. Layout Components

#### Sidebar Navigation
```typescript
// components/layout/sidebar.tsx
interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType;
  badge?: number;
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Assets', href: '/assets', icon: PhotoIcon },
  { name: 'Playlists', href: '/playlists', icon: PlayIcon },
  { name: 'Devices', href: '/devices', icon: DevicePhoneMobileIcon },
  { name: 'System', href: '/system', icon: CogIcon },
];
```

#### Header Component
```typescript
// components/layout/header.tsx
interface HeaderProps {
  title: string;
  actions?: React.ReactNode;
  breadcrumb?: BreadcrumbItem[];
}
```

### 2. Feature Components

#### Asset Management
```typescript
// components/features/assets/asset-list.tsx
interface AssetListProps {
  assets: Asset[];
  onEdit: (asset: Asset) => void;
  onDelete: (assetId: string) => void;
  onPreview: (asset: Asset) => void;
}

// components/features/assets/asset-upload.tsx
interface AssetUploadProps {
  onUpload: (file: File, metadata: AssetMetadata) => Promise<void>;
  acceptedTypes: string[];
  maxSize: number;
}
```

#### Playlist Management
```typescript
// components/features/playlists/playlist-manager.tsx
interface PlaylistManagerProps {
  assets: Asset[];
  activeAssets: string[];
  onReorder: (assetIds: string[]) => void;
  onToggleAsset: (assetId: string) => void;
}
```

## API Integration Layer

### API Client Configuration
```typescript
// lib/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Type-Safe API Hooks
```typescript
// lib/api/queries/assets.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export const useAssets = () => {
  return useQuery({
    queryKey: ['assets'],
    queryFn: () => apiClient.get<Asset[]>('/api/v2/assets').then(res => res.data),
  });
};

export const useCreateAsset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAssetRequest) =>
      apiClient.post<Asset>('/api/v2/assets', data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });
};
```

## State Management Architecture

### Auth Store (Zustand)
```typescript
// lib/store/auth-store.ts
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  login: async (username, password) => {
    // Login logic
  },
  logout: () => {
    // Logout logic
  },
}));
```

### UI Store
```typescript
// lib/store/ui-store.ts
interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notifications: Notification[];
  toggleSidebar: () => void;
  addNotification: (notification: Notification) => void;
}
```

## Real-time Updates (WebSocket)

### WebSocket Client
```typescript
// lib/websocket/client.ts
class WebSocketClient {
  private socket: Socket | null = null;

  connect() {
    this.socket = io(process.env.NEXT_PUBLIC_WS_URL);

    this.socket.on('asset_updated', (data) => {
      // Handle asset updates
    });

    this.socket.on('playlist_changed', (data) => {
      // Handle playlist changes
    });
  }
}
```

### WebSocket Hook
```typescript
// lib/hooks/use-websocket.ts
export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const client = new WebSocketClient();
    client.connect();

    return () => client.disconnect();
  }, []);

  return { isConnected };
};
```

## Type Definitions

### Core Types
```typescript
// lib/types/assets.ts
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
  nocache: boolean;
  play_order: number;
  skip_asset_check: boolean;
}

export interface CreateAssetRequest {
  name: string;
  uri: string;
  duration?: number;
  start_date?: string;
  end_date?: string;
  is_enabled?: boolean;
}

export interface UpdateAssetRequest extends Partial<CreateAssetRequest> {
  play_order?: number;
}
```

### Device Types
```typescript
// lib/types/devices.ts
export interface DeviceSettings {
  player_name: string;
  audio_output: string;
  default_duration: number;
  default_streaming_duration: number;
  date_format: string;
  auth_backend: string;
  show_splash: boolean;
  default_assets: boolean;
  shuffle_playlist: boolean;
  use_24_hour_clock: boolean;
  debug_logging: boolean;
  username?: string;
}

export interface SystemInfo {
  viewlog: string;
  loadavg: number;
  free_space: string;
  display_power: string | null;
  up_to_date: boolean;
  anthias_version: string;
  device_model: string;
  uptime: {
    days: number;
    hours: number;
  };
  memory: {
    total: number;
    used: number;
    free: number;
    shared: number;
    buff: number;
    available: number;
  };
  ip_addresses: string[];
  mac_address: string;
  host_user: string;
}
```

## Security Considerations

### Authentication Middleware
```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token')?.value;

  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/assets/:path*', '/playlists/:path*']
};
```

### CSRF Protection
```typescript
// lib/api/client.ts
// Add CSRF token to requests
apiClient.interceptors.request.use((config) => {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});
```

## Performance Optimizations

### Code Splitting
- Route-based code splitting with Next.js App Router
- Component-level lazy loading for heavy components
- Dynamic imports for feature modules

### Caching Strategy
- React Query for server state caching
- Next.js built-in caching for static assets
- Service Worker for offline functionality

### Bundle Optimization
- Tree shaking with ES modules
- Dynamic imports for vendor libraries
- Image optimization with Next.js Image component

## Development Workflow

### Environment Setup
```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local

# Run development server
npm run dev

# Run tests
npm run test

# Build for production
npm run build
```

### Code Quality
- ESLint + Prettier for code formatting
- Husky for pre-commit hooks
- Jest + Testing Library for unit tests
- Playwright for E2E testing

## Deployment Considerations

### Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=http://localhost:3000
```

### Docker Configuration
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

This architecture provides a scalable, maintainable frontend that maps directly to the Anthias backend capabilities while leveraging modern React patterns and best practices.