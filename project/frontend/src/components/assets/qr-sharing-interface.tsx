'use client'

import React, { useState, useRef } from 'react'
import QRCode from 'qrcode'
import JsBarcode from 'jsbarcode'
import {
  QrCode,
  Barcode,
  Download,
  Copy,
  Share2,
  Eye,
  Settings,
  RefreshCw,
  ExternalLink,
  Printer,
  Mail,
  MessageSquare,
  Link
} from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { DatePicker } from '@/components/ui/date-picker'
import { Asset } from '@/types/api'
import { cn } from '@/lib/utils'
import { toast } from 'react-hot-toast'

interface QRSharingInterfaceProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  asset: Asset | null
}

interface ShareSettings {
  includePreview: boolean
  includeMetadata: boolean
  allowDownload: boolean
  requirePassword: boolean
  password: string
  expiresAt: Date | null
  customMessage: string
  trackViews: boolean
}

interface QRCodeSettings {
  size: number
  errorCorrectionLevel: 'L' | 'M' | 'Q' | 'H'
  margin: number
  color: {
    dark: string
    light: string
  }
}

interface BarcodeSettings {
  format: 'CODE128' | 'CODE39' | 'EAN13' | 'UPC'
  width: number
  height: number
  displayValue: boolean
  fontSize: number
  textMargin: number
}

const QR_ERROR_LEVELS = [
  { value: 'L', label: 'Low (~7%)', description: 'Low error correction' },
  { value: 'M', label: 'Medium (~15%)', description: 'Medium error correction' },
  { value: 'Q', label: 'Quartile (~25%)', description: 'Quartile error correction' },
  { value: 'H', label: 'High (~30%)', description: 'High error correction' }
]

const BARCODE_FORMATS = [
  { value: 'CODE128', label: 'Code 128', description: 'Most common format' },
  { value: 'CODE39', label: 'Code 39', description: 'Legacy format' },
  { value: 'EAN13', label: 'EAN-13', description: 'Product barcodes' },
  { value: 'UPC', label: 'UPC', description: 'US product codes' }
]

const SHARE_TEMPLATES = [
  {
    name: 'Public Gallery',
    description: 'Share for public viewing',
    settings: {
      includePreview: true,
      includeMetadata: true,
      allowDownload: false,
      requirePassword: false,
      trackViews: true
    }
  },
  {
    name: 'Download Access',
    description: 'Allow file downloads',
    settings: {
      includePreview: true,
      includeMetadata: false,
      allowDownload: true,
      requirePassword: false,
      trackViews: true
    }
  },
  {
    name: 'Secure Share',
    description: 'Password protected',
    settings: {
      includePreview: true,
      includeMetadata: false,
      allowDownload: false,
      requirePassword: true,
      trackViews: true
    }
  }
]

