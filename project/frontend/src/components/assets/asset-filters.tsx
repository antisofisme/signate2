'use client'

import React, { useState } from 'react'
import {
  Filter,
  Search,
  X,
  Calendar,
  Tag,
  User,
  FileType,
  SlidersHorizontal,
  Download
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Popover,
  PopoverContent,
  PopoverTrigger
} from '@/components/ui/popover'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { DatePicker } from '@/components/ui/date-picker'
import { Separator } from '@/components/ui/separator'
import { useAssetFilters } from '@/stores/assets'
import { AssetFilters as AssetFiltersType } from '@/types/api'

const FILE_TYPES = [
  { value: 'image', label: 'Images', mimes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'] },
  { value: 'video', label: 'Videos', mimes: ['video/mp4', 'video/webm', 'video/ogg'] },
  { value: 'audio', label: 'Audio', mimes: ['audio/mp3', 'audio/wav', 'audio/ogg'] },
  { value: 'document', label: 'Documents', mimes: ['application/pdf', 'text/plain'] },
]

const SORT_OPTIONS = [
  { value: '-created_at', label: 'Newest First' },
  { value: 'created_at', label: 'Oldest First' },
  { value: 'name', label: 'Name A-Z' },
  { value: '-name', label: 'Name Z-A' },
  { value: '-play_order', label: 'Most Played' },
  { value: 'play_order', label: 'Least Played' },
]

const QUICK_FILTERS = [
  { key: 'is_enabled', value: true, label: 'Enabled Only' },
  { key: 'is_shared', value: true, label: 'Shared Assets' },
  { key: 'status', value: 'active', label: 'Active Only' },
]

interface AdvancedFiltersProps {
  filters: AssetFiltersType
  onFiltersChange: (filters: Partial<AssetFiltersType>) => void
  onClear: () => void
}

const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFiltersChange,
  onClear
}) => {
  const [dateFrom, setDateFrom] = useState<Date | undefined>(
    filters.created_at__gte ? new Date(filters.created_at__gte) : undefined
  )
  const [dateTo, setDateTo] = useState<Date | undefined>(
    filters.created_at__lte ? new Date(filters.created_at__lte) : undefined
  )
  const [selectedTypes, setSelectedTypes] = useState<string[]>(
    filters.mimetype ? [filters.mimetype] : []
  )
  const [tags, setTags] = useState(filters.tags || '')

  const handleTypeToggle = (type: string) => {
    const newTypes = selectedTypes.includes(type)
      ? selectedTypes.filter(t => t !== type)
      : [...selectedTypes, type]

    setSelectedTypes(newTypes)

    // Convert to mimetype filter
    if (newTypes.length === 0) {
      onFiltersChange({ mimetype: undefined })
    } else if (newTypes.length === 1) {
      const fileType = FILE_TYPES.find(ft => ft.value === newTypes[0])
      if (fileType) {
        onFiltersChange({ mimetype: fileType.mimes[0].split('/')[0] })
      }
    } else {
      // Multiple types selected - clear mimetype filter for now
      onFiltersChange({ mimetype: undefined })
    }
  }

  const handleDateFromChange = (date: Date | undefined) => {
    setDateFrom(date)
    onFiltersChange({
      created_at__gte: date ? date.toISOString().split('T')[0] : undefined
    })
  }

  const handleDateToChange = (date: Date | undefined) => {
    setDateTo(date)
    onFiltersChange({
      created_at__lte: date ? date.toISOString().split('T')[0] : undefined
    })
  }

  const handleTagsChange = (value: string) => {
    setTags(value)
    onFiltersChange({
      tags: value.trim() || undefined
    })
  }

  const clearFilters = () => {
    setDateFrom(undefined)
    setDateTo(undefined)
    setSelectedTypes([])
    setTags('')
    onClear()
  }

  const hasActiveFilters =
    dateFrom || dateTo || selectedTypes.length > 0 || tags ||
    filters.is_enabled !== undefined || filters.is_shared !== undefined

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Advanced Filters</CardTitle>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-4 w-4 mr-2" />
              Clear All
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* File Types */}
        <div>
          <Label className="text-sm font-medium mb-3 block">File Types</Label>
          <div className="grid grid-cols-2 gap-2">
            {FILE_TYPES.map((type) => (
              <div key={type.value} className="flex items-center space-x-2">
                <Checkbox
                  id={`type-${type.value}`}
                  checked={selectedTypes.includes(type.value)}
                  onCheckedChange={() => handleTypeToggle(type.value)}
                />
                <Label htmlFor={`type-${type.value}`} className="text-sm">
                  {type.label}
                </Label>
              </div>
            ))}
          </div>
        </div>

        <Separator />

        {/* Date Range */}
        <div>
          <Label className="text-sm font-medium mb-3 block">Date Range</Label>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label className="text-xs text-muted-foreground">From</Label>
              <DatePicker date={dateFrom} setDate={handleDateFromChange} />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">To</Label>
              <DatePicker date={dateTo} setDate={handleDateToChange} />
            </div>
          </div>
        </div>

        <Separator />

        {/* Tags */}
        <div>
          <Label htmlFor="filter-tags" className="text-sm font-medium">
            Tags
          </Label>
          <Input
            id="filter-tags"
            value={tags}
            onChange={(e) => handleTagsChange(e.target.value)}
            placeholder="Filter by tags..."
            className="mt-2"
          />
        </div>

        <Separator />

        {/* Status Filters */}
        <div>
          <Label className="text-sm font-medium mb-3 block">Status</Label>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="filter-enabled"
                checked={filters.is_enabled === true}
                onCheckedChange={(checked) =>
                  onFiltersChange({ is_enabled: checked ? true : undefined })
                }
              />
              <Label htmlFor="filter-enabled" className="text-sm">
                Enabled only
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="filter-shared"
                checked={filters.is_shared === true}
                onCheckedChange={(checked) =>
                  onFiltersChange({ is_shared: checked ? true : undefined })
                }
              />
              <Label htmlFor="filter-shared" className="text-sm">
                Shared assets
              </Label>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export const AssetFilters: React.FC = () => {
  const { filters, setFilters, clearFilters, setSorting } = useAssetFilters()
  const [searchTerm, setSearchTerm] = useState(filters.search || '')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSearchChange = (value: string) => {
    setSearchTerm(value)
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFilters({ search: searchTerm.trim() || undefined })
  }

  const handleQuickFilter = (key: string, value: any) => {
    setFilters({ [key]: value })
  }

  const handleSortChange = (value: string) => {
    const isDesc = value.startsWith('-')
    const field = isDesc ? value.slice(1) : value
    setSorting(field, isDesc ? 'desc' : 'asc')
  }

  const activeFiltersCount = Object.keys(filters).filter(key =>
    key !== 'page' && key !== 'per_page' && key !== 'ordering' && filters[key as keyof AssetFiltersType]
  ).length

  return (
    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
      {/* Search */}
      <form onSubmit={handleSearchSubmit} className="flex-1 min-w-0">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchTerm}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Search assets..."
            className="pl-10 pr-4"
          />
        </div>
      </form>

      {/* Sort */}
      <Select value={filters.ordering || '-created_at'} onValueChange={handleSortChange}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Sort by" />
        </SelectTrigger>
        <SelectContent>
          {SORT_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Quick Filters */}
      <div className="flex flex-wrap gap-2">
        {QUICK_FILTERS.map((filter) => (
          <Button
            key={filter.key}
            variant={filters[filter.key as keyof AssetFiltersType] === filter.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleQuickFilter(filter.key,
              filters[filter.key as keyof AssetFiltersType] === filter.value ? undefined : filter.value
            )}
          >
            {filter.label}
          </Button>
        ))}
      </div>

      {/* Advanced Filters */}
      <Popover open={showAdvanced} onOpenChange={setShowAdvanced}>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm">
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            Filters
            {activeFiltersCount > 0 && (
              <Badge variant="secondary" className="ml-2 h-5 w-5 p-0 flex items-center justify-center">
                {activeFiltersCount}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <AdvancedFilters
            filters={filters}
            onFiltersChange={setFilters}
            onClear={() => {
              clearFilters()
              setSearchTerm('')
              setShowAdvanced(false)
            }}
          />
        </PopoverContent>
      </Popover>

      {/* Export */}
      <Button variant="outline" size="sm">
        <Download className="h-4 w-4 mr-2" />
        Export
      </Button>
    </div>
  )
}