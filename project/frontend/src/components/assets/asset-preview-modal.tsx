'use client'

import React, { useState, useEffect } from 'react'
import { formatDistanceToNow } from 'date-fns'
import {
  X,
  Download,
  Share2,
  Edit3,
  Copy,
  Trash2,
  Eye,
  Calendar,
  Tag,
  User,
  Clock,
  FileText,
  Image as ImageIcon,
  Video,
  Music,
  File,
  ExternalLink,
  Maximize2,
  RotateCcw,
  Save,
  Loader2
} from 'lucide-react'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { DatePicker } from '@/components/ui/date-picker'
import { Skeleton } from '@/components/ui/skeleton'
import { useAssets, useAssetActions } from '@/stores/assets'
import { Asset } from '@/types/api'
import { cn } from '@/lib/utils'
import { toast } from 'react-hot-toast'

interface AssetPreviewModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  assetId: string | null
}

const getFileIcon = (mimetype: string) => {
  if (mimetype.startsWith('image/')) return ImageIcon
  if (mimetype.startsWith('video/')) return Video
  if (mimetype.startsWith('audio/')) return Music
  if (mimetype.includes('pdf')) return FileText
  return File
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const AssetPreview: React.FC<{ asset: Asset }> = ({ asset }) => {
  const [isFullscreen, setIsFullscreen] = useState(false)

  const handleFullscreen = () => {
    setIsFullscreen(true)
  }

  if (asset.mimetype.startsWith('image/')) {
    return (
      <div className="relative group">
        <img
          src={asset.uri}
          alt={asset.name}
          className="w-full h-auto max-h-96 object-contain rounded-lg"
        />
        <Button
          variant="secondary"
          size="icon"
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={handleFullscreen}
        >
          <Maximize2 className="h-4 w-4" />
        </Button>

        {isFullscreen && (
          <Dialog open={isFullscreen} onOpenChange={setIsFullscreen}>
            <DialogContent className="max-w-7xl w-full h-full p-2">
              <img
                src={asset.uri}
                alt={asset.name}
                className="w-full h-full object-contain"
              />
            </DialogContent>
          </Dialog>
        )}
      </div>
    )
  }

  if (asset.mimetype.startsWith('video/')) {
    return (
      <video
        controls
        className="w-full h-auto max-h-96 rounded-lg"
        poster={asset.uri} // Assuming thumbnail URL
      >
        <source src={asset.uri} type={asset.mimetype} />
        Your browser does not support the video tag.
      </video>
    )
  }

  if (asset.mimetype.startsWith('audio/')) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-center h-48 bg-muted/50 rounded-lg">
          <Music className="h-16 w-16 text-muted-foreground" />
        </div>
        <audio controls className="w-full">
          <source src={asset.uri} type={asset.mimetype} />
          Your browser does not support the audio tag.
        </audio>
      </div>
    )
  }

  const Icon = getFileIcon(asset.mimetype)

  return (
    <div className="flex flex-col items-center justify-center h-48 bg-muted/50 rounded-lg">
      <Icon className="h-16 w-16 text-muted-foreground mb-4" />
      <p className="text-sm text-muted-foreground text-center">
        {asset.mimetype} file
      </p>
      <Button
        variant="outline"
        size="sm"
        className="mt-2"
        onClick={() => window.open(asset.uri, '_blank')}
      >
        <ExternalLink className="h-4 w-4 mr-2" />
        Open File
      </Button>
    </div>
  )
}

