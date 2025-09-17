'use client'

import React, { useState, useEffect } from 'react'
import {
  Activity,
  Wifi,
  WifiOff,
  Clock,
  Eye,
  Play,
  Pause,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Monitor,
  Smartphone,
  Tablet,
  Signal,
  Battery,
  Cpu,
  HardDrive,
  Upload,
  Download
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'

interface AssetStatus {
  assetId: string
  assetName: string
  status: 'playing' | 'paused' | 'loading' | 'error' | 'completed'
  progress: number
  duration: number
  currentTime: number
  errors: string[]
  deviceInfo: DeviceInfo[]
  lastUpdated: Date
}

interface DeviceInfo {
  deviceId: string
  deviceName: string
  location: string
  status: 'online' | 'offline' | 'error'
  type: 'display' | 'mobile' | 'tablet'
  performance: DevicePerformance
  lastSeen: Date
}

interface DevicePerformance {
  cpuUsage: number
  memoryUsage: number
  storageUsage: number
  batteryLevel?: number
  signalStrength?: number
  networkSpeed: {
    upload: number
    download: number
  }
}

interface SystemMetrics {
  totalAssets: number
  playingAssets: number
  errorAssets: number
  onlineDevices: number
  totalDevices: number
  averageLoad: number
  networkLatency: number
}

// Mock data for demonstration
const MOCK_ASSET_STATUS: AssetStatus[] = [
  {
    assetId: '1',
    assetName: 'Morning Announcements Video',
    status: 'playing',
    progress: 65,
    duration: 180,
    currentTime: 117,
    errors: [],
    deviceInfo: [
      {
        deviceId: 'dev-1',
        deviceName: 'Lobby Display 1',
        location: 'Main Lobby',
        status: 'online',
        type: 'display',
        performance: {
          cpuUsage: 23,
          memoryUsage: 67,
          storageUsage: 45,
          networkSpeed: { upload: 10.5, download: 25.2 }
        },
        lastSeen: new Date()
      }
    ],
    lastUpdated: new Date()
  },
  {
    assetId: '2',
    assetName: 'Weather Widget',
    status: 'error',
    progress: 0,
    duration: 30,
    currentTime: 0,
    errors: ['Network timeout', 'API rate limit exceeded'],
    deviceInfo: [
      {
        deviceId: 'dev-2',
        deviceName: 'Entrance Display',
        location: 'Main Entrance',
        status: 'error',
        type: 'display',
        performance: {
          cpuUsage: 15,
          memoryUsage: 45,
          storageUsage: 67,
          networkSpeed: { upload: 0, download: 0 }
        },
        lastSeen: new Date(Date.now() - 5 * 60 * 1000)
      }
    ],
    lastUpdated: new Date()
  }
]

const MOCK_SYSTEM_METRICS: SystemMetrics = {
  totalAssets: 45,
  playingAssets: 23,
  errorAssets: 3,
  onlineDevices: 8,
  totalDevices: 10,
  averageLoad: 72,
  networkLatency: 45
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'playing': case 'online': return 'text-green-600 bg-green-100'
    case 'error': case 'offline': return 'text-red-600 bg-red-100'
    case 'paused': return 'text-yellow-600 bg-yellow-100'
    case 'loading': return 'text-blue-600 bg-blue-100'
    default: return 'text-gray-600 bg-gray-100'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'playing': return Play
    case 'paused': return Pause
    case 'error': return AlertTriangle
    case 'loading': return RefreshCw
    case 'completed': return CheckCircle
    case 'online': return Wifi
    case 'offline': return WifiOff
    default: return Activity
  }
}

const getDeviceIcon = (type: string) => {
  switch (type) {
    case 'mobile': return Smartphone
    case 'tablet': return Tablet
    default: return Monitor
  }
}

