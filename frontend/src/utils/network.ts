// Network utility functions for connectivity detection and monitoring

export const isOnline = (): boolean => {
  return navigator.onLine;
};

export const addOnlineListener = (callback: () => void): void => {
  window.addEventListener('online', callback);
};

export const addOfflineListener = (callback: () => void): void => {
  window.addEventListener('offline', callback);
};

export const removeOnlineListener = (callback: () => void): void => {
  window.removeEventListener('online', callback);
};

export const removeOfflineListener = (callback: () => void): void => {
  window.removeEventListener('offline', callback);
};

// Network status monitoring hook-like utility
export class NetworkMonitor {
  private listeners: Set<(isOnline: boolean) => void> = new Set();
  private isCurrentlyOnline = navigator.onLine;

  constructor() {
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
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    this.listeners.clear();
  }
}

// Global network monitor instance
export const networkMonitor = new NetworkMonitor();