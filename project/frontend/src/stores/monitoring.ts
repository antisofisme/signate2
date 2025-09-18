import { create } from 'zustand';

interface MonitoringState {
  systemHealth: {
    cpu: number;
    memory: number;
    storage: number;
  };
  alerts: Array<{
    id: string;
    level: 'info' | 'warning' | 'error';
    message: string;
    timestamp: string;
  }>;
  devices: Array<{
    id: string;
    name: string;
    status: 'online' | 'offline' | 'warning';
  }>;
  updateSystemHealth: (health: Partial<MonitoringState['systemHealth']>) => void;
  addAlert: (alert: Omit<MonitoringState['alerts'][0], 'id'>) => void;
  updateDeviceStatus: (deviceId: string, status: MonitoringState['devices'][0]['status']) => void;
}

export const useMonitoringStore = create<MonitoringState>((set) => ({
  systemHealth: {
    cpu: 0,
    memory: 0,
    storage: 0,
  },
  alerts: [],
  devices: [],

  updateSystemHealth: (health) =>
    set((state) => ({
      systemHealth: { ...state.systemHealth, ...health },
    })),

  addAlert: (alert) =>
    set((state) => ({
      alerts: [
        {
          ...alert,
          id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        },
        ...state.alerts,
      ],
    })),

  updateDeviceStatus: (deviceId, status) =>
    set((state) => ({
      devices: state.devices.map((device) =>
        device.id === deviceId ? { ...device, status } : device
      ),
    })),
}));

export default useMonitoringStore;