const formatTime = (seconds: number) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const AssetStatusCard: React.FC<{ asset: AssetStatus }> = ({ asset }) => {
  const StatusIcon = getStatusIcon(asset.status)

  return (
    <Card>
      <CardContent className="p-4">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-medium truncate">{asset.assetName}</h4>
              <p className="text-sm text-muted-foreground">
                {formatTime(asset.currentTime)} / {formatTime(asset.duration)}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={getStatusColor(asset.status)}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {asset.status}
              </Badge>
            </div>
          </div>

          {/* Progress */}
          {asset.status === 'playing' && (
            <div>
              <Progress value={asset.progress} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>{asset.progress}%</span>
                <span>{formatDistanceToNow(asset.lastUpdated, { addSuffix: true })}</span>
              </div>
            </div>
          )}

          {/* Errors */}
          {asset.errors.length > 0 && (
            <div className="space-y-1">
              {asset.errors.map((error, index) => (
                <div key={index} className="flex items-center gap-2 text-sm text-red-600">
                  <AlertTriangle className="h-3 w-3" />
                  {error}
                </div>
              ))}
            </div>
          )}

          {/* Devices */}
          <div className="space-y-2">
            {asset.deviceInfo.map((device) => {
              const DeviceIcon = getDeviceIcon(device.type)
              const DeviceStatusIcon = getStatusIcon(device.status)

              return (
                <div key={device.deviceId} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                  <div className="flex items-center gap-2">
                    <DeviceIcon className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{device.deviceName}</p>
                      <p className="text-xs text-muted-foreground">{device.location}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={getStatusColor(device.status)}>
                      <DeviceStatusIcon className="h-3 w-3 mr-1" />
                      {device.status}
                    </Badge>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

const DevicePerformanceCard: React.FC<{ device: DeviceInfo }> = ({ device }) => {
  const DeviceIcon = getDeviceIcon(device.type)

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <DeviceIcon className="h-4 w-4" />
          {device.deviceName}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span>CPU Usage</span>
            <span>{device.performance.cpuUsage}%</span>
          </div>
          <Progress value={device.performance.cpuUsage} className="h-2" />
        </div>

        <div>
          <div className="flex justify-between text-sm mb-1">
            <span>Memory Usage</span>
            <span>{device.performance.memoryUsage}%</span>
          </div>
          <Progress value={device.performance.memoryUsage} className="h-2" />
        </div>

        <div>
          <div className="flex justify-between text-sm mb-1">
            <span>Storage Usage</span>
            <span>{device.performance.storageUsage}%</span>
          </div>
          <Progress value={device.performance.storageUsage} className="h-2" />
        </div>

        {device.performance.batteryLevel && (
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="flex items-center gap-1">
                <Battery className="h-3 w-3" />
                Battery
              </span>
              <span>{device.performance.batteryLevel}%</span>
            </div>
            <Progress value={device.performance.batteryLevel} className="h-2" />
          </div>
        )}

        <Separator />

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1">
              <Upload className="h-3 w-3" />
              Upload
            </span>
            <span>{device.performance.networkSpeed.upload} Mbps</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1">
              <Download className="h-3 w-3" />
              Download
            </span>
            <span>{device.performance.networkSpeed.download} Mbps</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

const SystemMetricsCard: React.FC<{ metrics: SystemMetrics }> = ({ metrics }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          System Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{metrics.playingAssets}</div>
            <p className="text-sm text-muted-foreground">Playing</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{metrics.errorAssets}</div>
            <p className="text-sm text-muted-foreground">Errors</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{metrics.onlineDevices}</div>
            <p className="text-sm text-muted-foreground">Online Devices</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{metrics.averageLoad}%</div>
            <p className="text-sm text-muted-foreground">Avg Load</p>
          </div>
        </div>

        <Separator className="my-4" />

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Network Latency</span>
            <span>{metrics.networkLatency}ms</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Device Connectivity</span>
            <span>{Math.round((metrics.onlineDevices / metrics.totalDevices) * 100)}%</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Asset Success Rate</span>
            <span>{Math.round(((metrics.totalAssets - metrics.errorAssets) / metrics.totalAssets) * 100)}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export const RealTimeMonitor: React.FC = () => {
  const [assetStatuses, setAssetStatuses] = useState<AssetStatus[]>(MOCK_ASSET_STATUS)
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>(MOCK_SYSTEM_METRICS)
  const [isConnected, setIsConnected] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setAssetStatuses(prev => prev.map(asset => ({
        ...asset,
        progress: asset.status === 'playing' ? Math.min(asset.progress + Math.random() * 5, 100) : asset.progress,
        currentTime: asset.status === 'playing' ? Math.min(asset.currentTime + 5, asset.duration) : asset.currentTime,
        lastUpdated: new Date()
      })))

      setSystemMetrics(prev => ({
        ...prev,
        averageLoad: Math.max(10, Math.min(90, prev.averageLoad + (Math.random() - 0.5) * 10)),
        networkLatency: Math.max(10, Math.min(200, prev.networkLatency + (Math.random() - 0.5) * 20))
      }))

      setLastUpdate(new Date())
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const handleRefresh = () => {
    // Simulate refresh
    setLastUpdate(new Date())
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Real-Time Monitor</h2>
          <p className="text-muted-foreground">
            Live status of assets and devices • Last update: {formatDistanceToNow(lastUpdate, { addSuffix: true })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isConnected ? 'default' : 'destructive'} className="flex items-center gap-1">
            {isConnected ? (
              <Wifi className="h-3 w-3" />
            ) : (
              <WifiOff className="h-3 w-3" />
            )}
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Metrics */}
      <SystemMetricsCard metrics={systemMetrics} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Asset Status */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Asset Status</h3>
          <ScrollArea className="h-96">
            <div className="space-y-4">
              {assetStatuses.map((asset) => (
                <AssetStatusCard key={asset.assetId} asset={asset} />
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Device Performance */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Device Performance</h3>
          <ScrollArea className="h-96">
            <div className="space-y-4">
              {assetStatuses.flatMap(asset => asset.deviceInfo).map((device) => (
                <DevicePerformanceCard key={device.deviceId} device={device} />
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}