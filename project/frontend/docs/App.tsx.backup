import React, { useEffect } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { BrowserRouter as Router } from 'react-router-dom';

import { queryClient } from './lib/react-query';
import { useAuthState } from './hooks/auth';
import { webSocketClient } from './utils/websocket';
import { offlineQueueManager } from './utils/offline-queue';
import { networkMonitor } from './utils/network';
import ErrorBoundary from './components/ErrorBoundary';

// Main App Router (you'll implement your routing here)
const AppRouter: React.FC = () => {
  const { isAuthenticated, isInitialized, user, tenant } = useAuthState();

  // Initialize WebSocket when authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      webSocketClient.connect().catch(console.error);

      // Join tenant room if available
      if (tenant) {
        webSocketClient.joinRoom(`tenant-${tenant.slug}`).catch(console.error);
      }
    } else {
      webSocketClient.disconnect();
    }

    return () => {
      if (tenant) {
        webSocketClient.leaveRoom(`tenant-${tenant.slug}`).catch(console.error);
      }
    };
  }, [isAuthenticated, user, tenant]);

  // Handle network status changes
  useEffect(() => {
    const handleOnline = () => {
      console.log('Network connection restored');
      // Process offline queue
      offlineQueueManager.processQueue();
    };

    const handleOffline = () => {
      console.log('Network connection lost');
    };

    networkMonitor.addListener((isOnline) => {
      if (isOnline) {
        handleOnline();
      } else {
        handleOffline();
      }
    });

    return () => {
      // networkMonitor cleanup is handled in its own class
    };
  }, []);

  // Show loading screen while initializing
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing application...</p>
        </div>
      </div>
    );
  }

  // Your routing logic would go here
  // For now, showing a simple authenticated/unauthenticated state
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Anthias Digital Signage
            </h1>
            <p className="text-gray-600 mb-6">
              Please log in to access your digital signage dashboard.
            </p>
            <button className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 transition-colors">
              Sign In
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="border-b border-gray-200 pb-4 mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, {user?.first_name || user?.username}!
            </h1>
            {tenant && (
              <p className="text-gray-600 mt-1">
                Current organization: {tenant.name}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Assets Overview */}
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                Assets
              </h3>
              <p className="text-3xl font-bold text-blue-600">
                {tenant?.asset_count || 0}
              </p>
              <p className="text-blue-700 text-sm">Total assets</p>
            </div>

            {/* Users Overview */}
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-900 mb-2">
                Team Members
              </h3>
              <p className="text-3xl font-bold text-green-600">
                {tenant?.user_count || 0}
              </p>
              <p className="text-green-700 text-sm">Active users</p>
            </div>

            {/* Storage Overview */}
            <div className="bg-purple-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-purple-900 mb-2">
                Storage Used
              </h3>
              <p className="text-3xl font-bold text-purple-600">
                {Math.round((tenant?.quota_usage.storage_used_mb || 0) / 1024 * 100) / 100}GB
              </p>
              <p className="text-purple-700 text-sm">of available storage</p>
            </div>
          </div>

          {/* API Integration Status */}
          <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">
                  API Integration Complete
                </h3>
                <div className="mt-1 text-sm text-green-700">
                  <p>
                    ✅ JWT Authentication with auto-refresh<br/>
                    ✅ Zustand state management with persistence<br/>
                    ✅ Real-time WebSocket connections<br/>
                    ✅ React Query caching and synchronization<br/>
                    ✅ Offline support with background sync<br/>
                    ✅ Type-safe API client with error handling
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <Router>
          <div className="App">
            <AppRouter />

            {/* Toast notifications */}
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#10B981',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#EF4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </div>
        </Router>

        {/* React Query Devtools (development only) */}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;