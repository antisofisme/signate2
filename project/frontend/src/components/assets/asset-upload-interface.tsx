'use client'

import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Upload,
  X,
  FileText,
  Image as ImageIcon,
  Video,
  Music,
  File,
  CheckCircle,
  AlertCircle,
  Loader2,
  Plus,
  Trash2,
  Calendar,
  Tag
} from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { DatePicker } from '@/components/ui/date-picker'
import { cn } from '@/lib/utils'

interface FileUploadItem {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  error?: string
  metadata?: {
    name?: string
    description?: string
    tags?: string[]
    startDate?: Date
    endDate?: Date
    isEnabled?: boolean
  }
}

interface AssetUploadInterfaceProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onUpload: (files: File[]) => Promise<void>
  maxFiles?: number
  maxSize?: number
  accept?: Record<string, string[]>
}

const getFileIcon = (type: string) => {
  if (type.startsWith('image/')) return ImageIcon
  if (type.startsWith('video/')) return Video
  if (type.startsWith('audio/')) return Music
  if (type.includes('pdf')) return FileText
  return File
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const FilePreview: React.FC<{
  file: FileUploadItem
  onUpdate: (id: string, metadata: any) => void
  onRemove: (id: string) => void
}> = ({ file, onUpdate, onRemove }) => {
  const Icon = getFileIcon(file.file.type)
  const [tags, setTags] = useState<string>(file.metadata?.tags?.join(', ') || '')

  const handleMetadataChange = (field: string, value: any) => {
    const metadata = { ...file.metadata, [field]: value }
    if (field === 'tags' && typeof value === 'string') {
      metadata.tags = value.split(',').map(tag => tag.trim()).filter(Boolean)
    }
    onUpdate(file.id, metadata)
  }

  const getStatusColor = () => {
    switch (file.status) {
      case 'completed': return 'text-green-600'
      case 'error': return 'text-red-600'
      case 'uploading': return 'text-blue-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusIcon = () => {
    switch (file.status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />
      case 'error': return <AlertCircle className="h-4 w-4" />
      case 'uploading': return <Loader2 className="h-4 w-4 animate-spin" />
      default: return null
    }
  }

  return (
    <Card className="relative">
      <CardContent className="p-4">
        {/* Remove Button */}
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 h-6 w-6 p-0"
          onClick={() => onRemove(file.id)}
        >
          <X className="h-3 w-3" />
        </Button>

        <div className="space-y-4">
          {/* File Info */}
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-lg bg-muted/50 flex items-center justify-center">
              {file.file.type.startsWith('image/') ? (
                <img
                  src={URL.createObjectURL(file.file)}
                  alt={file.file.name}
                  className="w-full h-full object-cover rounded-lg"
                />
              ) : (
                <Icon className="h-6 w-6 text-muted-foreground" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-medium truncate">{file.file.name}</h4>
              <p className="text-sm text-muted-foreground">
                {formatFileSize(file.file.size)} • {file.file.type}
              </p>
              {file.status !== 'pending' && (
                <div className={cn('flex items-center gap-1 text-sm mt-1', getStatusColor())}>
                  {getStatusIcon()}
                  <span>
                    {file.status === 'completed' && 'Upload completed'}
                    {file.status === 'error' && (file.error || 'Upload failed')}
                    {file.status === 'uploading' && `Uploading... ${file.progress}%`}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          {file.status === 'uploading' && (
            <Progress value={file.progress} className="h-1" />
          )}

          {/* Metadata Form */}
          <div className="space-y-3 pt-2 border-t">
            <div>
              <Label htmlFor={`name-${file.id}`} className="text-sm">Asset Name</Label>
              <Input
                id={`name-${file.id}`}
                value={file.metadata?.name || file.file.name}
                onChange={(e) => handleMetadataChange('name', e.target.value)}
                placeholder="Enter asset name"
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor={`description-${file.id}`} className="text-sm">Description</Label>
              <Textarea
                id={`description-${file.id}`}
                value={file.metadata?.description || ''}
                onChange={(e) => handleMetadataChange('description', e.target.value)}
                placeholder="Enter asset description"
                rows={2}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor={`tags-${file.id}`} className="text-sm">Tags</Label>
              <Input
                id={`tags-${file.id}`}
                value={tags}
                onChange={(e) => {
                  setTags(e.target.value)
                  handleMetadataChange('tags', e.target.value)
                }}
                placeholder="Enter tags separated by commas"
                className="mt-1"
              />
              {file.metadata?.tags && file.metadata.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {file.metadata.tags.map((tag, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-sm">Start Date</Label>
                <DatePicker
                  date={file.metadata?.startDate}
                  onSelect={(date) => handleMetadataChange('startDate', date)}
                />
              </div>
              <div>
                <Label className="text-sm">End Date</Label>
                <DatePicker
                  date={file.metadata?.endDate}
                  onSelect={(date) => handleMetadataChange('endDate', date)}
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor={`enabled-${file.id}`} className="text-sm">Enable Asset</Label>
              <Switch
                id={`enabled-${file.id}`}
                checked={file.metadata?.isEnabled !== false}
                onCheckedChange={(checked) => handleMetadataChange('isEnabled', checked)}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export const AssetUploadInterface: React.FC<AssetUploadInterfaceProps> = ({
  open,
  onOpenChange,
  onUpload,
  maxFiles = 10,
  maxSize = 100 * 1024 * 1024, // 100MB
  accept = {
    'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
    'video/*': ['.mp4', '.webm', '.ogg'],
    'audio/*': ['.mp3', '.wav', '.ogg'],
    'application/pdf': ['.pdf'],
  }
}) => {
  const [files, setFiles] = useState<FileUploadItem[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [activeTab, setActiveTab] = useState('upload')

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substring(7),
      file,
      progress: 0,
      status: 'pending' as const,
      metadata: {
        name: file.name,
        description: '',
        tags: [],
        isEnabled: true
      }
    }))

    setFiles(prev => [...prev, ...newFiles])
    setActiveTab('files')
  }, [])

  const { getRootProps, getInputProps, isDragActive, isDragReject, fileRejections } = useDropzone({
    onDrop,
    accept,
    maxFiles: maxFiles - files.length,
    maxSize,
    multiple: true,
  })

  const updateFileMetadata = (id: string, metadata: any) => {
    setFiles(prev => prev.map(file =>
      file.id === id ? { ...file, metadata: { ...file.metadata, ...metadata } } : file
    ))
  }

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id))
  }

  const clearAll = () => {
    setFiles([])
    setActiveTab('upload')
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setIsUploading(true)

    try {
      // Update status to uploading
      setFiles(prev => prev.map(file => ({ ...file, status: 'uploading' as const })))

      // Simulate upload progress for each file
      for (const file of files) {
        for (let progress = 0; progress <= 100; progress += 10) {
          await new Promise(resolve => setTimeout(resolve, 100))
          setFiles(prev => prev.map(f =>
            f.id === file.id ? { ...f, progress } : f
          ))
        }
      }

      // Call the actual upload function
      await onUpload(files.map(f => f.file))

      // Mark all as completed
      setFiles(prev => prev.map(file => ({ ...file, status: 'completed' as const })))

      // Close modal after a short delay
      setTimeout(() => {
        onOpenChange(false)
        clearAll()
      }, 1500)

    } catch (error) {
      console.error('Upload failed:', error)
      setFiles(prev => prev.map(file => ({
        ...file,
        status: 'error' as const,
        error: error instanceof Error ? error.message : 'Upload failed'
      })))
    } finally {
      setIsUploading(false)
    }
  }

  const hasErrors = fileRejections.length > 0
  const canUpload = files.length > 0 && !isUploading && files.every(f => f.status !== 'uploading')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Assets
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="upload">Upload Files</TabsTrigger>
            <TabsTrigger value="files" disabled={files.length === 0}>
              Files ({files.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            <Card
              {...getRootProps()}
              className={cn(
                'cursor-pointer border-2 border-dashed transition-colors hover:bg-accent/50',
                isDragActive && 'border-primary bg-primary/5',
                isDragReject && 'border-destructive bg-destructive/5',
                files.length >= maxFiles && 'cursor-not-allowed opacity-50'
              )}
            >
              <CardContent className="flex flex-col items-center justify-center p-12 text-center">
                <input {...getInputProps()} disabled={files.length >= maxFiles} />
                <Upload className="h-16 w-16 text-muted-foreground mb-4" />
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">
                    {isDragActive ? 'Drop files here' : 'Upload your assets'}
                  </h3>
                  <p className="text-muted-foreground">
                    Drag and drop files here, or click to browse
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Supports images, videos, audio, and documents up to {formatFileSize(maxSize)}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {files.length} of {maxFiles} files selected
                  </p>
                </div>
              </CardContent>
            </Card>

            {hasErrors && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-destructive">Upload Errors</h4>
                {fileRejections.map(({ file, errors }) => (
                  <Card key={file.name} className="border-destructive/50">
                    <CardContent className="p-3">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 text-destructive" />
                        <span className="font-medium">{file.name}</span>
                      </div>
                      <ul className="mt-1 text-sm text-destructive">
                        {errors.map((error) => (
                          <li key={error.code}>• {error.message}</li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {files.length > 0 && (
              <div className="flex justify-center">
                <Button onClick={() => setActiveTab('files')} variant="outline">
                  Review Files ({files.length})
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="files" className="space-y-4 overflow-y-auto max-h-[60vh]">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Review and Configure Assets</h3>
              <div className="flex gap-2">
                <Button variant="outline" onClick={clearAll} size="sm">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
                <Button variant="outline" onClick={() => setActiveTab('upload')} size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add More
                </Button>
              </div>
            </div>

            <div className="grid gap-4">
              {files.map((file) => (
                <FilePreview
                  key={file.id}
                  file={file}
                  onUpdate={updateFileMetadata}
                  onRemove={removeFile}
                />
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {/* Footer Actions */}
        <div className="flex justify-between items-center pt-4 border-t">
          <div className="text-sm text-muted-foreground">
            {files.length} file{files.length !== 1 ? 's' : ''} selected
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!canUpload}
              className="min-w-24"
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload {files.length} File{files.length !== 1 ? 's' : ''}
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}