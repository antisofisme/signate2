/**
 * Real-time Monitoring Dashboard
 * Device management and system monitoring interface
 */

import React, { useState, useEffect } from 'react';
import {
  Monitor,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Wifi,
  Battery,
  HardDrive,
  Cpu,
  RefreshCw
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';

import DashboardLayout from '@/components/layout/DashboardLayout';
import DeviceGrid from '@/components/monitoring/device-grid';
import SystemHealthWidget from '@/components/monitoring/system-health-widget';
import AlertsPanel from '@/components/monitoring/alerts-panel';
import PerformanceCharts from '@/components/monitoring/performance-charts';

import { useMonitoringStore } from '@/stores/monitoring';
import { useNotificationStore } from '@/stores/notifications';

const MonitoringPage: React.FC = () => {
  const {
    devices,
    systemHealth,
    alerts,
    performance,
    loading,
    fetchDevices,
    fetchSystemHealth,
    fetchAlerts,
    fetchPerformanceData,
    subscribeToUpdates
  } = useMonitoringStore();

  const { notifications } = useNotificationStore();

  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    // Initial data fetch
    fetchDevices();
    fetchSystemHealth();
    fetchAlerts();
    fetchPerformanceData();

    // Subscribe to real-time updates
    const unsubscribe = subscribeToUpdates();

    return () => {
      unsubscribe?.();
    };
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      fetchDevices(),
      fetchSystemHealth(),
      fetchAlerts(),
      fetchPerformanceData()
    ]);
    setRefreshing(false);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return <Badge variant="success"><CheckCircle className="h-3 w-3 mr-1" />Online</Badge>;
      case 'offline':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Offline</Badge>;
      case 'warning':
        return <Badge variant="warning"><AlertTriangle className="h-3 w-3 mr-1" />Warning</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const stats = {
    totalDevices: devices.length,
    onlineDevices: devices.filter(d => d.status === 'online').length,
    offlineDevices: devices.filter(d => d.status === 'offline').length,
    warningDevices: devices.filter(d => d.status === 'warning').length,
    activeAlerts: alerts.filter(a => a.status === 'active').length
  };

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Real-time Monitoring</h1>
            <p className="text-muted-foreground">
              Monitor device status, system health, and performance metrics
            </p>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Devices</CardTitle>
              <Monitor className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalDevices}</div>
              <p className="text-xs text-muted-foreground">
                Active displays
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Online</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.onlineDevices}</div>
              <p className="text-xs text-muted-foreground">
                {((stats.onlineDevices / stats.totalDevices) * 100).toFixed(1)}% uptime
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Offline</CardTitle>
              <XCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.offlineDevices}</div>
              <p className="text-xs text-muted-foreground">
                Need attention
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Warnings</CardTitle>
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{stats.warningDevices}</div>
              <p className="text-xs text-muted-foreground">
                Performance issues
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
              <Activity className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.activeAlerts}</div>
              <p className="text-xs text-muted-foreground">
                Require response
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="devices">Devices</TabsTrigger>
            <TabsTrigger value="alerts">Alerts</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
          </TabsList>

          <div className="mt-6">
            <TabsContent value="overview" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* System Health */}
                <Card>
                  <CardHeader>
                    <CardTitle>System Health</CardTitle>
                    <CardDescription>
                      Overall system status and health metrics
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <SystemHealthWidget data={systemHealth} />
                  </CardContent>
                </Card>

                {/* Recent Alerts */}
                <Card>
                  <CardHeader>
                    <CardTitle>Recent Alerts</CardTitle>
                    <CardDescription>
                      Latest system alerts and notifications
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <AlertsPanel alerts={alerts.slice(0, 5)} compact />
                  </CardContent>
                </Card>
              </div>

              {/* Device Status Grid */}
              <Card>
                <CardHeader>
                  <CardTitle>Device Status Overview</CardTitle>
                  <CardDescription>
                    Quick view of all connected devices
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <DeviceGrid devices={devices.slice(0, 12)} compact />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="devices">
              <Card>
                <CardHeader>
                  <CardTitle>Device Management</CardTitle>
                  <CardDescription>
                    Monitor and manage all connected devices
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <DeviceGrid devices={devices} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="alerts">
              <Card>
                <CardHeader>
                  <CardTitle>Alert Management</CardTitle>
                  <CardDescription>
                    View and manage system alerts and notifications
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <AlertsPanel alerts={alerts} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="performance">
              <Card>
                <CardHeader>
                  <CardTitle>Performance Analytics</CardTitle>
                  <CardDescription>
                    System performance metrics and trends
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <PerformanceCharts data={performance} />
                </CardContent>
              </Card>
            </TabsContent>
          </div>
        </Tabs>

        {/* Live System Status Bar */}
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium">System Status: Operational</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Wifi className="h-4 w-4" />
                <span>Network: Good</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Cpu className="h-4 w-4" />
                <span>CPU: {systemHealth?.cpuUsage || 0}%</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <HardDrive className="h-4 w-4" />
                <span>Storage: {systemHealth?.storageUsage || 0}%</span>
              </div>
            </div>
            <div className="text-xs text-muted-foreground">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default MonitoringPage;