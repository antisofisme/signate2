'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { DatePicker } from '@/components/ui/date-picker'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { X, Filter, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SearchFilters } from '@/types'

interface AdvancedFiltersProps {
  filters: SearchFilters
  onChange: (filters: SearchFilters) => void
  onReset: () => void
  availableTypes?: string[]
  availableTags?: string[]
  availableUsers?: { id: string; name: string }[]
  className?: string
}

export function AdvancedFilters({
  filters,
  onChange,
  onReset,
  availableTypes = ['image', 'video', 'audio', 'document'],
  availableTags = [],
  availableUsers = [],
  className,
}: AdvancedFiltersProps) {
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters)

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    const newFilters = { ...localFilters, [key]: value }
    setLocalFilters(newFilters)
    onChange(newFilters)
  }

  const removeTag = (tagToRemove: string) => {
    const newTags = localFilters.tags?.filter(tag => tag !== tagToRemove) || []
    updateFilter('tags', newTags.length > 0 ? newTags : undefined)
  }

  const addTag = (tag: string) => {
    if (!tag || localFilters.tags?.includes(tag)) return
    const newTags = [...(localFilters.tags || []), tag]
    updateFilter('tags', newTags)
  }

  const handleReset = () => {
    setLocalFilters({})
    onReset()
  }

  const activeFiltersCount = Object.values(localFilters).filter(
    value => value !== undefined && value !== '' && (!Array.isArray(value) || value.length > 0)
  ).length

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg flex items-center space-x-2">
          <Filter className="h-5 w-5" />
          <span>Advanced Filters</span>
          {activeFiltersCount > 0 && (
            <Badge variant="secondary">{activeFiltersCount}</Badge>
          )}
        </CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={handleReset}
          disabled={activeFiltersCount === 0}
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          Reset
        </Button>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* File Type Filter */}
        <div className="space-y-2">
          <Label htmlFor="type-filter">File Type</Label>
          <Select
            value={localFilters.type || ''}
            onValueChange={(value) => updateFilter('type', value || undefined)}
          >
            <SelectTrigger>
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All types</SelectItem>
              {availableTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Separator />

        {/* Date Range Filter */}
        <div className="space-y-4">
          <Label>Date Range</Label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="date-from" className="text-sm text-muted-foreground">
                From
              </Label>
              <DatePicker
                date={localFilters.dateFrom ? new Date(localFilters.dateFrom) : undefined}
                onSelect={(date) => updateFilter('dateFrom', date?.toISOString() || undefined)}
                placeholder="Select start date"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="date-to" className="text-sm text-muted-foreground">
                To
              </Label>
              <DatePicker
                date={localFilters.dateTo ? new Date(localFilters.dateTo) : undefined}
                onSelect={(date) => updateFilter('dateTo', date?.toISOString() || undefined)}
                placeholder="Select end date"
              />
            </div>
          </div>
        </div>

        <Separator />

        {/* File Size Filter */}
        <div className="space-y-4">
          <Label>File Size (MB)</Label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="size-min" className="text-sm text-muted-foreground">
                Minimum
              </Label>
              <Input
                id="size-min"
                type="number"
                placeholder="0"
                value={localFilters.size?.min || ''}
                onChange={(e) => {
                  const value = e.target.value ? parseInt(e.target.value) * 1024 * 1024 : undefined
                  updateFilter('size', { ...localFilters.size, min: value })
                }}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="size-max" className="text-sm text-muted-foreground">
                Maximum
              </Label>
              <Input
                id="size-max"
                type="number"
                placeholder="100"
                value={localFilters.size?.max ? localFilters.size.max / (1024 * 1024) : ''}
                onChange={(e) => {
                  const value = e.target.value ? parseInt(e.target.value) * 1024 * 1024 : undefined
                  updateFilter('size', { ...localFilters.size, max: value })
                }}
              />
            </div>
          </div>
        </div>

        <Separator />

        {/* Tags Filter */}
        <div className="space-y-4">
          <Label>Tags</Label>

          {/* Selected Tags */}
          {localFilters.tags && localFilters.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {localFilters.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="flex items-center space-x-1">
                  <span>{tag}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeTag(tag)}
                    className="h-4 w-4 p-0 hover:bg-transparent"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              ))}
            </div>
          )}

          {/* Available Tags */}
          {availableTags.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm text-muted-foreground">Available Tags</Label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                {availableTags
                  .filter(tag => !localFilters.tags?.includes(tag))
                  .map((tag) => (
                    <Badge
                      key={tag}
                      variant="outline"
                      className="cursor-pointer hover:bg-accent"
                      onClick={() => addTag(tag)}
                    >
                      {tag}
                    </Badge>
                  ))}
              </div>
            </div>
          )}
        </div>

        <Separator />

        {/* User Filter */}
        {availableUsers.length > 0 && (
          <div className="space-y-2">
            <Label htmlFor="user-filter">Uploaded By</Label>
            <Select
              value={localFilters.user || ''}
              onValueChange={(value) => updateFilter('user', value || undefined)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All users" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All users</SelectItem>
                {availableUsers.map((user) => (
                  <SelectItem key={user.id} value={user.id}>
                    {user.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </CardContent>
    </Card>
  )
}