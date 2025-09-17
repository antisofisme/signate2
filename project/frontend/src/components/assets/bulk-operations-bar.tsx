'use client'

import React, { useState } from 'react'
import {
  Trash2,
  Download,
  Share2,
  Copy,
  Move,
  Archive,
  Eye,
  EyeOff,
  Tag,
  Calendar,
  CheckCircle,
  X,
  ChevronDown,
  Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useAssetActions, useAssetSelection } from '@/stores/assets'
import { cn } from '@/lib/utils'
import { toast } from 'react-hot-toast'

interface BulkOperationsBarProps {
  selectedCount: number
  onAction: (action: string, assetIds: string[]) => Promise<void>
  onClear: () => void
  className?: string
}

interface BulkAction {
  key: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  variant?: 'default' | 'destructive' | 'outline'
  requiresConfirmation?: boolean
  requiresInput?: boolean
  description?: string
}

const BULK_ACTIONS: BulkAction[] = [
  {
    key: 'enable',
    label: 'Enable',
    icon: Eye,
    description: 'Enable selected assets'
  },
  {
    key: 'disable',
    label: 'Disable',
    icon: EyeOff,
    description: 'Disable selected assets'
  },
  {
    key: 'duplicate',
    label: 'Duplicate',
    icon: Copy,
    description: 'Create copies of selected assets'
  },
  {
    key: 'move',
    label: 'Move to Folder',
    icon: Move,
    requiresInput: true,
    description: 'Move assets to a different folder'
  },
  {
    key: 'tag',
    label: 'Add Tags',
    icon: Tag,
    requiresInput: true,
    description: 'Add tags to selected assets'
  },
  {
    key: 'schedule',
    label: 'Schedule',
    icon: Calendar,
    requiresInput: true,
    description: 'Set schedule for selected assets'
  },
  {
    key: 'archive',
    label: 'Archive',
    icon: Archive,
    requiresConfirmation: true,
    description: 'Archive selected assets'
  },
  {
    key: 'delete',
    label: 'Delete',
    icon: Trash2,
    variant: 'destructive',
    requiresConfirmation: true,
    description: 'Permanently delete selected assets'
  }
]

interface ActionDialogProps {
  action: BulkAction | null
  selectedCount: number
  onConfirm: (data?: any) => void
  onCancel: () => void
}

