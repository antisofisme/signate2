# Anthias Frontend

A Next.js 14 frontend application for the Anthias multi-tenant SaaS platform.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript with strict configuration
- **Styling**: Tailwind CSS + ShadCN UI components
- **State Management**: Zustand with persistence
- **Authentication**: JWT tokens with refresh
- **API Client**: Axios with interceptors
- **UI Components**: Radix UI primitives
- **Icons**: Lucide React
- **Form Handling**: React Hook Form + Zod validation

## Project Structure

```
src/
├── app/                    # Next.js app router pages
├── components/
│   ├── ui/                # ShadCN UI components
│   ├── auth/              # Authentication components
│   ├── layout/            # Layout components
│   └── dashboard/         # Dashboard-specific components
├── lib/
│   ├── api.ts             # API client configuration
│   └── utils.ts           # Utility functions
├── store/
│   ├── authStore.ts       # Authentication state
│   └── appStore.ts        # Application state
├── types/
│   └── index.ts           # TypeScript type definitions
└── styles/
    └── globals.css        # Global styles and CSS variables
```

## Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Environment setup**:
   ```bash
   cp .env.example .env.local
   # Update the API URL to point to your backend
   ```

3. **Development server**:
   ```bash
   npm run dev
   ```

4. **Build for production**:
   ```bash
   npm run build
   npm start
   ```

## Key Features

### Authentication System
- JWT-based authentication with refresh tokens
- Protected routes with role-based access control
- Automatic token refresh via Axios interceptors
- Persistent authentication state with Zustand

### State Management
- **Auth Store**: User authentication and profile management
- **App Store**: Theme, sidebar, notifications, and preferences
- Persistent state across browser sessions

### UI Components
- Complete ShadCN UI component library
- Dark/light mode support with system preference detection
- Responsive design with mobile-first approach
- Loading states and error handling components

### API Integration
- Axios client with request/response interceptors
- Automatic authentication header injection
- Error handling and API response transformation
- Backend integration for all API v3 endpoints

### Dashboard Layout
- Responsive sidebar with collapse functionality
- Header with search, notifications, and user menu
- Role-based navigation and access control
- Mobile-optimized layout with overlay sidebar

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check
- `npm test` - Run Jest tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Generate test coverage report

## Architecture Decisions

### Why Next.js 14?
- Latest app router for better performance and DX
- Built-in TypeScript support
- Server-side rendering capabilities
- Excellent developer experience

### Why Zustand?
- Lightweight state management solution
- TypeScript-first design
- Persistence middleware support
- Simpler than Redux for our use case

### Why ShadCN UI?
- Accessible components built on Radix UI
- Customizable design system
- TypeScript support out of the box
- Modern styling with Tailwind CSS

### Why Axios over Fetch?
- Built-in request/response interceptors
- Better error handling
- Request/response transformation
- Automatic JSON parsing

## Integration with Backend

This frontend integrates with the Anthias backend API v3:

- **Authentication**: `/api/v3/auth/*`
- **Content Management**: `/api/v3/content/*`
- **User Management**: `/api/v3/users/*`
- **Tenant Settings**: `/api/v3/tenant/*`
- **Dashboard**: `/api/v3/dashboard/*`

## Development Guidelines

1. **Component Structure**: Use the established component patterns
2. **Type Safety**: Maintain strict TypeScript usage
3. **Error Handling**: Implement proper error boundaries
4. **Accessibility**: Follow WCAG guidelines
5. **Performance**: Optimize for Core Web Vitals
6. **Testing**: Write tests for critical user flows

## Deployment

The frontend can be deployed to any platform that supports Next.js:

- **Vercel** (recommended for Next.js apps)
- **Netlify**
- **AWS Amplify**
- **Traditional hosting** with Node.js

Make sure to set the appropriate environment variables for production deployment.