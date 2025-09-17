/**
 * Device Status Overview Component
 *
 * Real-time overview of device status, health, and performance metrics.
 * Displays device grid with status indicators and quick actions.
 */

import React, { useState, useEffect } from 'react';
import {
  Card, CardContent, Typography, Grid, Box, Chip,
  Avatar, IconButton, Menu, MenuItem, Dialog,
  DialogTitle, DialogContent, LinearProgress,
  Tooltip, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Badge
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Tv as TvIcon,
  Tablet as TabletIcon,
  MoreVert as MoreVertIcon,
  PowerSettingsNew as PowerIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { format } from 'date-fns';

interface Device {
  id: string;
  name: string;
  deviceId: string;
  deviceType: string;
  status: 'online' | 'offline' | 'maintenance' | 'error';
  location: string;
  lastHeartbeat: string;
  healthScore?: number;
  cpuUsage?: number;
  memoryUsage?: number;
  temperature?: number;
  uptime?: number;
  activeAlerts?: number;
  contentPlaying?: string;
}

interface DeviceStatusOverviewProps {
  viewMode?: 'grid' | 'table';
  maxDevices?: number;
}

export const DeviceStatusOverview: React.FC<DeviceStatusOverviewProps> = ({
  viewMode = 'grid',
  maxDevices
}) => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [deviceDetailOpen, setDeviceDetailOpen] = useState(false);

  // Fetch device data
  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const mockDevices: Device[] = [
        {
          id: '1',
          name: 'Main Lobby Display',
          deviceId: 'DISP-001',
          deviceType: 'display',
          status: 'online',
          location: 'Main Lobby',
          lastHeartbeat: new Date().toISOString(),
          healthScore: 95,
          cpuUsage: 45,
          memoryUsage: 62,
          temperature: 42,
          uptime: 345600, // 4 days in seconds
          activeAlerts: 0,
          contentPlaying: 'Welcome Video'
        },
        {
          id: '2',
          name: 'Conference Room A',
          deviceId: 'DISP-002',
          deviceType: 'tv',
          status: 'online',
          location: 'Conference Room A',
          lastHeartbeat: new Date(Date.now() - 30000).toISOString(),
          healthScore: 88,
          cpuUsage: 78,
          memoryUsage: 55,
          temperature: 38,
          uptime: 172800, // 2 days
          activeAlerts: 1,
          contentPlaying: 'Schedule Board'
        },
        {
          id: '3',
          name: 'Kiosk Terminal 1',
          deviceId: 'KIOSK-001',
          deviceType: 'kiosk',
          status: 'error',
          location: 'Reception',
          lastHeartbeat: new Date(Date.now() - 300000).toISOString(),
          healthScore: 25,
          cpuUsage: 95,
          memoryUsage: 89,
          temperature: 65,
          uptime: 3600, // 1 hour
          activeAlerts: 3,
          contentPlaying: null
        },
        {
          id: '4',
          name: 'Cafeteria Menu',
          deviceId: 'DISP-003',
          deviceType: 'display',
          status: 'offline',
          location: 'Cafeteria',
          lastHeartbeat: new Date(Date.now() - 900000).toISOString(),
          healthScore: 0,
          activeAlerts: 2,
          contentPlaying: null
        }
      ];

      const displayDevices = maxDevices ? mockDevices.slice(0, maxDevices) : mockDevices;
      setDevices(displayDevices);
    } catch (error) {
      console.error('Error fetching devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType) {
      case 'tv':
        return <TvIcon />;
      case 'tablet':
        return <TabletIcon />;
      case 'kiosk':
        return <ComputerIcon />;
      default:
        return <ComputerIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'error';
      case 'maintenance':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string, alertCount: number = 0) => {
    if (alertCount > 0) {
      return <WarningIcon color="warning" />;
    }

    switch (status) {
      case 'online':
        return <CheckIcon color="success" />;
      case 'offline':
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <ScheduleIcon color="warning" />;
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}d ${hours}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const handleDeviceMenuClick = (event: React.MouseEvent<HTMLElement>, device: Device) => {
    setSelectedDevice(device);
    setAnchorEl(event.currentTarget);
  };

  const handleDeviceMenuClose = () => {
    setAnchorEl(null);
    setSelectedDevice(null);
  };

  const handleDeviceAction = (action: string) => {
    if (selectedDevice) {
      console.log(`${action} on device:`, selectedDevice.name);
      // Implement device actions here
    }
    handleDeviceMenuClose();
  };

  const handleDeviceClick = (device: Device) => {
    setSelectedDevice(device);
    setDeviceDetailOpen(true);
  };

  const renderGridView = () => (
    <Grid container spacing={2}>
      {devices.map((device) => (
        <Grid item xs={12} sm={6} md={4} lg={3} key={device.id}>
          <Card
            sx={{
              cursor: 'pointer',
              '&:hover': { elevation: 4 },
              border: device.status === 'error' ? '2px solid' : 'none',
              borderColor: device.status === 'error' ? 'error.main' : 'transparent'
            }}
            onClick={() => handleDeviceClick(device)}
          >
            <CardContent sx={{ pb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar
                  sx={{
                    bgcolor: `${getStatusColor(device.status)}.main`,
                    width: 40,
                    height: 40,
                    mr: 2
                  }}
                >
                  {getDeviceIcon(device.deviceType)}
                </Avatar>

                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" noWrap>
                    {device.name}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" noWrap>
                    {device.deviceId}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {device.activeAlerts > 0 && (
                    <Badge badgeContent={device.activeAlerts} color="error">
                      {getStatusIcon(device.status, device.activeAlerts)}
                    </Badge>
                  )}
                  {device.activeAlerts === 0 && getStatusIcon(device.status)}

                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeviceMenuClick(e, device);
                    }}
                  >
                    <MoreVertIcon />
                  </IconButton>
                </Box>
              </Box>

              <Box sx={{ mb: 1 }}>
                <Chip
                  label={device.status.toUpperCase()}
                  color={getStatusColor(device.status) as any}
                  size="small"
                  sx={{ mr: 1 }}
                />
                {device.healthScore !== undefined && (
                  <Chip
                    label={`Health: ${device.healthScore}%`}
                    color={device.healthScore > 80 ? 'success' : device.healthScore > 60 ? 'warning' : 'error'}
                    size="small"
                  />
                )}
              </Box>

              <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                📍 {device.location}
              </Typography>

              {device.contentPlaying && (
                <Typography variant="body2" color="primary" sx={{ mb: 1 }}>
                  ▶️ {device.contentPlaying}
                </Typography>
              )}

              {device.status !== 'offline' && device.healthScore !== undefined && (
                <Box sx={{ mt: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption">CPU</Typography>
                    <Typography variant="caption">{device.cpuUsage}%</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={device.cpuUsage}
                    color={device.cpuUsage > 80 ? 'error' : device.cpuUsage > 60 ? 'warning' : 'primary'}
                    sx={{ height: 4, borderRadius: 2 }}
                  />
                </Box>
              )}

              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                Last seen: {format(new Date(device.lastHeartbeat), 'HH:mm:ss')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const renderTableView = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Device</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Location</TableCell>
            <TableCell>Health</TableCell>
            <TableCell>CPU</TableCell>
            <TableCell>Memory</TableCell>
            <TableCell>Uptime</TableCell>
            <TableCell>Alerts</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {devices.map((device) => (
            <TableRow key={device.id} hover>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar sx={{ mr: 2, bgcolor: `${getStatusColor(device.status)}.main` }}>
                    {getDeviceIcon(device.deviceType)}
                  </Avatar>
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      {device.name}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {device.deviceId}
                    </Typography>
                  </Box>
                </Box>
              </TableCell>
              <TableCell>
                <Chip
                  label={device.status}
                  color={getStatusColor(device.status) as any}
                  size="small"
                />
              </TableCell>
              <TableCell>{device.location}</TableCell>
              <TableCell>
                {device.healthScore !== undefined ? (
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <LinearProgress
                      variant="determinate"
                      value={device.healthScore}
                      sx={{ width: 60, mr: 1 }}
                    />
                    <Typography variant="body2">{device.healthScore}%</Typography>
                  </Box>
                ) : (
                  'N/A'
                )}
              </TableCell>
              <TableCell>{device.cpuUsage ? `${device.cpuUsage}%` : 'N/A'}</TableCell>
              <TableCell>{device.memoryUsage ? `${device.memoryUsage}%` : 'N/A'}</TableCell>
              <TableCell>{device.uptime ? formatUptime(device.uptime) : 'N/A'}</TableCell>
              <TableCell>
                {device.activeAlerts > 0 ? (
                  <Badge badgeContent={device.activeAlerts} color="error">
                    <WarningIcon color="warning" />
                  </Badge>
                ) : (
                  <CheckIcon color="success" />
                )}
              </TableCell>
              <TableCell>
                <IconButton
                  size="small"
                  onClick={(e) => handleDeviceMenuClick(e, device)}
                >
                  <MoreVertIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
            <LinearProgress sx={{ width: '100%' }} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Device Status Overview ({devices.length} devices)
            </Typography>
            <IconButton onClick={fetchDevices}>
              <RefreshIcon />
            </IconButton>
          </Box>

          {viewMode === 'grid' ? renderGridView() : renderTableView()}
        </CardContent>
      </Card>

      {/* Device Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleDeviceMenuClose}
      >
        <MenuItem onClick={() => handleDeviceAction('restart')}>
          <PowerIcon sx={{ mr: 1 }} />
          Restart Device
        </MenuItem>
        <MenuItem onClick={() => handleDeviceAction('configure')}>
          <SettingsIcon sx={{ mr: 1 }} />
          Configure
        </MenuItem>
        <MenuItem onClick={() => handleDeviceAction('refresh')}>
          <RefreshIcon sx={{ mr: 1 }} />
          Refresh Content
        </MenuItem>
      </Menu>

      {/* Device Detail Dialog */}
      <Dialog
        open={deviceDetailOpen}
        onClose={() => setDeviceDetailOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Device Details: {selectedDevice?.name}
        </DialogTitle>
        <DialogContent>
          {selectedDevice && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Basic Information
                </Typography>
                <Typography variant="body2">
                  <strong>Device ID:</strong> {selectedDevice.deviceId}
                </Typography>
                <Typography variant="body2">
                  <strong>Type:</strong> {selectedDevice.deviceType}
                </Typography>
                <Typography variant="body2">
                  <strong>Location:</strong> {selectedDevice.location}
                </Typography>
                <Typography variant="body2">
                  <strong>Status:</strong> {selectedDevice.status}
                </Typography>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Performance Metrics
                </Typography>
                {selectedDevice.healthScore !== undefined && (
                  <Typography variant="body2">
                    <strong>Health Score:</strong> {selectedDevice.healthScore}%
                  </Typography>
                )}
                {selectedDevice.cpuUsage && (
                  <Typography variant="body2">
                    <strong>CPU Usage:</strong> {selectedDevice.cpuUsage}%
                  </Typography>
                )}
                {selectedDevice.memoryUsage && (
                  <Typography variant="body2">
                    <strong>Memory Usage:</strong> {selectedDevice.memoryUsage}%
                  </Typography>
                )}
                {selectedDevice.temperature && (
                  <Typography variant="body2">
                    <strong>Temperature:</strong> {selectedDevice.temperature}°C
                  </Typography>
                )}
              </Grid>
            </Grid>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};