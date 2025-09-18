// Network utility functions for connectivity detection and monitoring

export const isOnline = (): boolean => {
  if (typeof navigator === 'undefined') return true;
  return navigator.onLine;
};

export const addOnlineListener = (callback: () => void): void => {
  if (typeof window === 'undefined') return;
  window.addEventListener('online', callback);
};

export const addOfflineListener = (callback: () => void): void => {
  if (typeof window === 'undefined') return;
  window.addEventListener('offline', callback);
};

export const removeOnlineListener = (callback: () => void): void => {
  if (typeof window === 'undefined') return;
  window.removeEventListener('online', callback);
};

export const removeOfflineListener = (callback: () => void): void => {
  if (typeof window === 'undefined') return;
  window.removeEventListener('offline', callback);
};

// Network status monitoring hook-like utility
export class NetworkMonitor {
  private listeners: Set<(isOnline: boolean) => void> = new Set();
  private isCurrentlyOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;

  constructor() {
    if (typeof window === 'undefined') return;

    this.handleOnline = this.handleOnline.bind(this);
    this.handleOffline = this.handleOffline.bind(this);

    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
  }

  private handleOnline(): void {
    this.isCurrentlyOnline = true;
    this.notifyListeners(true);
  }

  private handleOffline(): void {
    this.isCurrentlyOnline = false;
    this.notifyListeners(false);
  }

  private notifyListeners(isOnline: boolean): void {
    this.listeners.forEach(listener => listener(isOnline));
  }

  addListener(callback: (isOnline: boolean) => void): void {
    this.listeners.add(callback);
  }

  removeListener(callback: (isOnline: boolean) => void): void {
    this.listeners.delete(callback);
  }

  getStatus(): boolean {
    return this.isCurrentlyOnline;
  }

  destroy(): void {
    if (typeof window === 'undefined') return;
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    this.listeners.clear();
  }
}

// Global network monitor instance - only create in browser
export const networkMonitor = typeof window !== 'undefined' ? new NetworkMonitor() : null;