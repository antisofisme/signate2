import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Monitor, Wifi, Battery, AlertTriangle, CheckCircle } from 'lucide-react';

interface Device {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'warning';
  type: 'display' | 'media_player' | 'sensor';
  batteryLevel?: number;
  signalStrength: number;
  lastSeen: string;
  location: string;
}

interface DeviceGridProps {
  devices?: Device[];
  onDeviceSelect?: (device: Device) => void;
  onRefresh?: () => void;
}

export function DeviceGrid({ devices = [], onDeviceSelect, onRefresh }: DeviceGridProps) {
  const mockDevices: Device[] = [
    {
      id: '1',
      name: 'Display Screen 1',
      status: 'online',
      type: 'display',
      batteryLevel: 85,
      signalStrength: 95,
      lastSeen: '2 minutes ago',
      location: 'Main Lobby'
    },
    {
      id: '2',
      name: 'Media Player A',
      status: 'warning',
      type: 'media_player',
      signalStrength: 60,
      lastSeen: '15 minutes ago',
      location: 'Conference Room'
    },
    {
      id: '3',
      name: 'Sensor Node B',
      status: 'offline',
      type: 'sensor',
      batteryLevel: 15,
      signalStrength: 0,
      lastSeen: '2 hours ago',
      location: 'Storage Area'
    }
  ];

  const displayDevices = devices.length > 0 ? devices : mockDevices;

  const getStatusColor = (status: Device['status']) => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'offline':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: Device['status']) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'offline':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Monitor className="h-4 w-4 text-gray-600" />;
    }
  };

  const getTypeIcon = (type: Device['type']) => {
    switch (type) {
      case 'display':
        return <Monitor className="h-5 w-5" />;
      case 'media_player':
        return <Monitor className="h-5 w-5" />;
      case 'sensor':
        return <Wifi className="h-5 w-5" />;
      default:
        return <Monitor className="h-5 w-5" />;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Device Monitoring</h2>
        <Button onClick={onRefresh} variant="outline">
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {displayDevices.map((device) => (
          <Card
            key={device.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => onDeviceSelect?.(device)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getTypeIcon(device.type)}
                  <CardTitle className="text-lg">{device.name}</CardTitle>
                </div>
                <div className="flex items-center space-x-1">
                  {getStatusIcon(device.status)}
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(device.status)}`} />
                </div>
              </div>
              <CardDescription>{device.location}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              <div className="flex justify-between items-center">
                <Badge variant={device.status === 'online' ? 'default' : 'destructive'}>
                  {device.status.toUpperCase()}
                </Badge>
                <span className="text-sm text-muted-foreground">{device.lastSeen}</span>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-1">
                    <Wifi className="h-3 w-3" />
                    <span>Signal</span>
                  </div>
                  <span className="font-medium">{device.signalStrength}%</span>
                </div>

                {device.batteryLevel !== undefined && (
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-1">
                      <Battery className="h-3 w-3" />
                      <span>Battery</span>
                    </div>
                    <span className="font-medium">{device.batteryLevel}%</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {displayDevices.length === 0 && (
        <div className="text-center py-8">
          <Monitor className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No devices found</p>
        </div>
      )}
    </div>
  );
}

export default DeviceGrid;