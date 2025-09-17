'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Search, X, Filter, Command } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn, debounce } from '@/lib/utils'
import type { SearchFilters } from '@/types'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  onFiltersChange?: (filters: SearchFilters) => void
  filters?: SearchFilters
  placeholder?: string
  suggestions?: string[]
  recentSearches?: string[]
  showFilters?: boolean
  className?: string
  loading?: boolean
}

export function SearchBar({
  value,
  onChange,
  onFiltersChange,
  filters = {},
  placeholder = 'Search...',
  suggestions = [],
  recentSearches = [],
  showFilters = true,
  className,
  loading = false,
}: SearchBarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [inputFocused, setInputFocused] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const debouncedOnChange = debounce(onChange, 300)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    debouncedOnChange(newValue)
  }

  const handleClear = () => {
    onChange('')
    inputRef.current?.focus()
  }

  const handleSuggestionClick = (suggestion: string) => {
    onChange(suggestion)
    setIsOpen(false)
    inputRef.current?.blur()
  }

  const activeFiltersCount = Object.values(filters).filter(
    (filter) => filter !== undefined && filter !== '' && (!Array.isArray(filter) || filter.length > 0)
  ).length

  const displaySuggestions = value.length > 0 ? suggestions.filter(s =>
    s.toLowerCase().includes(value.toLowerCase())
  ).slice(0, 5) : recentSearches.slice(0, 5)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
      if (e.key === 'Escape') {
        inputRef.current?.blur()
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div className={cn('relative', className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          ref={inputRef}
          defaultValue={value}
          onChange={handleInputChange}
          onFocus={() => {
            setInputFocused(true)
            setIsOpen(true)
          }}
          onBlur={() => {
            setInputFocused(false)
            setTimeout(() => setIsOpen(false), 200)
          }}
          placeholder={placeholder}
          className={cn(
            'pl-10 pr-20',
            inputFocused && 'ring-2 ring-primary'
          )}
          disabled={loading}
        />

        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-1">
          {value && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              className="h-6 w-6 p-0 hover:bg-muted"
            >
              <X className="h-3 w-3" />
            </Button>
          )}

          {showFilters && (
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    'h-6 w-6 p-0 hover:bg-muted',
                    activeFiltersCount > 0 && 'bg-primary text-primary-foreground hover:bg-primary/90'
                  )}
                >
                  <Filter className="h-3 w-3" />
                  {activeFiltersCount > 0 && (
                    <Badge className="absolute -top-1 -right-1 h-4 w-4 p-0 text-xs">
                      {activeFiltersCount}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80" align="end">
                <div className="space-y-4">
                  <h4 className="font-medium">Filters</h4>
                  {/* Filter content will be implemented by parent component */}
                  <p className="text-sm text-muted-foreground">
                    Filter options will be displayed here
                  </p>
                </div>
              </PopoverContent>
            </Popover>
          )}

          <div className="hidden sm:flex items-center space-x-1 text-xs text-muted-foreground">
            <Command className="h-3 w-3" />
            <span>K</span>
          </div>
        </div>
      </div>

      {/* Search Suggestions */}
      {isOpen && (displaySuggestions.length > 0 || value.length > 0) && (
        <Card className="absolute top-full mt-1 w-full z-50 shadow-lg">
          <CardContent className="p-2">
            {displaySuggestions.length > 0 ? (
              <div className="space-y-1">
                <div className="px-2 py-1 text-xs font-medium text-muted-foreground">
                  {value.length > 0 ? 'Suggestions' : 'Recent searches'}
                </div>
                {displaySuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="flex w-full items-center space-x-2 rounded-md px-2 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    <Search className="h-4 w-4 text-muted-foreground" />
                    <span className="flex-1 text-left">{suggestion}</span>
                  </button>
                ))}
              </div>
            ) : value.length > 0 ? (
              <div className="px-2 py-4 text-center text-sm text-muted-foreground">
                No suggestions found
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  )
}