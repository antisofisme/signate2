// Offline queue management for storing and processing requests when offline
import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { StoredRequest, OfflineQueueItem } from '../types/api';

interface OfflineQueueDB extends DBSchema {
  requests: {
    key: string;
    value: OfflineQueueItem;
    indexes: {
      'by-timestamp': string;
      'by-priority': string;
    };
  };
}

class OfflineQueueManager {
  private db: IDBPDatabase<OfflineQueueDB> | null = null;
  private isInitialized = false;

  async init(): Promise<void> {
    if (this.isInitialized) return;

    try {
      this.db = await openDB<OfflineQueueDB>('offline-queue', 1, {
        upgrade(db) {
          const store = db.createObjectStore('requests', {
            keyPath: 'id',
          });

          store.createIndex('by-timestamp', 'timestamp');
          store.createIndex('by-priority', 'priority');
        },
      });

      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize offline queue database:', error);
    }
  }

  async addToQueue(request: StoredRequest, priority: 'low' | 'medium' | 'high' = 'medium'): Promise<void> {
    if (!this.db) await this.init();
    if (!this.db) throw new Error('Failed to initialize offline queue');

    const queueItem: OfflineQueueItem = {
      ...request,
      priority,
      dependencies: [],
    };

    try {
      await this.db.add('requests', queueItem);
      console.log('Request added to offline queue:', queueItem.id);
    } catch (error) {
      console.error('Failed to add request to offline queue:', error);
    }
  }

  async getQueuedRequests(priority?: 'low' | 'medium' | 'high'): Promise<OfflineQueueItem[]> {
    if (!this.db) await this.init();
    if (!this.db) return [];

    try {
      if (priority) {
        return await this.db.getAllFromIndex('requests', 'by-priority', priority);
      } else {
        return await this.db.getAll('requests');
      }
    } catch (error) {
      console.error('Failed to get queued requests:', error);
      return [];
    }
  }

  async removeFromQueue(requestId: string): Promise<void> {
    if (!this.db) await this.init();
    if (!this.db) return;

    try {
      await this.db.delete('requests', requestId);
      console.log('Request removed from offline queue:', requestId);
    } catch (error) {
      console.error('Failed to remove request from offline queue:', error);
    }
  }

  async updateRequest(requestId: string, updates: Partial<OfflineQueueItem>): Promise<void> {
    if (!this.db) await this.init();
    if (!this.db) return;

    try {
      const existing = await this.db.get('requests', requestId);
      if (existing) {
        const updated = { ...existing, ...updates };
        await this.db.put('requests', updated);
      }
    } catch (error) {
      console.error('Failed to update request in offline queue:', error);
    }
  }

  async processQueue(): Promise<void> {
    if (!this.db) await this.init();
    if (!this.db) return;

    try {
      // Get all requests sorted by priority and timestamp
      const requests = await this.db.getAll('requests');

      // Sort by priority (high -> medium -> low) and then by timestamp
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      const sortedRequests = requests.sort((a, b) => {
        const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
        if (priorityDiff !== 0) return priorityDiff;

        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      });

      for (const request of sortedRequests) {
        try {
          await this.executeRequest(request);
          await this.removeFromQueue(request.id);
        } catch (error) {
          console.error('Failed to execute queued request:', error);

          // Increment retry count
          const newRetryCount = request.retryCount + 1;

          if (newRetryCount >= request.maxRetries) {
            console.log('Max retries reached, removing request from queue:', request.id);
            await this.removeFromQueue(request.id);
          } else {
            await this.updateRequest(request.id, { retryCount: newRetryCount });
          }
        }
      }
    } catch (error) {
      console.error('Failed to process offline queue:', error);
    }
  }

  private async executeRequest(request: OfflineQueueItem): Promise<void> {
    const { method, url, data, headers } = request;

    // Use fetch to execute the request
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    console.log('Successfully executed queued request:', request.id);
  }

  async clearQueue(): Promise<void> {
    if (!this.db) await this.init();
    if (!this.db) return;

    try {
      await this.db.clear('requests');
      console.log('Offline queue cleared');
    } catch (error) {
      console.error('Failed to clear offline queue:', error);
    }
  }

  async getQueueStats(): Promise<{
    total: number;
    byPriority: Record<string, number>;
    oldestRequest?: string;
  }> {
    if (!this.db) await this.init();
    if (!this.db) return { total: 0, byPriority: {} };

    try {
      const requests = await this.db.getAll('requests');

      const byPriority = requests.reduce((acc, req) => {
        acc[req.priority] = (acc[req.priority] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      const oldestRequest = requests.length > 0
        ? requests.sort((a, b) =>
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          )[0]?.timestamp
        : undefined;

      return {
        total: requests.length,
        byPriority,
        oldestRequest,
      };
    } catch (error) {
      console.error('Failed to get queue stats:', error);
      return { total: 0, byPriority: {} };
    }
  }
}

// Global offline queue manager instance
export const offlineQueueManager = new OfflineQueueManager();

// Convenience function to add request to queue
export const addToOfflineQueue = (request: StoredRequest, priority?: 'low' | 'medium' | 'high'): Promise<void> => {
  return offlineQueueManager.addToQueue(request, priority);
};

// Auto-process queue when coming back online
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    console.log('Network connection restored, processing offline queue...');
    offlineQueueManager.processQueue();
  });
}