export const QRSharingInterface: React.FC<QRSharingInterfaceProps> = ({
  open,
  onOpenChange,
  asset
}) => {
  const [activeTab, setActiveTab] = useState('qr-code')
  const [shareUrl, setShareUrl] = useState('')
  const [qrDataUrl, setQrDataUrl] = useState('')
  const [barcodeDataUrl, setBarcodeDataUrl] = useState('')
  const qrCanvasRef = useRef<HTMLCanvasElement>(null)
  const barcodeCanvasRef = useRef<HTMLCanvasElement>(null)

  const [shareSettings, setShareSettings] = useState<ShareSettings>({
    includePreview: true,
    includeMetadata: true,
    allowDownload: false,
    requirePassword: false,
    password: '',
    expiresAt: null,
    customMessage: '',
    trackViews: true
  })

  const [qrSettings, setQrSettings] = useState<QRCodeSettings>({
    size: 256,
    errorCorrectionLevel: 'M',
    margin: 4,
    color: {
      dark: '#000000',
      light: '#ffffff'
    }
  })

  const [barcodeSettings, setBarcodeSettings] = useState<BarcodeSettings>({
    format: 'CODE128',
    width: 2,
    height: 100,
    displayValue: true,
    fontSize: 20,
    textMargin: 2
  })

  React.useEffect(() => {
    if (asset && open) {
      generateShareUrl()
    }
  }, [asset, open, shareSettings])

  React.useEffect(() => {
    if (shareUrl) {
      generateQRCode()
      generateBarcode()
    }
  }, [shareUrl, qrSettings, barcodeSettings])

  const generateShareUrl = () => {
    if (!asset) return

    const baseUrl = window.location.origin
    const params = new URLSearchParams()

    // Add share settings as URL parameters
    if (shareSettings.includePreview) params.set('preview', '1')
    if (shareSettings.includeMetadata) params.set('metadata', '1')
    if (shareSettings.allowDownload) params.set('download', '1')
    if (shareSettings.trackViews) params.set('track', '1')

    // Generate unique share ID (in real app, this would come from backend)
    const shareId = btoa(`${asset.asset_id}-${Date.now()}`).replace(/[+/=]/g, '')

    const url = `${baseUrl}/share/${shareId}?${params.toString()}`
    setShareUrl(url)
  }

  const generateQRCode = async () => {
    if (!shareUrl) return

    try {
      const dataUrl = await QRCode.toDataURL(shareUrl, {
        width: qrSettings.size,
        margin: qrSettings.margin,
        errorCorrectionLevel: qrSettings.errorCorrectionLevel,
        color: qrSettings.color
      })
      setQrDataUrl(dataUrl)
    } catch (error) {
      console.error('Failed to generate QR code:', error)
      toast.error('Failed to generate QR code')
    }
  }

  const generateBarcode = () => {
    if (!shareUrl || !barcodeCanvasRef.current) return

    try {
      // Use a shorter identifier for barcode (URLs are too long)
      const barcodeValue = asset ? asset.asset_id.replace(/[^a-zA-Z0-9]/g, '').slice(0, 12) : '123456789012'

      JsBarcode(barcodeCanvasRef.current, barcodeValue, {
        format: barcodeSettings.format,
        width: barcodeSettings.width,
        height: barcodeSettings.height,
        displayValue: barcodeSettings.displayValue,
        fontSize: barcodeSettings.fontSize,
        textMargin: barcodeSettings.textMargin
      })

      setBarcodeDataUrl(barcodeCanvasRef.current.toDataURL())
    } catch (error) {
      console.error('Failed to generate barcode:', error)
      toast.error('Failed to generate barcode')
    }
  }

  const downloadCode = (type: 'qr' | 'barcode') => {
    const dataUrl = type === 'qr' ? qrDataUrl : barcodeDataUrl
    if (!dataUrl || !asset) return

    const link = document.createElement('a')
    link.download = `${asset.name}-${type}-code.png`
    link.href = dataUrl
    link.click()
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('Copied to clipboard')
    } catch (error) {
      toast.error('Failed to copy to clipboard')
    }
  }

  const applyTemplate = (template: typeof SHARE_TEMPLATES[0]) => {
    setShareSettings(prev => ({
      ...prev,
      ...template.settings
    }))
    toast.success(`Applied "${template.name}" template`)
  }

  const shareViaEmail = () => {
    const subject = `Shared Asset: ${asset?.name}`
    const body = `I'm sharing this digital asset with you:\n\n${shareUrl}\n\n${shareSettings.customMessage}`
    const emailUrl = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
    window.open(emailUrl)
  }

  const shareViaSMS = () => {
    const message = `Check out this asset: ${shareUrl}`
    const smsUrl = `sms:?body=${encodeURIComponent(message)}`
    window.open(smsUrl)
  }

  const printCode = (type: 'qr' | 'barcode') => {
    const dataUrl = type === 'qr' ? qrDataUrl : barcodeDataUrl
    if (!dataUrl) return

    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>Print ${type.toUpperCase()} Code</title>
            <style>
              body { margin: 0; padding: 20px; text-align: center; }
              img { max-width: 100%; height: auto; }
              .info { margin-top: 20px; font-family: Arial, sans-serif; }
            </style>
          </head>
          <body>
            <img src="${dataUrl}" alt="${type.toUpperCase()} Code" />
            <div class="info">
              <h3>${asset?.name}</h3>
              <p>${shareUrl}</p>
            </div>
          </body>
        </html>
      `)
      printWindow.document.close()
      printWindow.print()
    }
  }

  if (!asset) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5" />
            Share Asset: {asset.name}
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="qr-code">QR Code</TabsTrigger>
            <TabsTrigger value="barcode">Barcode</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <div className="mt-4 overflow-y-auto max-h-[70vh]">
            <TabsContent value="qr-code" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* QR Code Display */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <QrCode className="h-5 w-5" />
                      QR Code
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-center">
                      {qrDataUrl ? (
                        <img
                          src={qrDataUrl}
                          alt="QR Code"
                          className="border rounded-lg"
                          style={{ maxWidth: qrSettings.size }}
                        />
                      ) : (
                        <div
                          className="border-2 border-dashed border-muted-foreground/25 rounded-lg flex items-center justify-center"
                          style={{ width: qrSettings.size, height: qrSettings.size }}
                        >
                          <QrCode className="h-12 w-12 text-muted-foreground" />
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Button onClick={() => downloadCode('qr')} size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                      <Button onClick={() => printCode('qr')} variant="outline" size="sm">
                        <Printer className="h-4 w-4 mr-2" />
                        Print
                      </Button>
                      <Button onClick={() => copyToClipboard(shareUrl)} variant="outline" size="sm">
                        <Copy className="h-4 w-4 mr-2" />
                        Copy URL
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* QR Code Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Settings className="h-5 w-5" />
                      QR Code Settings
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="qr-size">Size (pixels)</Label>
                      <Input
                        id="qr-size"
                        type="number"
                        value={qrSettings.size}
                        onChange={(e) => setQrSettings(prev => ({ ...prev, size: parseInt(e.target.value) || 256 }))}
                        min="128"
                        max="1024"
                        step="32"
                        className="mt-1"
                      />
                    </div>

                    <div>
                      <Label htmlFor="qr-error-level">Error Correction</Label>
                      <Select
                        value={qrSettings.errorCorrectionLevel}
                        onValueChange={(value: 'L' | 'M' | 'Q' | 'H') =>
                          setQrSettings(prev => ({ ...prev, errorCorrectionLevel: value }))
                        }
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {QR_ERROR_LEVELS.map(level => (
                            <SelectItem key={level.value} value={level.value}>
                              {level.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="qr-margin">Margin</Label>
                      <Input
                        id="qr-margin"
                        type="number"
                        value={qrSettings.margin}
                        onChange={(e) => setQrSettings(prev => ({ ...prev, margin: parseInt(e.target.value) || 4 }))}
                        min="0"
                        max="10"
                        className="mt-1"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="qr-dark-color">Foreground Color</Label>
                        <Input
                          id="qr-dark-color"
                          type="color"
                          value={qrSettings.color.dark}
                          onChange={(e) => setQrSettings(prev => ({
                            ...prev,
                            color: { ...prev.color, dark: e.target.value }
                          }))}
                          className="mt-1 h-10"
                        />
                      </div>
                      <div>
                        <Label htmlFor="qr-light-color">Background Color</Label>
                        <Input
                          id="qr-light-color"
                          type="color"
                          value={qrSettings.color.light}
                          onChange={(e) => setQrSettings(prev => ({
                            ...prev,
                            color: { ...prev.color, light: e.target.value }
                          }))}
                          className="mt-1 h-10"
                        />
                      </div>
                    </div>

                    <Button onClick={generateQRCode} variant="outline" className="w-full">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Regenerate QR Code
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="barcode" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Barcode Display */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Barcode className="h-5 w-5" />
                      Barcode
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-center">
                      <canvas
                        ref={barcodeCanvasRef}
                        className="border rounded-lg"
                        style={{ display: barcodeDataUrl ? 'none' : 'block' }}
                      />
                      {barcodeDataUrl && (
                        <img
                          src={barcodeDataUrl}
                          alt="Barcode"
                          className="border rounded-lg"
                        />
                      )}
                    </div>

                    <div className="text-center text-sm text-muted-foreground">
                      Asset ID: {asset.asset_id.slice(0, 12)}
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Button onClick={() => downloadCode('barcode')} size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                      <Button onClick={() => printCode('barcode')} variant="outline" size="sm">
                        <Printer className="h-4 w-4 mr-2" />
                        Print
                      </Button>
                      <Button onClick={() => copyToClipboard(asset.asset_id)} variant="outline" size="sm">
                        <Copy className="h-4 w-4 mr-2" />
                        Copy ID
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Barcode Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Settings className="h-5 w-5" />
                      Barcode Settings
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="barcode-format">Format</Label>
                      <Select
                        value={barcodeSettings.format}
                        onValueChange={(value: BarcodeSettings['format']) =>
                          setBarcodeSettings(prev => ({ ...prev, format: value }))
                        }
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {BARCODE_FORMATS.map(format => (
                            <SelectItem key={format.value} value={format.value}>
                              {format.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="barcode-width">Width</Label>
                        <Input
                          id="barcode-width"
                          type="number"
                          value={barcodeSettings.width}
                          onChange={(e) => setBarcodeSettings(prev => ({
                            ...prev,
                            width: parseInt(e.target.value) || 2
                          }))}
                          min="1"
                          max="5"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label htmlFor="barcode-height">Height</Label>
                        <Input
                          id="barcode-height"
                          type="number"
                          value={barcodeSettings.height}
                          onChange={(e) => setBarcodeSettings(prev => ({
                            ...prev,
                            height: parseInt(e.target.value) || 100
                          }))}
                          min="50"
                          max="200"
                          className="mt-1"
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="barcode-display-value">Show Text</Label>
                      <Switch
                        id="barcode-display-value"
                        checked={barcodeSettings.displayValue}
                        onCheckedChange={(checked) =>
                          setBarcodeSettings(prev => ({ ...prev, displayValue: checked }))
                        }
                      />
                    </div>

                    {barcodeSettings.displayValue && (
                      <div>
                        <Label htmlFor="barcode-font-size">Font Size</Label>
                        <Input
                          id="barcode-font-size"
                          type="number"
                          value={barcodeSettings.fontSize}
                          onChange={(e) => setBarcodeSettings(prev => ({
                            ...prev,
                            fontSize: parseInt(e.target.value) || 20
                          }))}
                          min="10"
                          max="30"
                          className="mt-1"
                        />
                      </div>
                    )}

                    <Button onClick={generateBarcode} variant="outline" className="w-full">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Regenerate Barcode
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="settings" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Share Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle>Share Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="include-preview">Include Preview</Label>
                        <Switch
                          id="include-preview"
                          checked={shareSettings.includePreview}
                          onCheckedChange={(checked) =>
                            setShareSettings(prev => ({ ...prev, includePreview: checked }))
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <Label htmlFor="include-metadata">Include Metadata</Label>
                        <Switch
                          id="include-metadata"
                          checked={shareSettings.includeMetadata}
                          onCheckedChange={(checked) =>
                            setShareSettings(prev => ({ ...prev, includeMetadata: checked }))
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <Label htmlFor="allow-download">Allow Download</Label>
                        <Switch
                          id="allow-download"
                          checked={shareSettings.allowDownload}
                          onCheckedChange={(checked) =>
                            setShareSettings(prev => ({ ...prev, allowDownload: checked }))
                          }
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <Label htmlFor="track-views">Track Views</Label>
                        <Switch
                          id="track-views"
                          checked={shareSettings.trackViews}
                          onCheckedChange={(checked) =>
                            setShareSettings(prev => ({ ...prev, trackViews: checked }))
                          }
                        />
                      </div>
                    </div>

                    <Separator />

                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="require-password">Password Protection</Label>
                        <Switch
                          id="require-password"
                          checked={shareSettings.requirePassword}
                          onCheckedChange={(checked) =>
                            setShareSettings(prev => ({ ...prev, requirePassword: checked }))
                          }
                        />
                      </div>

                      {shareSettings.requirePassword && (
                        <div>
                          <Label htmlFor="share-password">Password</Label>
                          <Input
                            id="share-password"
                            type="password"
                            value={shareSettings.password}
                            onChange={(e) =>
                              setShareSettings(prev => ({ ...prev, password: e.target.value }))
                            }
                            placeholder="Enter password"
                            className="mt-1"
                          />
                        </div>
                      )}

                      <div>
                        <Label>Expires On</Label>
                        <DatePicker
                          date={shareSettings.expiresAt}
                          setDate={(date) =>
                            setShareSettings(prev => ({ ...prev, expiresAt: date }))
                          }
                        />
                      </div>

                      <div>
                        <Label htmlFor="custom-message">Custom Message</Label>
                        <Textarea
                          id="custom-message"
                          value={shareSettings.customMessage}
                          onChange={(e) =>
                            setShareSettings(prev => ({ ...prev, customMessage: e.target.value }))
                          }
                          placeholder="Add a custom message for recipients"
                          rows={3}
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Templates & Share Actions */}
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Quick Templates</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {SHARE_TEMPLATES.map((template) => (
                        <Button
                          key={template.name}
                          variant="outline"
                          className="w-full justify-start"
                          onClick={() => applyTemplate(template)}
                        >
                          <div className="text-left">
                            <div className="font-medium">{template.name}</div>
                            <div className="text-xs text-muted-foreground">{template.description}</div>
                          </div>
                        </Button>
                      ))}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Share Via</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <Button onClick={shareViaEmail} variant="outline" className="w-full justify-start">
                        <Mail className="h-4 w-4 mr-2" />
                        Email
                      </Button>
                      <Button onClick={shareViaSMS} variant="outline" className="w-full justify-start">
                        <MessageSquare className="h-4 w-4 mr-2" />
                        SMS
                      </Button>
                      <Button
                        onClick={() => copyToClipboard(shareUrl)}
                        variant="outline"
                        className="w-full justify-start"
                      >
                        <Link className="h-4 w-4 mr-2" />
                        Copy Link
                      </Button>
                    </CardContent>
                  </Card>

                  {shareUrl && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Share URL</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="p-2 bg-muted rounded text-sm font-mono break-all">
                            {shareUrl}
                          </div>
                          <div className="flex gap-2">
                            <Button
                              onClick={() => copyToClipboard(shareUrl)}
                              size="sm"
                              className="flex-1"
                            >
                              <Copy className="h-4 w-4 mr-2" />
                              Copy
                            </Button>
                            <Button
                              onClick={() => window.open(shareUrl, '_blank')}
                              variant="outline"
                              size="sm"
                              className="flex-1"
                            >
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Preview
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}