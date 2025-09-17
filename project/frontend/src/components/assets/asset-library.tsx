'use client'

import React, { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import {
  MoreHorizontal,
  Download,
  Share2,
  Edit,
  Trash2,
  Eye,
  Copy,
  FileText,
  Image as ImageIcon,
  Video,
  Music,
  File
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { useAssets, useAssetActions, useAssetSelection } from '@/stores/assets'
import { Asset } from '@/types/api'
import { cn } from '@/lib/utils'

interface AssetLibraryProps {
  viewMode: 'grid' | 'list'
  onAssetSelect: (assetId: string) => void
  isLoading?: boolean
}

const getFileIcon = (mimetype: string) => {
  if (mimetype.startsWith('image/')) return ImageIcon
  if (mimetype.startsWith('video/')) return Video
  if (mimetype.startsWith('audio/')) return Music
  if (mimetype.includes('pdf')) return FileText
  return File
}

const getFileTypeColor = (mimetype: string) => {
  if (mimetype.startsWith('image/')) return 'bg-blue-100 text-blue-800'
  if (mimetype.startsWith('video/')) return 'bg-purple-100 text-purple-800'
  if (mimetype.startsWith('audio/')) return 'bg-green-100 text-green-800'
  if (mimetype.includes('pdf')) return 'bg-red-100 text-red-800'
  return 'bg-gray-100 text-gray-800'
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const AssetGridCard: React.FC<{
  asset: Asset
  isSelected: boolean
  onSelect: (assetId: string) => void
  onToggleSelection: (assetId: string) => void
  onAction: (action: string, asset: Asset) => void
}> = ({ asset, isSelected, onSelect, onToggleSelection, onAction }) => {
  const Icon = getFileIcon(asset.mimetype)

  return (
    <Card className={cn(
      "group relative cursor-pointer transition-all hover:shadow-md",
      isSelected && "ring-2 ring-primary"
    )}>
      <CardContent className="p-4">
        {/* Selection Checkbox */}
        <div className="absolute top-2 left-2 z-10">
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onToggleSelection(asset.asset_id)}
            className="bg-white shadow-sm"
          />
        </div>

        {/* Action Menu */}
        <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8 bg-white shadow-sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onSelect(asset.asset_id)}>
                <Eye className="h-4 w-4 mr-2" />
                Preview
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction('edit', asset)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction('duplicate', asset)}>
                <Copy className="h-4 w-4 mr-2" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction('download', asset)}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction('share', asset)}>
                <Share2 className="h-4 w-4 mr-2" />
                Share
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onAction('delete', asset)}
                className="text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Asset Preview */}
        <div
          className="aspect-video rounded-lg bg-muted/50 flex items-center justify-center mb-3 overflow-hidden"
          onClick={() => onSelect(asset.asset_id)}
        >
          {asset.mimetype.startsWith('image/') ? (
            <img
              src={asset.uri}
              alt={asset.name}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <Icon className="h-12 w-12 text-muted-foreground" />
          )}
        </div>

        {/* Asset Info */}
        <div className="space-y-2">
          <h3 className="font-medium truncate" title={asset.name}>
            {asset.name}
          </h3>

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <Badge className={getFileTypeColor(asset.mimetype)}>
              {asset.mimetype.split('/')[0]}
            </Badge>
            <span>{formatFileSize(1024 * 1024)}</span> {/* Placeholder size */}
          </div>

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>By {asset.created_by.username}</span>
            <span>{formatDistanceToNow(new Date(asset.created_at), { addSuffix: true })}</span>
          </div>

          {/* Tags */}
          {asset.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {asset.tags.slice(0, 2).map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {asset.tags.length > 2 && (
                <Badge variant="outline" className="text-xs">
                  +{asset.tags.length - 2}
                </Badge>
              )}
            </div>
          )}

          {/* Status Indicators */}
          <div className="flex items-center gap-2">
            {!asset.is_enabled && (
              <Badge variant="secondary" className="text-xs">Disabled</Badge>
            )}
            {asset.is_processing && (
              <Badge variant="outline" className="text-xs">Processing</Badge>
            )}
            {asset.is_shared && (
              <Badge variant="outline" className="text-xs">Shared</Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

const AssetListRow: React.FC<{
  asset: Asset
  isSelected: boolean
  onSelect: (assetId: string) => void
  onToggleSelection: (assetId: string) => void
  onAction: (action: string, asset: Asset) => void
}> = ({ asset, isSelected, onSelect, onToggleSelection, onAction }) => {
  const Icon = getFileIcon(asset.mimetype)

  return (
    <TableRow className={cn(isSelected && "bg-muted/50")}>
      <TableCell className="w-12">
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onToggleSelection(asset.asset_id)}
        />
      </TableCell>

      <TableCell>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-muted/50 flex items-center justify-center">
            {asset.mimetype.startsWith('image/') ? (
              <img
                src={asset.uri}
                alt={asset.name}
                className="w-full h-full object-cover rounded"
                loading="lazy"
              />
            ) : (
              <Icon className="h-5 w-5 text-muted-foreground" />
            )}
          </div>
          <div>
            <div className="font-medium cursor-pointer hover:text-primary" onClick={() => onSelect(asset.asset_id)}>
              {asset.name}
            </div>
            <div className="text-sm text-muted-foreground">
              {asset.mimetype}
            </div>
          </div>
        </div>
      </TableCell>

      <TableCell>
        <Badge className={getFileTypeColor(asset.mimetype)}>
          {asset.mimetype.split('/')[0]}
        </Badge>
      </TableCell>

      <TableCell className="text-sm text-muted-foreground">
        {formatFileSize(1024 * 1024)} {/* Placeholder size */}
      </TableCell>

      <TableCell className="text-sm text-muted-foreground">
        {asset.created_by.username}
      </TableCell>

      <TableCell className="text-sm text-muted-foreground">
        {formatDistanceToNow(new Date(asset.created_at), { addSuffix: true })}
      </TableCell>

      <TableCell>
        <div className="flex items-center gap-1">
          {!asset.is_enabled && <Badge variant="secondary" className="text-xs">Disabled</Badge>}
          {asset.is_processing && <Badge variant="outline" className="text-xs">Processing</Badge>}
          {asset.is_shared && <Badge variant="outline" className="text-xs">Shared</Badge>}
        </div>
      </TableCell>

      <TableCell>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onSelect(asset.asset_id)}>
              <Eye className="h-4 w-4 mr-2" />
              Preview
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onAction('edit', asset)}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onAction('duplicate', asset)}>
              <Copy className="h-4 w-4 mr-2" />
              Duplicate
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onAction('download', asset)}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onAction('share', asset)}>
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => onAction('delete', asset)}
              className="text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  )
}

