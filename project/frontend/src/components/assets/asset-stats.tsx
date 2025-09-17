'use client'

import React from 'react'
import {
  FileText,
  Image as ImageIcon,
  Video,
  Music,
  HardDrive,
  Activity,
  TrendingUp,
  Users,
  Clock,
  Share2
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useAssets } from '@/stores/assets'

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

export const AssetStats: React.FC = () => {
  const { assets, totalAssets } = useAssets()

  // Calculate statistics from assets
  const stats = React.useMemo(() => {
    const typeStats = {
      images: 0,
      videos: 0,
      audio: 0,
      documents: 0
    }

    let totalSize = 0
    let enabledAssets = 0
    let sharedAssets = 0
    let totalViews = 0
    let totalPlayTime = 0

    assets.forEach(asset => {
      // File type classification
      if (asset.mimetype.startsWith('image/')) {
        typeStats.images++
      } else if (asset.mimetype.startsWith('video/')) {
        typeStats.videos++
      } else if (asset.mimetype.startsWith('audio/')) {
        typeStats.audio++
      } else {
        typeStats.documents++
      }

      // Size calculation (placeholder since size isn't in API)
      totalSize += 1024 * 1024 // 1MB per asset as placeholder

      // Status counts
      if (asset.is_enabled) enabledAssets++
      if (asset.is_shared) sharedAssets++

      // Usage stats
      if (asset.usage_stats) {
        totalViews += asset.usage_stats.play_count
        totalPlayTime += asset.usage_stats.total_play_time
      }
    })

    return {
      typeStats,
      totalSize,
      enabledAssets,
      sharedAssets,
      totalViews,
      totalPlayTime: Math.round(totalPlayTime / 60), // Convert to minutes
    }
  }, [assets])

  const storageLimit = 10 * 1024 * 1024 * 1024 // 10GB placeholder
  const storageUsagePercent = (stats.totalSize / storageLimit) * 100

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
      {/* Total Assets */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
          <FileText className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatNumber(totalAssets)}</div>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="text-xs">
              {stats.enabledAssets} enabled
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Images */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Images</CardTitle>
          <ImageIcon className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-600">
            {formatNumber(stats.typeStats.images)}
          </div>
          <p className="text-xs text-muted-foreground">
            {totalAssets > 0 ? Math.round((stats.typeStats.images / totalAssets) * 100) : 0}% of total
          </p>
        </CardContent>
      </Card>

      {/* Videos */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Videos</CardTitle>
          <Video className="h-4 w-4 text-purple-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-purple-600">
            {formatNumber(stats.typeStats.videos)}
          </div>
          <p className="text-xs text-muted-foreground">
            {totalAssets > 0 ? Math.round((stats.typeStats.videos / totalAssets) * 100) : 0}% of total
          </p>
        </CardContent>
      </Card>

      {/* Audio */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Audio</CardTitle>
          <Music className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {formatNumber(stats.typeStats.audio)}
          </div>
          <p className="text-xs text-muted-foreground">
            {totalAssets > 0 ? Math.round((stats.typeStats.audio / totalAssets) * 100) : 0}% of total
          </p>
        </CardContent>
      </Card>

      {/* Storage Usage */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Storage</CardTitle>
          <HardDrive className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatFileSize(stats.totalSize)}</div>
          <div className="mt-2">
            <Progress value={storageUsagePercent} className="h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {storageUsagePercent.toFixed(1)}% of {formatFileSize(storageLimit)}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Total Views */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Views</CardTitle>
          <Activity className="h-4 w-4 text-orange-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-orange-600">
            {formatNumber(stats.totalViews)}
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
            <Clock className="h-3 w-3" />
            {stats.totalPlayTime}m play time
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="md:col-span-2 lg:col-span-4 xl:col-span-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quick Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.enabledAssets}</div>
                <p className="text-sm text-muted-foreground">Active Assets</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{stats.sharedAssets}</div>
                <p className="text-sm text-muted-foreground">Shared Assets</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {Math.round((stats.totalViews / Math.max(totalAssets, 1)) * 10) / 10}
                </div>
                <p className="text-sm text-muted-foreground">Avg Views/Asset</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {Math.round((stats.totalPlayTime / Math.max(totalAssets, 1)) * 10) / 10}m
                </div>
                <p className="text-sm text-muted-foreground">Avg Play Time</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}