const AssetInfo: React.FC<{ asset: Asset }> = ({ asset }) => {
  return (
    <div className="space-y-6">
      {/* Basic Info */}
      <div className="space-y-4">
        <div>
          <Label className="text-sm font-medium">File Name</Label>
          <p className="text-sm text-muted-foreground mt-1">{asset.name}</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-medium">File Type</Label>
            <p className="text-sm text-muted-foreground mt-1">{asset.mimetype}</p>
          </div>
          <div>
            <Label className="text-sm font-medium">File Size</Label>
            <p className="text-sm text-muted-foreground mt-1">{formatFileSize(1024 * 1024)}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-medium">Created By</Label>
            <div className="flex items-center gap-2 mt-1">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{asset.created_by.username}</span>
            </div>
          </div>
          <div>
            <Label className="text-sm font-medium">Created</Label>
            <div className="flex items-center gap-2 mt-1">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {formatDistanceToNow(new Date(asset.created_at), { addSuffix: true })}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Metadata */}
      {asset.metadata && Object.keys(asset.metadata).length > 0 && (
        <div>
          <Label className="text-sm font-medium">Metadata</Label>
          <div className="mt-2 space-y-2">
            {asset.metadata.resolution && (
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Resolution:</span>
                <span className="text-sm">{asset.metadata.resolution}</span>
              </div>
            )}
            {asset.metadata.fps && (
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Frame Rate:</span>
                <span className="text-sm">{asset.metadata.fps} fps</span>
              </div>
            )}
            {asset.metadata.description && (
              <div>
                <span className="text-sm text-muted-foreground">Description:</span>
                <p className="text-sm mt-1">{asset.metadata.description}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tags */}
      {asset.tags.length > 0 && (
        <div>
          <Label className="text-sm font-medium">Tags</Label>
          <div className="flex flex-wrap gap-2 mt-2">
            {asset.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="flex items-center gap-1">
                <Tag className="h-3 w-3" />
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Schedule */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-sm font-medium">Start Date</Label>
          <p className="text-sm text-muted-foreground mt-1">
            {asset.start_date ? new Date(asset.start_date).toLocaleDateString() : 'Not set'}
          </p>
        </div>
        <div>
          <Label className="text-sm font-medium">End Date</Label>
          <p className="text-sm text-muted-foreground mt-1">
            {asset.end_date ? new Date(asset.end_date).toLocaleDateString() : 'Not set'}
          </p>
        </div>
      </div>

      {/* Status */}
      <div>
        <Label className="text-sm font-medium">Status</Label>
        <div className="flex flex-wrap gap-2 mt-2">
          <Badge variant={asset.is_enabled ? 'default' : 'secondary'}>
            {asset.is_enabled ? 'Enabled' : 'Disabled'}
          </Badge>
          {asset.is_processing && (
            <Badge variant="outline">Processing</Badge>
          )}
          {asset.is_shared && (
            <Badge variant="outline">Shared</Badge>
          )}
          <Badge variant={asset.is_active ? 'default' : 'secondary'}>
            {asset.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </div>

      {/* Usage Stats */}
      {asset.usage_stats && (
        <div>
          <Label className="text-sm font-medium">Usage Statistics</Label>
          <div className="mt-2 space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Play Count:</span>
              <span className="text-sm">{asset.usage_stats.play_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Play Time:</span>
              <span className="text-sm">{Math.round(asset.usage_stats.total_play_time / 60)} minutes</span>
            </div>
            {asset.usage_stats.last_played && (
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Last Played:</span>
                <span className="text-sm">
                  {formatDistanceToNow(new Date(asset.usage_stats.last_played), { addSuffix: true })}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const AssetEdit: React.FC<{
  asset: Asset
  onSave: (updates: any) => Promise<void>
  onCancel: () => void
}> = ({ asset, onSave, onCancel }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: asset.name,
    description: asset.metadata?.description || '',
    tags: asset.tags.join(', '),
    startDate: asset.start_date ? new Date(asset.start_date) : undefined,
    endDate: asset.end_date ? new Date(asset.end_date) : undefined,
    isEnabled: asset.is_enabled,
    duration: asset.duration || 0
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const updates = {
        name: formData.name,
        metadata: {
          ...asset.metadata,
          description: formData.description
        },
        tags: formData.tags.split(',').map(tag => tag.trim()).filter(Boolean),
        start_date: formData.startDate?.toISOString(),
        end_date: formData.endDate?.toISOString(),
        is_enabled: formData.isEnabled,
        duration: formData.duration
      }

      await onSave(updates)
      toast.success('Asset updated successfully!')
    } catch (error) {
      console.error('Failed to update asset:', error)
      toast.error('Failed to update asset')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <Label htmlFor="asset-name">Asset Name</Label>
        <Input
          id="asset-name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Enter asset name"
          className="mt-1"
        />
      </div>

      <div>
        <Label htmlFor="asset-description">Description</Label>
        <Textarea
          id="asset-description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Enter asset description"
          rows={3}
          className="mt-1"
        />
      </div>

      <div>
        <Label htmlFor="asset-tags">Tags</Label>
        <Input
          id="asset-tags"
          value={formData.tags}
          onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
          placeholder="Enter tags separated by commas"
          className="mt-1"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Start Date</Label>
          <DatePicker
            date={formData.startDate}
            onSelect={(date) => setFormData({ ...formData, startDate: date })}
          />
        </div>
        <div>
          <Label>End Date</Label>
          <DatePicker
            date={formData.endDate}
            onSelect={(date) => setFormData({ ...formData, endDate: date })}
          />
        </div>
      </div>

      <div>
        <Label htmlFor="asset-duration">Duration (seconds)</Label>
        <Input
          id="asset-duration"
          type="number"
          value={formData.duration}
          onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) || 0 })}
          placeholder="Enter duration in seconds"
          className="mt-1"
        />
      </div>

      <div className="flex items-center justify-between">
        <Label htmlFor="asset-enabled">Enable Asset</Label>
        <Switch
          id="asset-enabled"
          checked={formData.isEnabled}
          onCheckedChange={(checked) => setFormData({ ...formData, isEnabled: checked })}
        />
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </form>
  )
}

export const AssetPreviewModal: React.FC<AssetPreviewModalProps> = ({
  open,
  onOpenChange,
  assetId
}) => {
  const [activeTab, setActiveTab] = useState('preview')
  const { assets, currentAsset } = useAssets()
  const { updateAsset, deleteAsset, duplicateAsset } = useAssetActions()

  const asset = currentAsset || assets.find(a => a.asset_id === assetId)

  useEffect(() => {
    // Asset will be found from assets array or currentAsset
    // No need to fetch individual assets
  }, [open, assetId, asset])

  const handleAction = async (action: string) => {
    if (!asset) return

    try {
      switch (action) {
        case 'download':
          const link = document.createElement('a')
          link.href = asset.uri
          link.download = asset.name
          link.click()
          break
        case 'duplicate':
          await duplicateAsset(asset.asset_id)
          toast.success('Asset duplicated successfully!')
          break
        case 'delete':
          if (confirm('Are you sure you want to delete this asset?')) {
            await deleteAsset(asset.asset_id)
            onOpenChange(false)
          }
          break
        case 'share':
          // Open share modal (to be implemented)
          toast('Share functionality coming soon!')
          break
      }
    } catch (error) {
      console.error(`Failed to ${action} asset:`, error)
      toast.error(`Failed to ${action} asset`)
    }
  }

  const handleSave = async (updates: any) => {
    if (!asset) return
    await updateAsset(asset.asset_id, updates)
    setActiveTab('info')
  }

  if (!asset && open) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <div className="space-y-4">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-64 w-full" />
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-20" />
              <Skeleton className="h-20" />
            </div>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!asset) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between border-b pb-4">
          <div>
            <h2 className="text-xl font-semibold truncate">{asset.name}</h2>
            <p className="text-sm text-muted-foreground">{asset.mimetype}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => handleAction('download')}
              title="Download"
            >
              <Download className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => handleAction('share')}
              title="Share"
            >
              <Share2 className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => handleAction('duplicate')}
              title="Duplicate"
            >
              <Copy className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => handleAction('delete')}
              title="Delete"
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="info">Information</TabsTrigger>
            <TabsTrigger value="edit">Edit</TabsTrigger>
          </TabsList>

          <TabsContent value="preview" className="space-y-4 overflow-y-auto">
            <AssetPreview asset={asset} />
          </TabsContent>

          <TabsContent value="info" className="space-y-4 overflow-y-auto">
            <AssetInfo asset={asset} />
          </TabsContent>

          <TabsContent value="edit" className="space-y-4 overflow-y-auto">
            <AssetEdit
              asset={asset}
              onSave={handleSave}
              onCancel={() => setActiveTab('info')}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}