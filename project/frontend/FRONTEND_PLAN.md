# Signate Frontend Development Plan
## Modern UI Replacement for Anthias Digital Signage

**Base Analysis:** Anthias Backend (Django REST API + WebSocket)
**Tech Stack:** Next.js 14 + ShadCN UI + Tailwind CSS + TypeScript
**Architecture:** Modular, Component-Based, Type-Safe

---

## 📋 **Backend Analysis Summary**

### Current Anthias Backend Structure
- **Django REST Framework** with API v2 (`/api/v2/`)
- **Single Asset Model** (images, videos, web content)
- **Playlist System** via `is_enabled` + `play_order` fields
- **Real-time Updates** via ZeroMQ WebSocket
- **Optional Authentication** with Basic Auth
- **File Upload** with progress tracking

### Key API Endpoints
```
GET/POST   /api/v2/assets/          # Asset CRUD
PUT/DELETE /api/v2/assets/:id/      # Asset management
POST       /api/v2/assets/upload/   # File upload
GET/POST   /api/v2/settings/        # Device configuration
GET        /api/v2/info/            # System information
POST       /api/v2/system/reboot/   # System controls
```

### Data Models
```typescript
interface Asset {
  id: string;
  name: string;
  mimetype: string;
  uri: string;
  duration: number;
  play_order: number;
  is_enabled: boolean;
  start_date: string;
  end_date: string;
}

interface DeviceSettings {
  player_name: string;
  hdmi_mode: number;
  audio_output: string;
  default_duration: number;
  use_24h_clock: boolean;
}
```

---

## 🏗️ **Frontend Architecture Plan**

### Project Structure
```
project/frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Authentication routes
│   │   ├── login/
│   │   └── layout.tsx
│   ├── dashboard/                # Main dashboard
│   ├── assets/                   # Asset management
│   │   ├── page.tsx
│   │   ├── upload/
│   │   └── [id]/
│   ├── playlists/                # Playlist management
│   ├── devices/                  # Device settings
│   ├── system/                   # System information
│   ├── globals.css               # Tailwind CSS
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Home page
├── components/                   # Reusable components
│   ├── ui/                       # ShadCN UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── form.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   └── toast.tsx
│   ├── layout/                   # Layout components
│   │   ├── header.tsx
│   │   ├── sidebar.tsx
│   │   ├── navigation.tsx
│   │   └── breadcrumb.tsx
│   ├── assets/                   # Asset-specific components
│   │   ├── asset-card.tsx
│   │   ├── asset-list.tsx
│   │   ├── upload-zone.tsx
│   │   ├── asset-preview.tsx
│   │   └── asset-form.tsx
│   ├── playlists/                # Playlist components
│   │   ├── playlist-builder.tsx
│   │   ├── drag-drop-list.tsx
│   │   └── schedule-picker.tsx
│   ├── devices/                  # Device management
│   │   ├── device-status.tsx
│   │   ├── settings-form.tsx
│   │   └── system-info.tsx
│   └── common/                   # Shared components
│       ├── loading-spinner.tsx
│       ├── error-boundary.tsx
│       ├── confirmation-dialog.tsx
│       └── data-table.tsx
├── lib/                          # Utilities & configurations
│   ├── api/                      # API integration
│   │   ├── client.ts             # HTTP client
│   │   ├── websocket.ts          # WebSocket client
│   │   ├── types.ts              # TypeScript definitions
│   │   └── endpoints.ts          # API endpoints
│   ├── auth/                     # Authentication
│   │   ├── provider.tsx
│   │   ├── middleware.ts
│   │   └── utils.ts
│   ├── hooks/                    # Custom React hooks
│   │   ├── use-assets.ts
│   │   ├── use-websocket.ts
│   │   ├── use-upload.ts
│   │   └── use-auth.ts
│   ├── store/                    # State management
│   │   ├── auth-store.ts         # Zustand auth store
│   │   ├── ui-store.ts           # UI preferences
│   │   └── websocket-store.ts    # Real-time events
│   ├── utils/                    # Helper functions
│   │   ├── cn.ts                 # Class name utility
│   │   ├── format.ts             # Data formatting
│   │   ├── validation.ts         # Form validation
│   │   └── file-utils.ts         # File handling
│   └── constants/                # App constants
│       ├── api-endpoints.ts
│       ├── file-types.ts
│       └── ui-constants.ts
├── types/                        # Global TypeScript types
│   ├── api.ts                    # API response types
│   ├── auth.ts                   # Authentication types
│   ├── assets.ts                 # Asset types
│   └── global.d.ts               # Global declarations
├── public/                       # Static assets
│   ├── icons/
│   ├── images/
│   └── favicon.ico
├── docs/                         # Documentation
│   ├── component-guide.md
│   ├── api-integration.md
│   └── deployment.md
├── package.json                  # Dependencies
├── next.config.js                # Next.js configuration
├── tailwind.config.js            # Tailwind CSS config
├── tsconfig.json                 # TypeScript config
├── components.json               # ShadCN UI config
└── README.md                     # Project documentation
```

