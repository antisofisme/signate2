'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { motion } from 'framer-motion'

interface StatsCardProps {
  title: string
  value: string | number
  description?: string
  icon?: React.ReactNode
  trend?: {
    value: number
    label: string
    direction: 'up' | 'down' | 'neutral'
  }
  className?: string
  loading?: boolean
}

export function StatsCard({
  title,
  value,
  description,
  icon,
  trend,
  className,
  loading = false,
}: StatsCardProps) {
  const getTrendIcon = () => {
    if (!trend) return null

    switch (trend.direction) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />
      case 'neutral':
        return <Minus className="h-4 w-4 text-gray-500" />
      default:
        return null
    }
  }

  const getTrendColor = () => {
    if (!trend) return 'text-muted-foreground'

    switch (trend.direction) {
      case 'up':
        return 'text-green-600'
      case 'down':
        return 'text-red-600'
      case 'neutral':
        return 'text-gray-600'
      default:
        return 'text-muted-foreground'
    }
  }

  if (loading) {
    return (
      <Card className={cn('', className)}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            <div className="h-4 w-24 bg-muted animate-shimmer rounded" />
          </CardTitle>
          <div className="h-4 w-4 bg-muted animate-shimmer rounded" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="h-8 w-16 bg-muted animate-shimmer rounded" />
            <div className="h-3 w-32 bg-muted animate-shimmer rounded" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className={cn('hover:shadow-md transition-shadow', className)}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          {icon && (
            <div className="text-muted-foreground">
              {icon}
            </div>
          )}
        </CardHeader>
        <CardContent>
          <div className="space-y-1">
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.5, type: 'spring' }}
              className="text-2xl font-bold"
            >
              {typeof value === 'number' ? value.toLocaleString() : value}
            </motion.div>

            <div className="flex items-center space-x-2 text-xs">
              {trend && (
                <div className={cn('flex items-center space-x-1', getTrendColor())}>
                  {getTrendIcon()}
                  <span className="font-medium">
                    {trend.value > 0 ? '+' : ''}{trend.value}%
                  </span>
                </div>
              )}
              {(description || trend?.label) && (
                <span className="text-muted-foreground">
                  {trend?.label || description}
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}