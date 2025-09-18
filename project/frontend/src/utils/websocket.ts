import { io, Socket } from 'socket.io-client';
import { toast } from 'react-hot-toast';
import {
  WebSocketMessage,
  AssetUpdateMessage,
  NotificationMessage,
  ApiError,
  ApiErrorCode
} from '../types/api';
import { getStorageItem } from './storage';
import { networkMonitor } from './network';

export interface WebSocketConfig {
  url: string;
  autoConnect?: boolean;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
  timeout?: number;
}

export type MessageHandler<T = any> = (message: T) => void;

export class WebSocketClient {
  private socket: Socket | null = null;
  private config: Required<WebSocketConfig>;
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private connectionPromise: Promise<void> | null = null;
  private isConnecting = false;
  private isDestroyed = false;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(config: WebSocketConfig) {
    this.config = {
      autoConnect: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 20000,
      ...config,
    };

    if (this.config.autoConnect) {
      this.connect();
    }

    // Listen for network changes
    networkMonitor?.addListener(this.handleNetworkChange.bind(this));
  }

  async connect(): Promise<void> {
    if (this.isDestroyed) {
      throw new Error('WebSocket client has been destroyed');
    }

    if (this.socket?.connected) {
      return Promise.resolve();
    }

    if (this.isConnecting && this.connectionPromise) {
      return this.connectionPromise;
    }

    this.isConnecting = true;
    this.connectionPromise = this._performConnection();

    try {
      await this.connectionPromise;
    } finally {
      this.isConnecting = false;
      this.connectionPromise = null;
    }
  }

  private async _performConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Get authentication token
        const accessToken = getStorageItem('access_token');
        const tenantSlug = getStorageItem('current_tenant_slug');

        this.socket = io(this.config.url, {
          auth: {
            token: accessToken,
            tenant_slug: tenantSlug,
          },
          timeout: this.config.timeout,
          reconnectionAttempts: this.config.reconnectionAttempts,
          reconnectionDelay: this.config.reconnectionDelay,
          transports: ['websocket', 'polling'],
        });

