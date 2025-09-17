'use client'

import React, { useState, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'
import { useSearchParams } from 'next/navigation'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { AssetLibrary } from '@/components/assets/asset-library'
import { AssetUploadInterface } from '@/components/assets/asset-upload-interface'
import { AssetPreviewModal } from '@/components/assets/asset-preview-modal'
import { BulkOperationsBar } from '@/components/assets/bulk-operations-bar'
import { PlaylistManager } from '@/components/assets/playlist-manager'
import { AssetFilters } from '@/components/assets/asset-filters'
import { AssetStats } from '@/components/assets/asset-stats'
import { useAssets, useAssetActions, useAssetSelection } from '@/stores/assets'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Upload, Grid, List, Filter, BarChart3, Calendar, Share2 } from 'lucide-react'
import { toast } from 'react-hot-toast'

export default function AssetsPage() {
  const [searchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'library')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showUpload, setShowUpload] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [showPlaylistManager, setShowPlaylistManager] = useState(false)
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null)

  const { assets, isLoading, totalAssets, currentAsset } = useAssets()
  const { fetchAssets, uploadFiles } = useAssetActions()
  const { selectedAssets, clearSelection } = useAssetSelection()

  useEffect(() => {
    fetchAssets()
  }, [fetchAssets])

  const handleAssetSelect = (assetId: string) => {
    setSelectedAssetId(assetId)
    setShowPreview(true)
  }

  const handleUpload = async (files: File[]) => {
    try {
      await uploadFiles(files as any)
      setShowUpload(false)
      toast.success('Files uploaded successfully!')
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error('Upload failed. Please try again.')
    }
  }

  const handleBulkAction = async (action: string, assetIds: string[]) => {
    // Bulk action implementation will be handled by BulkOperationsBar
    console.log(`Performing ${action} on assets:`, assetIds)
  }

  return (
    <DashboardLayout>
      <Helmet>
        <title>Asset Management - Anthias Digital Signage</title>
        <meta name="description" content="Manage your digital signage assets, playlists, and content schedules" />
      </Helmet>

      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Asset Management</h1>
            <p className="text-muted-foreground">
              Manage your digital signage content, playlists, and schedules
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setShowUpload(true)}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Upload Assets
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowPlaylistManager(true)}
              className="flex items-center gap-2"
            >
              <Calendar className="h-4 w-4" />
              Manage Playlists
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        <AssetStats />

        {/* Bulk Operations Bar */}
        {selectedAssets.length > 0 && (
          <BulkOperationsBar
            selectedCount={selectedAssets.length}
            onAction={handleBulkAction}
            onClear={clearSelection}
          />
        )}

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="library" className="flex items-center gap-2">
              <Grid className="h-4 w-4" />
              Asset Library
            </TabsTrigger>
            <TabsTrigger value="playlists" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Playlists
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="sharing" className="flex items-center gap-2">
              <Share2 className="h-4 w-4" />
              Sharing
            </TabsTrigger>
          </TabsList>

          <TabsContent value="library" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <CardTitle className="flex items-center gap-2">
                    <Grid className="h-5 w-5" />
                    Asset Library ({totalAssets} assets)
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <AssetFilters />
                    <div className="flex items-center gap-1 border rounded-md">
                      <Button
                        variant={viewMode === 'grid' ? 'default' : 'ghost'}
                        size="sm"
                        onClick={() => setViewMode('grid')}
                        className="h-8 w-8 p-0"
                      >
                        <Grid className="h-4 w-4" />
                      </Button>
                      <Button
                        variant={viewMode === 'list' ? 'default' : 'ghost'}
                        size="sm"
                        onClick={() => setViewMode('list')}
                        className="h-8 w-8 p-0"
                      >
                        <List className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <AssetLibrary
                  viewMode={viewMode}
                  onAssetSelect={handleAssetSelect}
                  isLoading={isLoading}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="playlists" className="space-y-6">
            <PlaylistManager />
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Asset Analytics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-muted-foreground">
                  Analytics dashboard coming soon...
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sharing" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Share2 className="h-5 w-5" />
                  Asset Sharing
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-muted-foreground">
                  Sharing management coming soon...
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Modals */}
      <AssetUploadInterface
        open={showUpload}
        onOpenChange={setShowUpload}
        onUpload={handleUpload}
      />

      <AssetPreviewModal
        open={showPreview}
        onOpenChange={setShowPreview}
        assetId={selectedAssetId}
      />

      <PlaylistManager
        open={showPlaylistManager}
        onOpenChange={setShowPlaylistManager}
      />
    </DashboardLayout>
  )
}