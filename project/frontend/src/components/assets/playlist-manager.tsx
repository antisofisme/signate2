'use client'

import React, { useState } from 'react'
import {
  Plus,
  Play,
  Pause,
  Edit,
  Trash2,
  Copy,
  Calendar,
  Clock,
  DragHandleDots2,
  Monitor,
  Users,
  Settings,
  Save,
  X,
  ChevronRight,
  ImageIcon,
  Video,
  Music,
  File
} from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Separator } from '@/components/ui/separator'
import { DatePicker } from '@/components/ui/date-picker'
import { ScrollArea } from '@/components/ui/scroll-area'
import { DragDropContext, Draggable, Droppable } from 'react-beautiful-dnd'
import { useAssets } from '@/stores/assets'
import { Asset } from '@/types/api'
import { cn } from '@/lib/utils'
import { toast } from 'react-hot-toast'

interface PlaylistAsset {
  id: string
  assetId: string
  asset: Asset
  duration: number
  order: number
  transition?: 'fade' | 'slide' | 'none'
}

interface Playlist {
  id: string
  name: string
  description?: string
  assets: PlaylistAsset[]
  totalDuration: number
  isActive: boolean
  schedules: PlaylistSchedule[]
  assignedScreens: string[]
  createdAt: string
  updatedAt: string
}

interface PlaylistSchedule {
  id: string
  name: string
  startDate: Date
  endDate: Date
  startTime: string
  endTime: string
  daysOfWeek: number[]
  isActive: boolean
}

interface PlaylistManagerProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

