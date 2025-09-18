'use client'

import React, { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Copy,
  Mail,
  Users,
  Eye,
  Calendar,
  Globe,
  Lock,
  ExternalLink,
  Check,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import toast from 'react-hot-toast'

interface ShareModalProps {
  isOpen: boolean
  onClose: () => void
  itemTitle: string
  itemType: 'asset' | 'playlist' | 'screen'
  onShare: (shareData: ShareData) => Promise<void>
}

interface ShareData {
  method: 'link' | 'email' | 'invite'
  permissions: 'view' | 'edit' | 'admin'
  expiry?: string
  password?: string
  message?: string
  recipients?: string[]
  isPublic: boolean
}

export function ShareModal({
  isOpen,
  onClose,
  itemTitle,
  itemType,
  onShare,
}: ShareModalProps) {
  const [shareMethod, setShareMethod] = useState<'link' | 'email' | 'invite'>('link')
  const [permissions, setPermissions] = useState<'view' | 'edit' | 'admin'>('view')
  const [isPublic, setIsPublic] = useState(false)
  const [expiry, setExpiry] = useState<string>('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [recipients, setRecipients] = useState<string[]>([])
  const [newRecipient, setNewRecipient] = useState('')
  const [shareLink, setShareLink] = useState('')
  const [loading, setLoading] = useState(false)
  const [linkCopied, setLinkCopied] = useState(false)

  const handleShare = async () => {
    setLoading(true)
    try {
      const shareData: ShareData = {
        method: shareMethod,
        permissions,
        expiry: expiry || undefined,
        password: password || undefined,
        message: message || undefined,
        recipients: recipients.length > 0 ? recipients : undefined,
        isPublic,
      }

      await onShare(shareData)

      // Simulate generating share link
      const mockLink = `https://app.anthias.com/shared/${itemType}/${Math.random().toString(36).substring(7)}`
      setShareLink(mockLink)

      toast.success(`${itemType} shared successfully!`)
    } catch (error) {
      toast.error('Failed to share. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCopyLink = async () => {
    if (shareLink) {
      await navigator.clipboard.writeText(shareLink)
      setLinkCopied(true)
      toast.success('Link copied to clipboard!')
      setTimeout(() => setLinkCopied(false), 2000)
    }
  }

  const addRecipient = () => {
    if (newRecipient && !recipients.includes(newRecipient)) {
      setRecipients([...recipients, newRecipient])
      setNewRecipient('')
    }
  }

  const removeRecipient = (email: string) => {
    setRecipients(recipients.filter(r => r !== email))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && shareMethod === 'email') {
      e.preventDefault()
      addRecipient()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Globe className="h-5 w-5" />
            <span>Share {itemType}</span>
          </DialogTitle>
          <DialogDescription>
            Share "{itemTitle}" with others in your organization
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Share Method */}
          <div className="space-y-2">
            <Label>Share method</Label>
            <Select value={shareMethod} onValueChange={(value: any) => setShareMethod(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="link">
                  <div className="flex items-center space-x-2">
                    <ExternalLink className="h-4 w-4" />
                    <span>Share link</span>
                  </div>
                </SelectItem>
                <SelectItem value="email">
                  <div className="flex items-center space-x-2">
                    <Mail className="h-4 w-4" />
                    <span>Send via email</span>
                  </div>
                </SelectItem>
                <SelectItem value="invite">
                  <div className="flex items-center space-x-2">
                    <Users className="h-4 w-4" />
                    <span>Invite users</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Public/Private Toggle */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="public"
              checked={isPublic}
              onCheckedChange={(checked) => setIsPublic(checked === true)}
            />
            <Label htmlFor="public" className="flex items-center space-x-2">
              {isPublic ? <Globe className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
              <span>{isPublic ? 'Public access' : 'Private access'}</span>
            </Label>
          </div>

          {/* Permissions */}
          <div className="space-y-2">
            <Label>Permissions</Label>
            <Select value={permissions} onValueChange={(value: any) => setPermissions(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="view">
                  <div className="flex items-center space-x-2">
                    <Eye className="h-4 w-4" />
                    <span>View only</span>
                  </div>
                </SelectItem>
                <SelectItem value="edit">
                  <div className="flex items-center space-x-2">
                    <Users className="h-4 w-4" />
                    <span>Can edit</span>
                  </div>
                </SelectItem>
                <SelectItem value="admin">
                  <div className="flex items-center space-x-2">
                    <Users className="h-4 w-4" />
                    <span>Admin access</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Expiry Date */}
          <div className="space-y-2">
            <Label htmlFor="expiry">Expiry (optional)</Label>
            <Input
              id="expiry"
              type="datetime-local"
              value={expiry}
              onChange={(e) => setExpiry(e.target.value)}
            />
          </div>

          {/* Password Protection */}
          <div className="space-y-2">
            <Label htmlFor="password">Password (optional)</Label>
            <Input
              id="password"
              type="password"
              placeholder="Set a password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {/* Recipients for email/invite */}
          {(shareMethod === 'email' || shareMethod === 'invite') && (
            <div className="space-y-2">
              <Label>Recipients</Label>
              <div className="flex space-x-2">
                <Input
                  placeholder="Enter email address"
                  value={newRecipient}
                  onChange={(e) => setNewRecipient(e.target.value)}
                  onKeyPress={handleKeyPress}
                />
                <Button onClick={addRecipient} disabled={!newRecipient}>
                  Add
                </Button>
              </div>
              {recipients.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {recipients.map((email) => (
                    <Badge key={email} variant="secondary" className="flex items-center space-x-1">
                      <span>{email}</span>
                      <button
                        onClick={() => removeRecipient(email)}
                        className="ml-1 text-xs hover:text-destructive"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Message */}
          <div className="space-y-2">
            <Label htmlFor="message">Message (optional)</Label>
            <Textarea
              id="message"
              placeholder="Add a message..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={3}
            />
          </div>

          {/* Share Link Display */}
          {shareLink && (
            <Card>
              <CardContent className="p-3">
                <div className="flex items-center space-x-2">
                  <Input value={shareLink} readOnly className="font-mono text-xs" />
                  <Button
                    size="sm"
                    onClick={handleCopyLink}
                    className={cn(linkCopied && 'bg-green-500 hover:bg-green-600')}
                  >
                    {linkCopied ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleShare} disabled={loading}>
            {loading ? 'Sharing...' : 'Share'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}