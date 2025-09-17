/**
 * Analytics Dashboard Main Component
 *
 * Comprehensive analytics dashboard with real-time monitoring,
 * device management, and performance insights.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Grid, Paper, Typography, Box, Card, CardContent,
  CircularProgress, Alert, Snackbar, IconButton,
  Tabs, Tab, Toolbar, Chip, Badge
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Fullscreen as FullscreenIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAnalyticsData } from '../hooks/useAnalyticsData';
import { DeviceStatusOverview } from './components/DeviceStatusOverview';
import { ContentPerformanceChart } from './components/ContentPerformanceChart';
import { SystemHealthMetrics } from './components/SystemHealthMetrics';
import { AlertsList } from './components/AlertsList';
import { RealtimeMetrics } from './components/RealtimeMetrics';
import { UsageAnalytics } from './components/UsageAnalytics';
import { BillingDashboard } from './components/BillingDashboard';
import { DeviceManagement } from './components/DeviceManagement';
import { ReportsSection } from './components/ReportsSection';

interface DashboardData {
  totalDevices: number;
  onlineDevices: number;
  offlineDevices: number;
  activeAlerts: number;
  contentViewsToday: number;
  deviceUptime: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const AnalyticsDashboard: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // WebSocket connection for real-time updates
  const {
    isConnected,
    lastMessage,
    sendMessage,
    connectionError
  } = useWebSocket('/ws/analytics/dashboard/');

  // Analytics data hook
  const {
    data: analyticsData,
    loading: analyticsLoading,
    error: analyticsError,
    refetch: refetchAnalytics
  } = useAnalyticsData();

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const message = JSON.parse(lastMessage.data);

        switch (message.type) {
          case 'dashboard_summary':
            setDashboardData(message.data);
            setLoading(false);
            break;

          case 'dashboard_update':
            // Update specific dashboard widgets
            updateDashboardWidget(message.widget, message.data);
            break;

          case 'new_alert':
            setNotifications(prev => [...prev, {
              id: Date.now(),
              type: 'alert',
              message: `New alert: ${message.alert.title}`,
              severity: message.alert.severity,
              timestamp: new Date()
            }]);
            setSnackbarOpen(true);
            break;

          case 'device_update':
            updateDeviceStatus(message.data);
            break;

          case 'metric_update':
            updateMetrics(message.data);
            break;

          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  const updateDashboardWidget = useCallback((widget: string, data: any) => {
    // Update specific dashboard widgets based on widget type
    if (widget === 'device_status') {
      setDashboardData(prev => prev ? { ...prev, ...data } : null);
    }
  }, []);

  const updateDeviceStatus = useCallback((deviceData: any) => {
    // Update device status in real-time
    setDashboardData(prev => {
      if (!prev) return prev;

      // Recalculate device counts based on updated device data
      // This would be more sophisticated in a real implementation
      return {
        ...prev,
        onlineDevices: deviceData.onlineCount || prev.onlineDevices,
        offlineDevices: deviceData.offlineCount || prev.offlineDevices
      };
    });
  }, []);

  const updateMetrics = useCallback((metricsData: any) => {
    // Handle real-time metrics updates
    console.log('Metrics updated:', metricsData);
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refetchAnalytics();
      // Send refresh request via WebSocket
      sendMessage(JSON.stringify({ type: 'refresh_dashboard' }));
    } catch (error) {
      setError('Failed to refresh dashboard data');
    } finally {
      setRefreshing(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  const renderConnectionStatus = () => {
    if (!isConnected) {
      return (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Real-time connection lost. Some data may not be current.
        </Alert>
      );
    }
    return null;
  };

  const renderDashboardSummary = () => {
    if (!dashboardData) return null;

    const getUptimeColor = (uptime: number) => {
      if (uptime >= 95) return 'success';
      if (uptime >= 85) return 'warning';
      return 'error';
    };

    return (
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="h6">
                Total Devices
              </Typography>
              <Typography variant="h4">
                {dashboardData.totalDevices}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="h6">
                Online
              </Typography>
              <Typography variant="h4" color="success.main">
                {dashboardData.onlineDevices}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="h6">
                Offline
              </Typography>
              <Typography variant="h4" color="error.main">
                {dashboardData.offlineDevices}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="h6">
                Active Alerts
              </Typography>
              <Typography variant="h4" color={dashboardData.activeAlerts > 0 ? "error.main" : "success.main"}>
                {dashboardData.activeAlerts}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="h6">
                Views Today
              </Typography>
              <Typography variant="h4">
                {dashboardData.contentViewsToday.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="h6">
                Uptime
              </Typography>
              <Typography variant="h4" color={`${getUptimeColor(dashboardData.deviceUptime)}.main`}>
                {dashboardData.deviceUptime.toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  if (loading && !dashboardData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading dashboard...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Dashboard Header */}
      <Toolbar sx={{ pl: 0, pr: 0, mb: 2 }}>
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          Analytics Dashboard
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={isConnected ? "Live" : "Disconnected"}
            color={isConnected ? "success" : "error"}
            size="small"
          />

          <Badge badgeContent={notifications.length} color="error">
            <IconButton>
              <NotificationsIcon />
            </IconButton>
          </Badge>

          <IconButton onClick={handleRefresh} disabled={refreshing}>
            <RefreshIcon />
          </IconButton>

          <IconButton>
            <SettingsIcon />
          </IconButton>

          <IconButton>
            <FullscreenIcon />
          </IconButton>
        </Box>
      </Toolbar>

      {/* Connection Status */}
      {renderConnectionStatus()}

      {/* Error Display */}
      {(error || connectionError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || connectionError}
        </Alert>
      )}

      {/* Dashboard Summary Cards */}
      {renderDashboardSummary()}

      {/* Main Dashboard Tabs */}
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Overview" />
          <Tab label="Device Management" />
          <Tab label="Content Analytics" />
          <Tab label="System Health" />
          <Tab label="Alerts" />
          <Tab label="Usage & Billing" />
          <Tab label="Reports" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={currentTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <RealtimeMetrics />
          </Grid>
          <Grid item xs={12} lg={4}>
            <AlertsList />
          </Grid>
          <Grid item xs={12}>
            <DeviceStatusOverview />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        <DeviceManagement />
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <ContentPerformanceChart />
          </Grid>
          <Grid item xs={12} lg={4}>
            <UsageAnalytics />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        <SystemHealthMetrics />
      </TabPanel>

      <TabPanel value={currentTab} index={4}>
        <AlertsList detailed={true} />
      </TabPanel>

      <TabPanel value={currentTab} index={5}>
        <BillingDashboard />
      </TabPanel>

      <TabPanel value={currentTab} index={6}>
        <ReportsSection />
      </TabPanel>

      {/* Notification Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="info">
          {notifications.length > 0 && notifications[notifications.length - 1]?.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};