const ActionDialog: React.FC<ActionDialogProps> = ({
  action,
  selectedCount,
  onConfirm,
  onCancel
}) => {
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  if (!action) return null

  const handleConfirm = async () => {
    setIsLoading(true)
    try {
      const data = action.requiresInput ? { input: inputValue } : undefined
      await onConfirm(data)
      setInputValue('')
    } finally {
      setIsLoading(false)
    }
  }

  const getTitle = () => {
    switch (action.key) {
      case 'delete':
        return `Delete ${selectedCount} asset${selectedCount > 1 ? 's' : ''}?`
      case 'archive':
        return `Archive ${selectedCount} asset${selectedCount > 1 ? 's' : ''}?`
      case 'move':
        return `Move ${selectedCount} asset${selectedCount > 1 ? 's' : ''}`
      case 'tag':
        return `Add tags to ${selectedCount} asset${selectedCount > 1 ? 's' : ''}`
      case 'schedule':
        return `Schedule ${selectedCount} asset${selectedCount > 1 ? 's' : ''}`
      default:
        return `${action.label} ${selectedCount} asset${selectedCount > 1 ? 's' : ''}?`
    }
  }

  const getDescription = () => {
    if (action.key === 'delete') {
      return 'This action cannot be undone. The selected assets will be permanently removed from your library.'
    }
    if (action.key === 'archive') {
      return 'Archived assets will be hidden from the main library but can be restored later.'
    }
    return action.description
  }

  const getInputPlaceholder = () => {
    switch (action.key) {
      case 'move':
        return 'Enter folder name or path'
      case 'tag':
        return 'Enter tags separated by commas'
      case 'schedule':
        return 'Enter schedule details'
      default:
        return 'Enter value'
    }
  }

  const getInputLabel = () => {
    switch (action.key) {
      case 'move':
        return 'Destination Folder'
      case 'tag':
        return 'Tags'
      case 'schedule':
        return 'Schedule'
      default:
        return 'Input'
    }
  }

  const isMultiline = action.key === 'schedule'

  return (
    <Dialog open={true} onOpenChange={onCancel}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <action.icon className="h-5 w-5" />
            {getTitle()}
          </DialogTitle>
          <DialogDescription>
            {getDescription()}
          </DialogDescription>
        </DialogHeader>

        {action.requiresInput && (
          <div className="space-y-2">
            <Label htmlFor="action-input">{getInputLabel()}</Label>
            {isMultiline ? (
              <Textarea
                id="action-input"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={getInputPlaceholder()}
                rows={3}
              />
            ) : (
              <Input
                id="action-input"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={getInputPlaceholder()}
              />
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onCancel} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            variant={action.variant || 'default'}
            disabled={isLoading || (action.requiresInput && !inputValue.trim())}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              action.label
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export const BulkOperationsBar: React.FC<BulkOperationsBarProps> = ({
  selectedCount,
  onAction,
  onClear,
  className
}) => {
  const [activeAction, setActiveAction] = useState<BulkAction | null>(null)
  const { selectedAssets } = useAssetSelection()
  const { deleteAssets, updateAsset } = useAssetActions()

  const handleAction = async (action: BulkAction) => {
    if (action.requiresConfirmation || action.requiresInput) {
      setActiveAction(action)
      return
    }

    try {
      await executeAction(action.key)
    } catch (error) {
      console.error(`Failed to ${action.key} assets:`, error)
      toast.error(`Failed to ${action.label.toLowerCase()} assets`)
    }
  }

  const executeAction = async (actionKey: string, data?: any) => {
    const assetIds = selectedAssets

    try {
      switch (actionKey) {
        case 'delete':
          await deleteAssets(assetIds)
          break

        case 'enable':
          await Promise.all(
            assetIds.map(id => updateAsset(id, { is_enabled: true }))
          )
          toast.success(`${assetIds.length} assets enabled`)
          break

        case 'disable':
          await Promise.all(
            assetIds.map(id => updateAsset(id, { is_enabled: false }))
          )
          toast.success(`${assetIds.length} assets disabled`)
          break

        case 'duplicate':
          // This would need to be implemented in the store
          toast.info('Bulk duplicate functionality coming soon')
          break

        case 'move':
          // This would need folder/category implementation
          toast.info('Move functionality coming soon')
          break

        case 'tag':
          if (data?.input) {
            const tags = data.input.split(',').map((tag: string) => tag.trim()).filter(Boolean)
            await Promise.all(
              assetIds.map(id => updateAsset(id, { tags }))
            )
            toast.success(`Tags added to ${assetIds.length} assets`)
          }
          break

        case 'schedule':
          // This would need scheduling implementation
          toast.info('Scheduling functionality coming soon')
          break

        case 'archive':
          // This would need archive functionality
          toast.info('Archive functionality coming soon')
          break

        default:
          await onAction(actionKey, assetIds)
      }

      onClear()
    } catch (error) {
      throw error
    }
  }

  const handleActionConfirm = async (data?: any) => {
    if (!activeAction) return

    try {
      await executeAction(activeAction.key, data)
      setActiveAction(null)
    } catch (error) {
      console.error(`Failed to ${activeAction.key} assets:`, error)
      toast.error(`Failed to ${activeAction.label.toLowerCase()} assets`)
    }
  }

  const primaryActions = BULK_ACTIONS.slice(0, 3)
  const secondaryActions = BULK_ACTIONS.slice(3)

  if (selectedCount === 0) return null

  return (
    <>
      <Card className={cn('border-primary/20 bg-primary/5', className)}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Checkbox checked={true} onChange={onClear} />
                <Badge variant="secondary" className="bg-primary/10 text-primary">
                  {selectedCount} selected
                </Badge>
              </div>

              <div className="flex items-center gap-2">
                {primaryActions.map((action) => (
                  <Button
                    key={action.key}
                    variant={action.variant || 'outline'}
                    size="sm"
                    onClick={() => handleAction(action)}
                    className="flex items-center gap-2"
                  >
                    <action.icon className="h-4 w-4" />
                    {action.label}
                  </Button>
                ))}

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      More
                      <ChevronDown className="h-4 w-4 ml-1" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    {secondaryActions.map((action, index) => (
                      <React.Fragment key={action.key}>
                        {index === secondaryActions.length - 2 && <DropdownMenuSeparator />}
                        <DropdownMenuItem
                          onClick={() => handleAction(action)}
                          className={cn(
                            action.variant === 'destructive' && 'text-destructive focus:text-destructive'
                          )}
                        >
                          <action.icon className="h-4 w-4 mr-2" />
                          {action.label}
                        </DropdownMenuItem>
                      </React.Fragment>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={onClear}>
                <X className="h-4 w-4 mr-2" />
                Clear Selection
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {activeAction && (
        <ActionDialog
          action={activeAction}
          selectedCount={selectedCount}
          onConfirm={handleActionConfirm}
          onCancel={() => setActiveAction(null)}
        />
      )}
    </>
  )
}