const LoadingSkeleton: React.FC<{ viewMode: 'grid' | 'list' }> = ({ viewMode }) => {
  if (viewMode === 'grid') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <Skeleton className="aspect-video rounded-lg mb-3" />
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-3 w-1/2" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12"></TableHead>
          <TableHead>Asset</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Size</TableHead>
          <TableHead>Created By</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="w-12"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: 5 }).map((_, i) => (
          <TableRow key={i}>
            <TableCell><Skeleton className="h-4 w-4" /></TableCell>
            <TableCell>
              <div className="flex items-center gap-3">
                <Skeleton className="w-10 h-10 rounded" />
                <div>
                  <Skeleton className="h-4 w-32 mb-1" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
            </TableCell>
            <TableCell><Skeleton className="h-6 w-16" /></TableCell>
            <TableCell><Skeleton className="h-3 w-16" /></TableCell>
            <TableCell><Skeleton className="h-3 w-20" /></TableCell>
            <TableCell><Skeleton className="h-3 w-24" /></TableCell>
            <TableCell><Skeleton className="h-6 w-16" /></TableCell>
            <TableCell><Skeleton className="h-8 w-8" /></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export const AssetLibrary: React.FC<AssetLibraryProps> = ({
  viewMode,
  onAssetSelect,
  isLoading
}) => {
  const { assets } = useAssets()
  const { deleteAsset, duplicateAsset, shareAsset } = useAssetActions()
  const { selectedAssets, toggleAssetSelection } = useAssetSelection()

  const handleAssetAction = async (action: string, asset: Asset) => {
    try {
      switch (action) {
        case 'delete':
          await deleteAsset(asset.asset_id)
          break
        case 'duplicate':
          await duplicateAsset(asset.asset_id)
          break
        case 'share':
          // Open share modal (to be implemented)
          console.log('Share asset:', asset)
          break
        case 'download':
          // Download asset
          const link = document.createElement('a')
          link.href = asset.uri
          link.download = asset.name
          link.click()
          break
        case 'edit':
          // Open edit modal (to be implemented)
          console.log('Edit asset:', asset)
          break
        default:
          console.log(`Action ${action} not implemented`)
      }
    } catch (error) {
      console.error(`Failed to ${action} asset:`, error)
    }
  }

  if (isLoading) {
    return <LoadingSkeleton viewMode={viewMode} />
  }

  if (assets.length === 0) {
    return (
      <div className="text-center py-12">
        <ImageIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium mb-2">No assets found</h3>
        <p className="text-muted-foreground mb-4">
          Upload your first asset to get started with digital signage content.
        </p>
        <Button>Upload Assets</Button>
      </div>
    )
  }

  if (viewMode === 'grid') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {assets.map((asset) => (
          <AssetGridCard
            key={asset.asset_id}
            asset={asset}
            isSelected={selectedAssets.includes(asset.asset_id)}
            onSelect={onAssetSelect}
            onToggleSelection={toggleAssetSelection}
            onAction={handleAssetAction}
          />
        ))}
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12"></TableHead>
          <TableHead>Asset</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Size</TableHead>
          <TableHead>Created By</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="w-12"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {assets.map((asset) => (
          <AssetListRow
            key={asset.asset_id}
            asset={asset}
            isSelected={selectedAssets.includes(asset.asset_id)}
            onSelect={onAssetSelect}
            onToggleSelection={toggleAssetSelection}
            onAction={handleAssetAction}
          />
        ))}
      </TableBody>
    </Table>
  )
}