---

## 🎨 **Design System & Components**

### ShadCN UI Component Library
```typescript
// Core UI Components (from ShadCN)
- Button (variants: default, destructive, outline, secondary)
- Card (header, content, footer)
- Dialog/Modal (responsive, accessible)
- Form (with validation, error handling)
- Input (text, file, number, date)
- Table (sortable, filterable, paginated)
- Toast (success, error, warning, info)
- Badge (status indicators)
- Avatar (user profiles)
- Dropdown Menu (actions, navigation)

// Custom Components
- AssetCard (thumbnail, metadata, actions)
- UploadZone (drag-and-drop file upload)
- PlaylistBuilder (drag-and-drop reordering)
- DeviceStatus (real-time system info)
- SchedulePicker (date/time selection)
```

### Tailwind CSS Design Tokens
```css
/* Color Palette */
--primary: #3b82f6;      /* Blue */
--secondary: #64748b;    /* Slate */
--success: #10b981;      /* Green */
--warning: #f59e0b;      /* Amber */
--error: #ef4444;        /* Red */
--background: #ffffff;    /* White */
--foreground: #0f172a;   /* Slate-900 */

/* Typography */
--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'Fira Code', monospace;

/* Spacing & Layout */
--container-max-width: 1200px;
--sidebar-width: 256px;
--header-height: 64px;
```

---

## 🔌 **API Integration Strategy**

### HTTP Client (Axios + React Query)
```typescript
// lib/api/client.ts
class AnthiasApiClient {
  private baseURL = 'http://localhost:8000/api/v2';

  // Asset Management
  async getAssets(): Promise<Asset[]>
  async createAsset(data: CreateAssetRequest): Promise<Asset>
  async updateAsset(id: string, data: UpdateAssetRequest): Promise<Asset>
  async deleteAsset(id: string): Promise<void>
  async uploadAsset(file: File, onProgress?: (progress: number) => void): Promise<Asset>

  // Device Settings
  async getSettings(): Promise<DeviceSettings>
  async updateSettings(data: Partial<DeviceSettings>): Promise<DeviceSettings>

  // System Information
  async getSystemInfo(): Promise<SystemInfo>
  async rebootSystem(): Promise<void>
}
```

### WebSocket Integration
```typescript
// lib/api/websocket.ts
class WebSocketManager {
  private ws: WebSocket;
  private eventHandlers: Map<string, Function[]>;

  // Real-time Events
  onAssetUpdate(callback: (asset: Asset) => void)
  onPlaylistChange(callback: (playlist: Asset[]) => void)
  onDeviceStatus(callback: (status: DeviceStatus) => void)

  // Connection Management
  connect(): Promise<void>
  disconnect(): void
  reconnect(): void
}
```

### Custom React Hooks
```typescript
// lib/hooks/use-assets.ts
export function useAssets() {
  const query = useQuery({
    queryKey: ['assets'],
    queryFn: () => apiClient.getAssets()
  });

  const createMutation = useMutation({
    mutationFn: apiClient.createAsset,
    onSuccess: () => queryClient.invalidateQueries(['assets'])
  });

  return {
    assets: query.data,
    isLoading: query.isLoading,
    error: query.error,
    createAsset: createMutation.mutate,
    isCreating: createMutation.isLoading
  };
}
```

---

## 🗂️ **Feature Modules**

### 1. Dashboard Module
```typescript
// app/dashboard/page.tsx
- System Overview (storage, CPU, memory)
- Recent Assets (last uploaded/modified)
- Playlist Status (currently playing)
- Device Health (online/offline status)
- Quick Actions (upload, create playlist)
- Analytics Charts (usage, performance)
```

### 2. Asset Management Module
```typescript
// app/assets/page.tsx
- Asset List (grid/table view toggle)
- Upload Zone (drag-and-drop)
- Asset Preview (image/video player)
- Metadata Editor (name, duration, schedule)
- Bulk Actions (enable/disable, delete)
- Search & Filter (type, date, status)
```

### 3. Playlist Management Module
```typescript
// app/playlists/page.tsx
- Drag-and-Drop Builder
- Schedule Configuration (start/end dates)
- Asset Duration Settings
- Preview Mode (playlist simulation)
- Publishing Controls (enable/disable)
- Playlist Templates
```

### 4. Device Settings Module
```typescript
// app/devices/page.tsx
- Display Configuration (resolution, rotation)
- Audio Settings (output, volume)
- Network Settings (WiFi, Ethernet)
- System Controls (reboot, shutdown)
- Update Management (firmware, app)
- Backup/Restore (configuration export)
```

