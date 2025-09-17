'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Upload,
  Monitor,
  PlayCircle,
  LogIn,
  Settings,
  Trash2,
  Edit,
  Share2,
  UserPlus,
  Calendar,
} from 'lucide-react'
import { cn, formatDateTime, getInitials } from '@/lib/utils'
import type { Activity } from '@/types'

interface RecentActivityProps {
  activities: Activity[]
  className?: string
  maxItems?: number
  loading?: boolean
}

const getActivityIcon = (type: Activity['type']) => {
  const iconMap = {
    asset_uploaded: Upload,
    screen_connected: Monitor,
    playlist_created: PlayCircle,
    user_logged_in: LogIn,
    settings_updated: Settings,
    asset_deleted: Trash2,
    asset_updated: Edit,
    asset_shared: Share2,
    user_invited: UserPlus,
    schedule_created: Calendar,
  }

  const Icon = iconMap[type] || Upload
  return <Icon className="h-4 w-4" />
}

const getActivityColor = (type: Activity['type']) => {
  const colorMap = {
    asset_uploaded: 'bg-blue-500',
    screen_connected: 'bg-green-500',
    playlist_created: 'bg-purple-500',
    user_logged_in: 'bg-gray-500',
    settings_updated: 'bg-orange-500',
    asset_deleted: 'bg-red-500',
    asset_updated: 'bg-yellow-500',
    asset_shared: 'bg-cyan-500',
    user_invited: 'bg-indigo-500',
    schedule_created: 'bg-pink-500',
  }

  return colorMap[type] || 'bg-blue-500'
}

const getActivityBadgeVariant = (type: Activity['type']) => {
  const variantMap = {
    asset_uploaded: 'default',
    screen_connected: 'default',
    playlist_created: 'secondary',
    user_logged_in: 'outline',
    settings_updated: 'secondary',
    asset_deleted: 'destructive',
    asset_updated: 'outline',
    asset_shared: 'default',
    user_invited: 'default',
    schedule_created: 'secondary',
  } as const

  return variantMap[type] || 'default'
}

export function RecentActivity({
  activities,
  className,
  maxItems = 10,
  loading = false,
}: RecentActivityProps) {
  const displayActivities = activities.slice(0, maxItems)

  if (loading) {
    return (
      <Card className={cn('', className)}>
        <CardHeader>
          <CardTitle>
            <div className="h-5 w-32 bg-muted animate-shimmer rounded" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-start space-x-3">
                <div className="h-8 w-8 bg-muted animate-shimmer rounded-full" />
                <div className="flex-1 space-y-1">
                  <div className="h-4 w-3/4 bg-muted animate-shimmer rounded" />
                  <div className="h-3 w-1/2 bg-muted animate-shimmer rounded" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn('', className)}>
      <CardHeader>
        <CardTitle className="text-base">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[400px]">
          <div className="space-y-0">
            {displayActivities.length === 0 ? (
              <div className="p-6 text-center text-muted-foreground">
                No recent activity
              </div>
            ) : (
              displayActivities.map((activity, index) => (
                <div
                  key={activity.id}
                  className={cn(
                    'flex items-start space-x-3 p-4 border-b border-border last:border-b-0 hover:bg-muted/50 transition-colors',
                    index === 0 && 'border-t-0'
                  )}
                >
                  {/* Activity Icon */}
                  <div
                    className={cn(
                      'flex items-center justify-center w-8 h-8 rounded-full text-white flex-shrink-0',
                      getActivityColor(activity.type)
                    )}
                  >
                    {getActivityIcon(activity.type)}
                  </div>

                  {/* Activity Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground mb-1">
                          {activity.description}
                        </p>
                        <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                          <span className="flex items-center space-x-1">
                            <Avatar className="h-4 w-4">
                              <AvatarImage src={`/avatars/${activity.userId}.jpg`} />
                              <AvatarFallback className="text-xs">
                                {getInitials(activity.userName)}
                              </AvatarFallback>
                            </Avatar>
                            <span>{activity.userName}</span>
                          </span>
                          <span>•</span>
                          <span>{formatDateTime(activity.timestamp)}</span>
                        </div>
                      </div>
                      <Badge
                        variant={getActivityBadgeVariant(activity.type)}
                        className="ml-2 text-xs"
                      >
                        {activity.type.replace(/_/g, ' ')}
                      </Badge>
                    </div>

                    {/* Additional metadata */}
                    {activity.metadata && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        {Object.entries(activity.metadata).map(([key, value]) => (
                          <span key={key} className="mr-3">
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}