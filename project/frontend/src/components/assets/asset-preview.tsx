'use client'

import React, { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Download,
  Edit,
  Trash2,
  Share2,
  Eye,
  Calendar,
  User,
  FileType,
  HardDrive,
  Tag
} from 'lucide-react'
import { cn, formatBytes, formatDateTime } from '@/lib/utils'
import type { Asset } from '@/types'

interface AssetPreviewProps {
  asset: Asset
  isOpen: boolean
  onClose: () => void
  onEdit?: (asset: Asset) => void
  onDelete?: (asset: Asset) => void
  onDownload?: (asset: Asset) => void
  onShare?: (asset: Asset) => void
  className?: string
}

const AssetPreview = React.memo(function AssetPreview({
  asset,
  isOpen,
  onClose,
  onEdit,
  onDelete,
  onDownload,
  onShare,
  className,
}: AssetPreviewProps) {
  const [isLoading, setIsLoading] = useState(false)

  const renderAssetContent = () => {
    switch (asset.type) {
      case 'image':
        return (
          <div className="relative group">
            <img
              src={asset.url}
              alt={asset.metadata.altText || asset.name}
              className="w-full h-auto max-h-96 object-contain rounded-lg"
              onLoad={() => setIsLoading(false)}
            />
            {asset.metadata.width && asset.metadata.height && (
              <Badge className="absolute top-2 right-2 bg-black/50 text-white">
                {asset.metadata.width} × {asset.metadata.height}
              </Badge>
            )}
          </div>
        )
      case 'video':
        return (
          <div className="relative">
            <video
              src={asset.url}
              controls
              className="w-full h-auto max-h-96 rounded-lg"
              poster={asset.thumbnailUrl}
            />
            {asset.metadata.duration && (
              <Badge className="absolute top-2 right-2 bg-black/50 text-white">
                {Math.floor(asset.metadata.duration / 60)}:
                {(asset.metadata.duration % 60).toString().padStart(2, '0')}
              </Badge>
            )}
          </div>
        )
      case 'audio':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-center h-32 bg-muted rounded-lg">
              <div className="text-center">
                <FileType className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">Audio File</p>
              </div>
            </div>
            <audio src={asset.url} controls className="w-full" />
          </div>
        )
      default:
        return (
          <div className="flex items-center justify-center h-32 bg-muted rounded-lg">
            <div className="text-center">
              <FileType className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground">
                {asset.mimeType || 'Unknown file type'}
              </p>
            </div>
          </div>
        )
    }
  }

  const actionButtons = [
    onDownload && {
      icon: Download,
      label: 'Download',
      onClick: () => onDownload(asset),
      variant: 'outline' as const,
    },
    onShare && {
      icon: Share2,
      label: 'Share',
      onClick: () => onShare(asset),
      variant: 'outline' as const,
    },
    onEdit && {
      icon: Edit,
      label: 'Edit',
      onClick: () => onEdit(asset),
      variant: 'outline' as const,
    },
    onDelete && {
      icon: Trash2,
      label: 'Delete',
      onClick: () => onDelete(asset),
      variant: 'destructive' as const,
    },
  ].filter(Boolean)

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className={cn('max-w-4xl max-h-[90vh] overflow-y-auto', className)}>
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Eye className="h-5 w-5" />
            <span className="truncate">{asset.name}</span>
            <Badge variant={asset.isPublic ? 'default' : 'secondary'}>
              {asset.isPublic ? 'Public' : 'Private'}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Preview Section */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardContent className="p-4">
                {renderAssetContent()}
              </CardContent>
            </Card>

            {/* Actions */}
            {actionButtons.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {actionButtons.map((button, index) => {
                  if (!button) return null
                  const Icon = button.icon
                  return (
                    <Button
                      key={index}
                      variant={button.variant}
                      size="sm"
                      onClick={button.onClick}
                      disabled={isLoading}
                    >
                      <Icon className="h-4 w-4 mr-2" />
                      {button.label}
                    </Button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Metadata Section */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-sm">
                    <FileType className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Type:</span>
                    <span className="font-medium">{asset.type}</span>
                  </div>

                  <div className="flex items-center space-x-2 text-sm">
                    <HardDrive className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Size:</span>
                    <span className="font-medium">{formatBytes(asset.size)}</span>
                  </div>

                  <div className="flex items-center space-x-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Created:</span>
                    <span className="font-medium">{formatDateTime(asset.createdAt)}</span>
                  </div>

                  <div className="flex items-center space-x-2 text-sm">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Uploaded by:</span>
                    <span className="font-medium">{asset.uploadedBy}</span>
                  </div>
                </div>

                {asset.metadata.description && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Description</h4>
                    <p className="text-sm text-muted-foreground">
                      {asset.metadata.description}
                    </p>
                  </div>
                )}

                {asset.tags.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2 flex items-center">
                      <Tag className="h-4 w-4 mr-1" />
                      Tags
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {asset.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Additional metadata based on type */}
                {asset.type === 'image' && asset.metadata.width && asset.metadata.height && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Dimensions</h4>
                    <p className="text-sm text-muted-foreground">
                      {asset.metadata.width} × {asset.metadata.height} pixels
                    </p>
                  </div>
                )}

                {asset.type === 'video' && asset.metadata.duration && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Duration</h4>
                    <p className="text-sm text-muted-foreground">
                      {Math.floor(asset.metadata.duration / 60)}:
                      {(asset.metadata.duration % 60).toString().padStart(2, '0')}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
})

export { AssetPreview }