### 5. System Information Module
```typescript
// app/system/page.tsx
- Hardware Information (CPU, RAM, storage)
- Network Status (IP, connectivity)
- Software Versions (OS, apps)
- Log Viewer (system, application)
- Performance Metrics (real-time charts)
- Diagnostics Tools (health checks)
```

---

## 🔐 **Authentication & Security**

### Authentication Flow
```typescript
// lib/auth/provider.tsx
- Session-based authentication (matching Anthias backend)
- Route protection middleware
- Automatic token refresh
- Logout handling
- Permission-based access control

// Middleware for protected routes
export function authMiddleware(request: NextRequest) {
  // Check authentication status
  // Redirect to login if unauthenticated
  // Allow access if authenticated
}
```

### Security Features
- CSRF protection for all API requests
- Input validation and sanitization
- File upload security (type/size validation)
- XSS protection (content sanitization)
- Secure session management

---

## 📱 **Responsive Design**

### Breakpoint Strategy
```css
/* Mobile First Design */
sm: '640px',   /* Small tablets */
md: '768px',   /* Tablets */
lg: '1024px',  /* Small laptops */
xl: '1280px',  /* Laptops */
2xl: '1536px'  /* Large monitors */
```

### Layout Adaptations
- **Mobile (< 768px)**: Bottom navigation, full-width cards
- **Tablet (768px - 1024px)**: Collapsible sidebar, grid layouts
- **Desktop (> 1024px)**: Fixed sidebar, multi-column layouts
- **Touch Optimizations**: Larger touch targets, gesture support

---

## 🚀 **Development Phases**

### Phase 1: Foundation (Week 1-2)
```bash
✅ Project setup (Next.js, TypeScript, Tailwind)
✅ ShadCN UI component installation
✅ Basic layout structure (header, sidebar, content)
✅ Authentication system setup
✅ API client configuration
✅ Routing structure with App Router
```

### Phase 2: Core Features (Week 3-5)
```bash
🔄 Asset Management (list, upload, edit, delete)
🔄 Basic Dashboard (overview, quick stats)
🔄 Device Settings (configuration forms)
🔄 WebSocket integration (real-time updates)
🔄 File upload with progress tracking
🔄 Basic responsive design
```

### Phase 3: Advanced Features (Week 6-8)
```bash
⏳ Playlist Management (drag-and-drop builder)
⏳ Advanced Asset Features (preview, scheduling)
⏳ System Information dashboard
⏳ Search & filtering capabilities
⏳ Bulk operations (multi-select actions)
⏳ Performance optimizations
```

### Phase 4: Polish & Optimization (Week 9-10)
```bash
⏳ UI/UX refinements
⏳ Error handling improvements
⏳ Loading states optimization
⏳ Mobile experience enhancement
⏳ Performance testing and optimization
⏳ Documentation completion
```

---

## 📦 **Dependencies**

### Core Dependencies
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "@radix-ui/react-*": "^1.0.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    "lucide-react": "^0.300.0"
  }
}
```

### State Management
```json
{
  "dependencies": {
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0"
  }
}
```

### Form & Validation
```json
{
  "dependencies": {
    "react-hook-form": "^7.48.0",
    "@hookform/resolvers": "^3.3.0",
    "zod": "^3.22.0"
  }
}
```

### File Upload & Media
```json
{
  "dependencies": {
    "react-dropzone": "^14.2.0",
    "react-player": "^2.13.0"
  }
}
```

### Development Tools
```json
{
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0",
    "prettier": "^3.0.0"
  }
}
```

---

## 🎯 **Success Metrics**

### Performance Goals
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Bundle Size**: < 500KB (gzipped)
- **API Response Time**: < 200ms average

### User Experience Goals
- **Mobile-friendly**: 100% responsive design
- **Accessibility**: WCAG 2.1 AA compliance
- **Real-time Updates**: < 100ms WebSocket latency
- **Upload Performance**: Support files up to 100MB

### Technical Goals
- **Type Safety**: 100% TypeScript coverage
- **Component Reusability**: 80% shared components
- **Code Quality**: ESLint + Prettier enforcement
- **Test Coverage**: 90% component testing

---

## 📚 **Documentation Plan**

### Developer Documentation
- **Component Library Guide**: ShadCN UI usage patterns
- **API Integration Guide**: Backend communication patterns
- **State Management Guide**: Zustand + React Query best practices
- **Deployment Guide**: Production build and deployment steps

### User Documentation
- **User Manual**: Feature-by-feature usage guide
- **Administrator Guide**: System configuration and maintenance
- **Troubleshooting Guide**: Common issues and solutions
- **API Reference**: Complete endpoint documentation

---

This comprehensive plan provides a roadmap for building a modern, scalable frontend that directly replaces and enhances the current Anthias React frontend while maintaining full compatibility with the existing Django backend API.