        // Connection event handlers
        this.socket.on('connect', () => {
          console.log('WebSocket connected');
          this.startHeartbeat();
          resolve();
        });

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          this.handleConnectionError(error);
          reject(new ApiError(
            ApiErrorCode.NETWORK_ERROR,
            `WebSocket connection failed: ${error.message}`
          ));
        });

        this.socket.on('disconnect', (reason) => {
          console.log('WebSocket disconnected:', reason);
          this.stopHeartbeat();

          if (reason === 'io server disconnect') {
            // Server-initiated disconnect, try to reconnect
            setTimeout(() => {
              if (!this.isDestroyed) {
                this.connect();
              }
            }, this.config.reconnectionDelay);
          }
        });

        this.socket.on('reconnect', (attemptNumber) => {
          console.log(`WebSocket reconnected after ${attemptNumber} attempts`);
          toast.success('Connection restored');
        });

        this.socket.on('reconnect_error', (error) => {
          console.error('WebSocket reconnection error:', error);
        });

        this.socket.on('reconnect_failed', () => {
          console.error('WebSocket reconnection failed');
          toast.error('Unable to establish real-time connection');
        });

        // Message handlers
        this.socket.on('message', this.handleMessage.bind(this));
        this.socket.on('asset_updated', this.handleAssetUpdate.bind(this));
        this.socket.on('notification', this.handleNotification.bind(this));
        this.socket.on('error', this.handleServerError.bind(this));

        // Authentication events
        this.socket.on('auth_error', (error) => {
          console.error('WebSocket authentication error:', error);
          toast.error('Authentication failed. Please log in again.');
        });

        this.socket.on('tenant_switched', (data) => {
          console.log('Tenant context switched:', data);
          // Refresh the connection with new tenant context
          this.disconnect();
          setTimeout(() => this.connect(), 1000);
        });

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }

    this.stopHeartbeat();
  }

  destroy(): void {
    this.isDestroyed = true;
    this.disconnect();
    this.messageHandlers.clear();
    networkMonitor.removeListener(this.handleNetworkChange.bind(this));
  }

  // Message handling
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    }

    // Also trigger 'all' handlers
    const allHandlers = this.messageHandlers.get('*');
    if (allHandlers) {
      allHandlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in universal message handler:', error);
        }
      });
    }
  }

  private handleAssetUpdate(message: AssetUpdateMessage): void {
    console.log('Asset updated:', message.payload);
    this.handleMessage(message);
  }

  private handleNotification(message: NotificationMessage): void {
    const { payload } = message;

    // Show toast notification
    switch (payload.level) {
      case 'success':
        toast.success(payload.message);
        break;
      case 'warning':
        toast(payload.message, { icon: '⚠️' });
        break;
      case 'error':
        toast.error(payload.message);
        break;
      case 'info':
      default:
        toast(payload.message);
        break;
    }

    this.handleMessage(message);
  }

  private handleServerError(error: any): void {
    console.error('WebSocket server error:', error);
    toast.error('Real-time connection error occurred');
  }

  private handleConnectionError(error: any): void {
    if (error.type === 'TransportError') {
      console.log('WebSocket transport error, will retry...');
    } else if (error.message?.includes('auth')) {
      toast.error('Authentication failed. Please log in again.');
    } else {
      console.error('WebSocket connection error:', error);
    }
  }

  private handleNetworkChange(isOnline: boolean): void {
    if (isOnline && !this.socket?.connected) {
      console.log('Network restored, reconnecting WebSocket...');
      this.connect();
    }
  }

  // Heartbeat to keep connection alive
  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatInterval = setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit('ping');
      }
    }, 30000); // Send ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // Public API
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // Subscribe to message types
  subscribe<T = any>(messageType: string, handler: MessageHandler<T>): () => void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set());
    }

    this.messageHandlers.get(messageType)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.messageHandlers.delete(messageType);
        }
      }
    };
  }

  // Subscribe to all messages
  subscribeToAll<T = any>(handler: MessageHandler<T>): () => void {
    return this.subscribe('*', handler);
  }

  // Send message to server
  async emit(event: string, data?: any): Promise<void> {
    if (!this.socket?.connected) {
      await this.connect();
    }

    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      throw new ApiError(
        ApiErrorCode.NETWORK_ERROR,
        'WebSocket is not connected'
      );
    }
  }

  // Join room (for multi-tenant support)
  async joinRoom(room: string): Promise<void> {
    await this.emit('join_room', { room });
  }

  // Leave room
  async leaveRoom(room: string): Promise<void> {
    await this.emit('leave_room', { room });
  }

  // Get connection status
  getStatus(): {
    connected: boolean;
    connecting: boolean;
    transport?: string;
    ping?: number;
  } {
    return {
      connected: this.socket?.connected || false,
      connecting: this.isConnecting,
      transport: this.socket?.io.engine.transport.name,
      ping: this.socket?.ping,
    };
  }

  // Update authentication (when token refreshes)
  updateAuth(accessToken: string, tenantSlug?: string): void {
    if (this.socket?.connected) {
      this.socket.auth = {
        token: accessToken,
        tenant_slug: tenantSlug,
      };

      // Re-authenticate with server
      this.socket.emit('authenticate', {
        token: accessToken,
        tenant_slug: tenantSlug,
      });
    }
  }
}

// Global WebSocket client instance
export const webSocketClient = typeof window !== 'undefined' ? new WebSocketClient({
  url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  autoConnect: false, // Don't auto-connect until user is authenticated
}) : null;

// Convenience hooks for React components
export const useWebSocket = () => {
  const subscribe = <T = any>(messageType: string, handler: MessageHandler<T>) => {
    return webSocketClient?.subscribe(messageType, handler);
  };

  const subscribeToAll = <T = any>(handler: MessageHandler<T>) => {
    return webSocketClient?.subscribeToAll(handler);
  };

  const emit = (event: string, data?: any) => {
    return webSocketClient?.emit(event, data);
  };

  const connect = () => webSocketClient?.connect();
  const disconnect = () => webSocketClient?.disconnect();
  const isConnected = () => webSocketClient?.isConnected() || false;
  const getStatus = () => webSocketClient?.getStatus() || 'disconnected';

  return {
    subscribe,
    subscribeToAll,
    emit,
    connect,
    disconnect,
    isConnected,
    getStatus,
  };
};

// Asset-specific WebSocket hooks
export const useAssetUpdates = (onAssetUpdate: (asset: any) => void) => {
  const { subscribe } = useWebSocket();

  React.useEffect(() => {
    const unsubscribe = subscribe('asset_updated', (message: AssetUpdateMessage) => {
      onAssetUpdate(message.payload);
    });

    return unsubscribe;
  }, [onAssetUpdate, subscribe]);
};

// Notification WebSocket hooks
export const useNotifications = (onNotification?: (notification: any) => void) => {
  const { subscribe } = useWebSocket();

  React.useEffect(() => {
    if (!onNotification) return;

    const unsubscribe = subscribe('notification', (message: NotificationMessage) => {
      onNotification(message.payload);
    });

    return unsubscribe;
  }, [onNotification, subscribe]);
};

export default webSocketClient;