const MOCK_PLAYLISTS: Playlist[] = [
  {
    id: '1',
    name: 'Morning Announcements',
    description: 'Daily morning content for lobby displays',
    assets: [],
    totalDuration: 300,
    isActive: true,
    schedules: [],
    assignedScreens: ['screen-1', 'screen-2'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: '2',
    name: 'Lunch Menu Display',
    description: 'Daily lunch menu rotation',
    assets: [],
    totalDuration: 180,
    isActive: true,
    schedules: [],
    assignedScreens: ['screen-3'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
]

const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' }
]

const getFileIcon = (mimetype: string) => {
  if (mimetype.startsWith('image/')) return ImageIcon
  if (mimetype.startsWith('video/')) return Video
  if (mimetype.startsWith('audio/')) return Music
  return File
}

const formatDuration = (seconds: number) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const AssetSelector: React.FC<{
  selectedAssets: Asset[]
  onAssetSelect: (asset: Asset) => void
  onAssetRemove: (assetId: string) => void
}> = ({ selectedAssets, onAssetSelect, onAssetRemove }) => {
  const { assets } = useAssets()
  const [searchTerm, setSearchTerm] = useState('')

  const availableAssets = assets.filter(
    asset => !selectedAssets.find(selected => selected.asset_id === asset.asset_id) &&
    asset.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-4">
      <div>
        <Label>Search Assets</Label>
        <Input
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search for assets to add..."
          className="mt-1"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Available Assets */}
        <div>
          <Label className="text-sm font-medium">Available Assets</Label>
          <ScrollArea className="h-64 mt-2 border rounded-md p-2">
            <div className="space-y-2">
              {availableAssets.map((asset) => {
                const Icon = getFileIcon(asset.mimetype)
                return (
                  <div
                    key={asset.asset_id}
                    className="flex items-center gap-2 p-2 hover:bg-accent rounded-md cursor-pointer"
                    onClick={() => onAssetSelect(asset)}
                  >
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{asset.name}</p>
                      <p className="text-xs text-muted-foreground">{asset.mimetype}</p>
                    </div>
                    <Plus className="h-4 w-4" />
                  </div>
                )
              })}
            </div>
          </ScrollArea>
        </div>

        {/* Selected Assets */}
        <div>
          <Label className="text-sm font-medium">Selected Assets</Label>
          <ScrollArea className="h-64 mt-2 border rounded-md p-2">
            <div className="space-y-2">
              {selectedAssets.map((asset) => {
                const Icon = getFileIcon(asset.mimetype)
                return (
                  <div
                    key={asset.asset_id}
                    className="flex items-center gap-2 p-2 bg-accent rounded-md"
                  >
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{asset.name}</p>
                      <p className="text-xs text-muted-foreground">{asset.mimetype}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onAssetRemove(asset.asset_id)}
                      className="h-6 w-6"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                )
              })}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}

const PlaylistEditor: React.FC<{
  playlist: Playlist | null
  onSave: (playlist: Partial<Playlist>) => void
  onCancel: () => void
}> = ({ playlist, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: playlist?.name || '',
    description: playlist?.description || '',
    isActive: playlist?.isActive ?? true
  })
  const [selectedAssets, setSelectedAssets] = useState<Asset[]>([])
  const [playlistAssets, setPlaylistAssets] = useState<PlaylistAsset[]>([])

  const handleAssetSelect = (asset: Asset) => {
    setSelectedAssets(prev => [...prev, asset])

    const newPlaylistAsset: PlaylistAsset = {
      id: Math.random().toString(36).substring(7),
      assetId: asset.asset_id,
      asset,
      duration: asset.duration || 10,
      order: playlistAssets.length,
      transition: 'fade'
    }

    setPlaylistAssets(prev => [...prev, newPlaylistAsset])
  }

  const handleAssetRemove = (assetId: string) => {
    setSelectedAssets(prev => prev.filter(asset => asset.asset_id !== assetId))
    setPlaylistAssets(prev => prev.filter(item => item.assetId !== assetId))
  }

  const handleDragEnd = (result: any) => {
    if (!result.destination) return

    const items = Array.from(playlistAssets)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    // Update order
    const updatedItems = items.map((item, index) => ({ ...item, order: index }))
    setPlaylistAssets(updatedItems)
  }

  const updateAssetDuration = (assetId: string, duration: number) => {
    setPlaylistAssets(prev =>
      prev.map(item =>
        item.id === assetId ? { ...item, duration } : item
      )
    )
  }

  const totalDuration = playlistAssets.reduce((sum, item) => sum + item.duration, 0)

  const handleSave = () => {
    const playlistData = {
      ...formData,
      assets: playlistAssets,
      totalDuration
    }
    onSave(playlistData)
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="playlist-name">Playlist Name</Label>
          <Input
            id="playlist-name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Enter playlist name"
            className="mt-1"
          />
        </div>
        <div className="flex items-center justify-between">
          <Label htmlFor="playlist-active">Active</Label>
          <Switch
            id="playlist-active"
            checked={formData.isActive}
            onCheckedChange={(checked) => setFormData({ ...formData, isActive: checked })}
          />
        </div>
      </div>

      <div>
        <Label htmlFor="playlist-description">Description</Label>
        <Textarea
          id="playlist-description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Enter playlist description"
          rows={2}
          className="mt-1"
        />
      </div>

      <AssetSelector
        selectedAssets={selectedAssets}
        onAssetSelect={handleAssetSelect}
        onAssetRemove={handleAssetRemove}
      />

      {playlistAssets.length > 0 && (
        <div>
          <Label className="text-sm font-medium">Playlist Items ({formatDuration(totalDuration)})</Label>
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="playlist-assets">
              {(provided) => (
                <div
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  className="space-y-2 mt-2"
                >
                  {playlistAssets.map((item, index) => {
                    const Icon = getFileIcon(item.asset.mimetype)
                    return (
                      <Draggable key={item.id} draggableId={item.id} index={index}>
                        {(provided) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            className="flex items-center gap-3 p-3 border rounded-md bg-card"
                          >
                            <div {...provided.dragHandleProps}>
                              <DragHandleDots2 className="h-4 w-4 text-muted-foreground" />
                            </div>

                            <Icon className="h-4 w-4 text-muted-foreground" />

                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">{item.asset.name}</p>
                              <p className="text-xs text-muted-foreground">{item.asset.mimetype}</p>
                            </div>

                            <div className="flex items-center gap-2">
                              <Input
                                type="number"
                                value={item.duration}
                                onChange={(e) => updateAssetDuration(item.id, parseInt(e.target.value) || 0)}
                                className="w-20 h-8"
                                min="1"
                              />
                              <span className="text-xs text-muted-foreground">sec</span>
                            </div>

                            <Select
                              value={item.transition}
                              onValueChange={(value: 'fade' | 'slide' | 'none') =>
                                setPlaylistAssets(prev =>
                                  prev.map(i => i.id === item.id ? { ...i, transition: value } : i)
                                )
                              }
                            >
                              <SelectTrigger className="w-24 h-8">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="fade">Fade</SelectItem>
                                <SelectItem value="slide">Slide</SelectItem>
                                <SelectItem value="none">None</SelectItem>
                              </SelectContent>
                            </Select>

                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleAssetRemove(item.assetId)}
                              className="h-8 w-8"
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        )}
                      </Draggable>
                    )
                  })}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </div>
      )}

      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSave} disabled={!formData.name.trim()}>
          <Save className="h-4 w-4 mr-2" />
          Save Playlist
        </Button>
      </div>
    </div>
  )
}

const PlaylistScheduler: React.FC<{
  playlist: Playlist
  onSave: (schedules: PlaylistSchedule[]) => void
}> = ({ playlist, onSave }) => {
  const [schedules, setSchedules] = useState<PlaylistSchedule[]>(playlist.schedules || [])

  const addSchedule = () => {
    const newSchedule: PlaylistSchedule = {
      id: Math.random().toString(36).substring(7),
      name: `Schedule ${schedules.length + 1}`,
      startDate: new Date(),
      endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days from now
      startTime: '09:00',
      endTime: '17:00',
      daysOfWeek: [1, 2, 3, 4, 5], // Monday to Friday
      isActive: true
    }
    setSchedules(prev => [...prev, newSchedule])
  }

  const updateSchedule = (id: string, updates: Partial<PlaylistSchedule>) => {
    setSchedules(prev =>
      prev.map(schedule =>
        schedule.id === id ? { ...schedule, ...updates } : schedule
      )
    )
  }

  const removeSchedule = (id: string) => {
    setSchedules(prev => prev.filter(schedule => schedule.id !== id))
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Label className="text-base font-medium">Playlist Schedules</Label>
        <Button onClick={addSchedule} size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Add Schedule
        </Button>
      </div>

      <div className="space-y-4">
        {schedules.map((schedule) => (
          <Card key={schedule.id}>
            <CardContent className="p-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Input
                    value={schedule.name}
                    onChange={(e) => updateSchedule(schedule.id, { name: e.target.value })}
                    className="font-medium"
                  />
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={schedule.isActive}
                      onCheckedChange={(checked) => updateSchedule(schedule.id, { isActive: checked })}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeSchedule(schedule.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm">Start Date</Label>
                    <DatePicker
                      date={schedule.startDate}
                      setDate={(date) => date && updateSchedule(schedule.id, { startDate: date })}
                    />
                  </div>
                  <div>
                    <Label className="text-sm">End Date</Label>
                    <DatePicker
                      date={schedule.endDate}
                      setDate={(date) => date && updateSchedule(schedule.id, { endDate: date })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm">Start Time</Label>
                    <Input
                      type="time"
                      value={schedule.startTime}
                      onChange={(e) => updateSchedule(schedule.id, { startTime: e.target.value })}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-sm">End Time</Label>
                    <Input
                      type="time"
                      value={schedule.endTime}
                      onChange={(e) => updateSchedule(schedule.id, { endTime: e.target.value })}
                      className="mt-1"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-sm">Days of Week</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {DAYS_OF_WEEK.map((day) => (
                      <Badge
                        key={day.value}
                        variant={schedule.daysOfWeek.includes(day.value) ? 'default' : 'outline'}
                        className="cursor-pointer"
                        onClick={() => {
                          const newDays = schedule.daysOfWeek.includes(day.value)
                            ? schedule.daysOfWeek.filter(d => d !== day.value)
                            : [...schedule.daysOfWeek, day.value]
                          updateSchedule(schedule.id, { daysOfWeek: newDays })
                        }}
                      >
                        {day.label.slice(0, 3)}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-end">
        <Button onClick={() => onSave(schedules)}>
          <Save className="h-4 w-4 mr-2" />
          Save Schedules
        </Button>
      </div>
    </div>
  )
}

export const PlaylistManager: React.FC<PlaylistManagerProps> = ({
  open = false,
  onOpenChange
}) => {
  const [playlists, setPlaylists] = useState<Playlist[]>(MOCK_PLAYLISTS)
  const [selectedPlaylist, setSelectedPlaylist] = useState<Playlist | null>(null)
  const [showEditor, setShowEditor] = useState(false)
  const [showScheduler, setShowScheduler] = useState(false)
  const [activeTab, setActiveTab] = useState('playlists')

  const createPlaylist = () => {
    setSelectedPlaylist(null)
    setShowEditor(true)
  }

  const editPlaylist = (playlist: Playlist) => {
    setSelectedPlaylist(playlist)
    setShowEditor(true)
  }

  const deletePlaylist = (id: string) => {
    if (confirm('Are you sure you want to delete this playlist?')) {
      setPlaylists(prev => prev.filter(p => p.id !== id))
      toast.success('Playlist deleted')
    }
  }

  const savePlaylist = (playlistData: Partial<Playlist>) => {
    if (selectedPlaylist) {
      // Update existing playlist
      setPlaylists(prev =>
        prev.map(p =>
          p.id === selectedPlaylist.id
            ? { ...p, ...playlistData, updatedAt: new Date().toISOString() }
            : p
        )
      )
      toast.success('Playlist updated')
    } else {
      // Create new playlist
      const newPlaylist: Playlist = {
        id: Math.random().toString(36).substring(7),
        ...playlistData,
        schedules: [],
        assignedScreens: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      } as Playlist

      setPlaylists(prev => [...prev, newPlaylist])
      toast.success('Playlist created')
    }

    setShowEditor(false)
    setSelectedPlaylist(null)
  }

  const saveSchedules = (schedules: PlaylistSchedule[]) => {
    if (selectedPlaylist) {
      setPlaylists(prev =>
        prev.map(p =>
          p.id === selectedPlaylist.id
            ? { ...p, schedules, updatedAt: new Date().toISOString() }
            : p
        )
      )
      toast.success('Schedules saved')
      setShowScheduler(false)
      setSelectedPlaylist(null)
    }
  }

  if (open && onOpenChange) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>Playlist Manager</DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-hidden">
            <PlaylistManagerContent
              playlists={playlists}
              onCreatePlaylist={createPlaylist}
              onEditPlaylist={editPlaylist}
              onDeletePlaylist={deletePlaylist}
              onSchedulePlaylist={(playlist) => {
                setSelectedPlaylist(playlist)
                setShowScheduler(true)
              }}
              showEditor={showEditor}
              showScheduler={showScheduler}
              selectedPlaylist={selectedPlaylist}
              onSavePlaylist={savePlaylist}
              onSaveSchedules={saveSchedules}
              onCloseEditor={() => {
                setShowEditor(false)
                setSelectedPlaylist(null)
              }}
              onCloseScheduler={() => {
                setShowScheduler(false)
                setSelectedPlaylist(null)
              }}
            />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Playlist Management</CardTitle>
      </CardHeader>
      <CardContent>
        <PlaylistManagerContent
          playlists={playlists}
          onCreatePlaylist={createPlaylist}
          onEditPlaylist={editPlaylist}
          onDeletePlaylist={deletePlaylist}
          onSchedulePlaylist={(playlist) => {
            setSelectedPlaylist(playlist)
            setShowScheduler(true)
          }}
          showEditor={showEditor}
          showScheduler={showScheduler}
          selectedPlaylist={selectedPlaylist}
          onSavePlaylist={savePlaylist}
          onSaveSchedules={saveSchedules}
          onCloseEditor={() => {
            setShowEditor(false)
            setSelectedPlaylist(null)
          }}
          onCloseScheduler={() => {
            setShowScheduler(false)
            setSelectedPlaylist(null)
          }}
        />
      </CardContent>
    </Card>
  )
}

const PlaylistManagerContent: React.FC<{
  playlists: Playlist[]
  onCreatePlaylist: () => void
  onEditPlaylist: (playlist: Playlist) => void
  onDeletePlaylist: (id: string) => void
  onSchedulePlaylist: (playlist: Playlist) => void
  showEditor: boolean
  showScheduler: boolean
  selectedPlaylist: Playlist | null
  onSavePlaylist: (data: Partial<Playlist>) => void
  onSaveSchedules: (schedules: PlaylistSchedule[]) => void
  onCloseEditor: () => void
  onCloseScheduler: () => void
}> = ({
  playlists,
  onCreatePlaylist,
  onEditPlaylist,
  onDeletePlaylist,
  onSchedulePlaylist,
  showEditor,
  showScheduler,
  selectedPlaylist,
  onSavePlaylist,
  onSaveSchedules,
  onCloseEditor,
  onCloseScheduler
}) => {
  if (showEditor) {
    return (
      <PlaylistEditor
        playlist={selectedPlaylist}
        onSave={onSavePlaylist}
        onCancel={onCloseEditor}
      />
    )
  }

  if (showScheduler && selectedPlaylist) {
    return (
      <PlaylistScheduler
        playlist={selectedPlaylist}
        onSave={onSaveSchedules}
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Playlists ({playlists.length})</h3>
        <Button onClick={onCreatePlaylist}>
          <Plus className="h-4 w-4 mr-2" />
          Create Playlist
        </Button>
      </div>

      <div className="space-y-4">
        {playlists.map((playlist) => (
          <Card key={playlist.id}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium">{playlist.name}</h4>
                    <Badge variant={playlist.isActive ? 'default' : 'secondary'}>
                      {playlist.isActive ? 'Active' : 'Inactive'}
                    </Badge>
                    {playlist.schedules.length > 0 && (
                      <Badge variant="outline">
                        <Calendar className="h-3 w-3 mr-1" />
                        {playlist.schedules.length} schedule{playlist.schedules.length !== 1 ? 's' : ''}
                      </Badge>
                    )}
                  </div>

                  {playlist.description && (
                    <p className="text-sm text-muted-foreground mb-2">{playlist.description}</p>
                  )}

                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDuration(playlist.totalDuration)}
                    </span>
                    <span className="flex items-center gap-1">
                      <File className="h-3 w-3" />
                      {playlist.assets.length} assets
                    </span>
                    <span className="flex items-center gap-1">
                      <Monitor className="h-3 w-3" />
                      {playlist.assignedScreens.length} screens
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onSchedulePlaylist(playlist)}
                  >
                    <Calendar className="h-4 w-4 mr-2" />
                    Schedule
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onEditPlaylist(playlist)}
                  >
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onDeletePlaylist(playlist.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {playlists.length === 0 && (
        <div className="text-center py-8">
          <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No playlists yet</h3>
          <p className="text-muted-foreground mb-4">
            Create your first playlist to organize and schedule your digital signage content.
          </p>
          <Button onClick={onCreatePlaylist}>
            <Plus className="h-4 w-4 mr-2" />
            Create Playlist
          </Button>
        </div>
      )}
    </div>
  )
}