# Content Sharing and Collaboration System

## Overview

The Content Sharing and Collaboration System provides advanced sharing capabilities with real-time collaboration features, social media integration, and comprehensive analytics. This system enables secure content distribution with granular access controls and interactive collaboration tools.

## Core Features

### 🔗 Advanced Sharing Options

#### Share Link Types
- **Public Links**: Accessible without authentication
- **Private Links**: Require user authentication
- **Password Protected**: Additional password security layer
- **Time-Limited**: Automatic expiration dates
- **Download Limited**: Quota-based access control

#### Sharing Permissions
- **Preview Only**: View content without downloading
- **Download Enabled**: Full file access
- **Comment Access**: Interactive annotation capabilities
- **Collaboration Mode**: Real-time editing and discussion

### 📱 Social Media Integration

#### Supported Platforms
- **Facebook**: Direct sharing with custom messages
- **Twitter**: Tweet with hashtags and mentions
- **LinkedIn**: Professional network sharing
- **WhatsApp**: Mobile messaging integration
- **Telegram**: Instant messaging distribution
- **Reddit**: Community-based sharing

#### Social Features
- **One-Click Sharing**: Pre-configured share buttons
- **Custom Messages**: Platform-specific content optimization
- **Analytics Tracking**: Social engagement metrics
- **QR Code Generation**: Mobile-friendly access codes

### 💬 Collaboration Tools

#### Real-Time Features
- **Live Comments**: Instant discussion threads
- **Position Annotations**: Location-specific comments on images/videos
- **Cursor Tracking**: See other users' activity
- **Live Notifications**: Real-time activity updates

#### Collaboration Sessions
- **Multi-User Access**: Simultaneous user collaboration
- **Voice Chat Integration**: Audio communication support
- **Screen Sharing**: Collaborative viewing sessions
- **Session Recording**: Capture collaboration history

### 📊 Analytics and Insights

#### Usage Analytics
- **View Tracking**: Detailed access logs
- **Geographic Data**: Location-based analytics
- **Device Analysis**: Platform and browser statistics
- **Engagement Metrics**: Time spent and interaction data

#### Advanced Reporting
- **Conversion Tracking**: View-to-download ratios
- **Referrer Analysis**: Traffic source identification
- **User Behavior**: Access pattern analysis
- **Performance Metrics**: Load times and engagement rates

## API Reference

### Share Link Management

#### Create Share Link
```http
POST /api/v3/assets/{id}/share/
Content-Type: application/json

{
    "share_type": "protected",
    "password": "secure123",
    "allow_download": true,
    "allow_preview": true,
    "allow_comments": true,
    "expires_in_hours": 168,
    "max_downloads": 50,
    "title": "Project Proposal",
    "description": "Q1 project proposal for review"
}
```

**Response:**
```json
{
    "id": 123,
    "uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "share_url": "https://example.com/share/f47ac10b-58cc-4372-a567-0e02b2c3d479/",
    "qr_code_data": "data:image/png;base64,iVBOR...",
    "social_links": {
        "facebook": "https://www.facebook.com/sharer/sharer.php?u=...",
        "twitter": "https://twitter.com/intent/tweet?url=...",
        "linkedin": "https://www.linkedin.com/sharing/share-offsite/?url=..."
    },
    "embed_code": "<iframe src='...' width='600' height='400'></iframe>",
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-22T10:30:00Z"
}
```

#### List Share Links
```http
GET /api/v3/shares/
```

#### Access Shared Content
```http
GET /share/{uuid}/
```

### Collaboration Features

#### Create Collaboration Session
```http
POST /api/v3/collaboration/sessions/
Content-Type: application/json

{
    "asset_id": 123,
    "participants": [
        {"email": "user1@example.com"},
        {"email": "user2@example.com"}
    ],
    "session_config": {
        "duration_hours": 24,
        "allow_download": false,
        "cursor_tracking": true,
        "voice_chat": true,
        "invitation_message": "Please review the marketing materials"
    }
}
```

#### Add Comments
```http
POST /api/v3/assets/{id}/comments/
Content-Type: application/json

{
    "content": "Please update the logo in the top-right corner",
    "position_x": 0.85,
    "position_y": 0.15,
    "timestamp": "00:01:30",
    "parent_comment_id": null
}
```

### Analytics Endpoints

#### Asset Analytics
```http
GET /api/v3/assets/{id}/analytics/?days=30
```

**Response:**
```json
{
    "summary": {
        "total_views": 156,
        "total_downloads": 23,
        "unique_visitors": 78,
        "conversion_rate": 14.7
    },
    "geographic_breakdown": [
        {"country": "US", "views": 89},
        {"country": "CA", "views": 34},
        {"country": "UK", "views": 33}
    ],
    "device_breakdown": [
        {"device_type": "desktop", "views": 92},
        {"device_type": "mobile", "views": 64}
    ],
    "daily_breakdown": [
        {
            "date": "2024-01-15",
            "views": 12,
            "downloads": 3,
            "unique_visitors": 8
        }
    ]
}
```

#### Share Link Analytics
```http
GET /api/v3/shares/{uuid}/analytics/?days=7
```

## Implementation Guide

### Setting Up Content Sharing

#### 1. Basic Share Link Creation

```python
from project.backend.utils.content_sharing import ContentSharingService

# Create a simple public share
share_config = {
    'share_type': 'public',
    'allow_download': True,
    'allow_preview': True,
    'expires_in_hours': 168  # 1 week
}

share_data = ContentSharingService.create_share_link(
    asset, request.user, share_config
)

# Access the generated components
share_link = share_data['share_link']
qr_code = share_data['qr_code']
social_links = share_data['social_links']
embed_code = share_data['embed_code']
```

#### 2. Advanced Sharing with Analytics

```python
# Create protected share with analytics
share_config = {
    'share_type': 'protected',
    'password': 'MySecurePass123',
    'allow_download': True,
    'allow_comments': True,
    'max_downloads': 25,
    'expires_in_hours': 72,
    'title': 'Confidential Project Files',
    'description': 'Internal review materials',
    'notify_on_access': True
}

share_data = ContentSharingService.create_share_link(
    asset, request.user, share_config
)

# Generate comprehensive analytics
analytics = ContentSharingService.generate_sharing_analytics(
    share_data['share_link'],
    date_range=30
)
```

### Social Media Integration

#### 1. Configure Social Platforms

```python
# settings.py
SOCIAL_SHARING = {
    'FACEBOOK_APP_ID': 'your_facebook_app_id',
    'TWITTER_API_KEY': 'your_twitter_api_key',
    'LINKEDIN_CLIENT_ID': 'your_linkedin_client_id',
    'DEFAULT_HASHTAGS': ['content', 'sharing'],
    'CUSTOM_MESSAGES': {
        'facebook': "Check out this amazing content!",
        'twitter': "Don't miss this! {title} {url} #content",
        'linkedin': "Professional content worth sharing: {title}"
    }
}
```

#### 2. Generate Social Sharing Links

```python
# Generate platform-specific sharing URLs
social_links = ContentSharingService.generate_social_sharing_links(share_link)

# Returns:
# {
#     'facebook': 'https://www.facebook.com/sharer/sharer.php?u=...',
#     'twitter': 'https://twitter.com/intent/tweet?url=...',
#     'linkedin': 'https://www.linkedin.com/sharing/share-offsite/?url=...',
#     'whatsapp': 'https://wa.me/?text=...',
#     'telegram': 'https://t.me/share/url?url=...',
#     'reddit': 'https://reddit.com/submit?url=...'
# }
```

#### 3. Custom QR Code Generation

```python
# Generate custom QR codes
qr_data = ContentSharingService.generate_qr_code(
    share_link,
    size=(300, 300),
    format='PNG'
)

# Returns base64 encoded QR code image
qr_image = qr_data['qr_code_data']
```

### Collaboration Features

#### 1. Real-Time Collaboration Setup

```python
# Create collaboration session
collaboration_data = ContentSharingService.create_collaboration_session(
    asset=asset,
    participants=[user1, user2, user3],
    session_config={
        'duration_hours': 48,
        'allow_download': False,
        'cursor_tracking': True,
        'voice_chat': True,
        'screen_sharing': False,
        'invitation_message': 'Please review and provide feedback'
    }
)

# Returns:
# {
#     'session_id': 'uuid',
#     'share_link': ShareLink object,
#     'participants': [users],
#     'features': {...},
#     'websocket_url': '/ws/collaboration/session_id/',
#     'collaboration_url': '/collaborate/share_uuid/'
# }
```

#### 2. Comment System Integration

```python
# Add positioned comment to asset
comment_data = {
    'content': 'Please adjust the brightness here',
    'position_x': 0.75,  # 75% from left
    'position_y': 0.40,  # 40% from top
    'timestamp': timedelta(minutes=1, seconds=30)  # For video
}

comment = ContentSharingService.create_comment_thread(
    asset, comment_data, request.user
)
```

#### 3. WebSocket Integration for Real-Time Features

```python
# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CollaborationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'collaboration_{self.session_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']

        if message_type == 'cursor_position':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'cursor_update',
                    'user_id': data['user_id'],
                    'x': data['x'],
                    'y': data['y']
                }
            )
        elif message_type == 'comment':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'new_comment',
                    'comment': data['comment']
                }
            )

    async def cursor_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'cursor_position',
            'user_id': event['user_id'],
            'x': event['x'],
            'y': event['y']
        }))

    async def new_comment(self, event):
        await self.send(text_data=json.dumps({
            'type': 'comment',
            'comment': event['comment']
        }))
```

### Analytics and Reporting

#### 1. Access Tracking Implementation

```python
# Track share link access
def track_share_access(request, share_link):
    ContentSharingService.track_share_access(
        share_link,
        request,
        event_type='view'
    )

# Track download
def track_download(request, share_link):
    ContentSharingService.track_share_access(
        share_link,
        request,
        event_type='download'
    )
```

#### 2. Generate Analytics Reports

```python
# Comprehensive analytics
analytics = ContentSharingService.generate_sharing_analytics(
    share_link,
    date_range=30
)

# Returns detailed metrics:
# - View/download counts
# - Geographic breakdown
# - Device/browser statistics
# - Referrer analysis
# - Daily trends
# - Conversion rates
```

#### 3. Real-Time Analytics Dashboard

```python
# views.py
class ShareAnalyticsView(APIView):
    def get(self, request, uuid):
        share_link = get_object_or_404(ShareLink, uuid=uuid)

        # Real-time metrics
        analytics = ContentSharingService.generate_sharing_analytics(
            share_link,
            date_range=int(request.GET.get('days', 30))
        )

        return Response(analytics)
```

## Frontend Integration

### JavaScript SDK

#### 1. Share Button Integration

```javascript
// share-widget.js
class ShareWidget {
    constructor(assetId, options = {}) {
        this.assetId = assetId;
        this.options = options;
        this.init();
    }

    async init() {
        const shareData = await this.createShareLink();
        this.renderShareButtons(shareData);
    }

    async createShareLink() {
        const response = await fetch(`/api/v3/assets/${this.assetId}/share/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify(this.options)
        });
        return response.json();
    }

    renderShareButtons(shareData) {
        const container = document.getElementById('share-buttons');

        // Social media buttons
        Object.entries(shareData.social_links).forEach(([platform, url]) => {
            const button = document.createElement('a');
            button.href = url;
            button.target = '_blank';
            button.className = `share-btn share-${platform}`;
            button.textContent = platform.charAt(0).toUpperCase() + platform.slice(1);
            container.appendChild(button);
        });

        // QR Code
        const qrImg = document.createElement('img');
        qrImg.src = shareData.qr_code_data;
        qrImg.alt = 'QR Code for sharing';
        container.appendChild(qrImg);

        // Copy link button
        const copyBtn = document.createElement('button');
        copyBtn.textContent = 'Copy Link';
        copyBtn.onclick = () => this.copyToClipboard(shareData.share_url);
        container.appendChild(copyBtn);
    }

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            alert('Share link copied to clipboard!');
        });
    }
}

// Usage
const shareWidget = new ShareWidget(123, {
    share_type: 'public',
    allow_download: true,
    expires_in_hours: 168
});
```

#### 2. Collaboration Interface

```javascript
// collaboration.js
class CollaborationClient {
    constructor(sessionId, assetId) {
        this.sessionId = sessionId;
        this.assetId = assetId;
        this.websocket = null;
        this.cursors = new Map();
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.setupEventListeners();
    }

    connectWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws/collaboration/${this.sessionId}/`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            console.log('Collaboration session connected');
        };

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.websocket.onclose = () => {
            console.log('Collaboration session disconnected');
            // Attempt reconnection
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    setupEventListeners() {
        // Track cursor movement
        document.addEventListener('mousemove', (e) => {
            const x = e.clientX / window.innerWidth;
            const y = e.clientY / window.innerHeight;

            this.sendMessage({
                type: 'cursor_position',
                user_id: this.getUserId(),
                x: x,
                y: y
            });
        });

        // Comment creation
        document.addEventListener('click', (e) => {
            if (e.shiftKey) {  // Shift+click to add comment
                this.createComment(e.clientX, e.clientY);
            }
        });
    }

    handleMessage(data) {
        switch (data.type) {
            case 'cursor_position':
                this.updateCursor(data.user_id, data.x, data.y);
                break;
            case 'comment':
                this.displayComment(data.comment);
                break;
        }
    }

    updateCursor(userId, x, y) {
        let cursor = this.cursors.get(userId);
        if (!cursor) {
            cursor = this.createCursorElement(userId);
            this.cursors.set(userId, cursor);
        }

        cursor.style.left = `${x * 100}%`;
        cursor.style.top = `${y * 100}%`;
    }

    createComment(x, y) {
        const content = prompt('Enter your comment:');
        if (content) {
            const comment = {
                content: content,
                position_x: x / window.innerWidth,
                position_y: y / window.innerHeight,
                timestamp: new Date().toISOString()
            };

            this.sendMessage({
                type: 'comment',
                comment: comment
            });
        }
    }

    sendMessage(data) {
        if (this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(data));
        }
    }
}
```

#### 3. Analytics Dashboard

```javascript
// analytics-dashboard.js
class AnalyticsDashboard {
    constructor(shareUuid) {
        this.shareUuid = shareUuid;
        this.charts = {};
        this.init();
    }

    async init() {
        const data = await this.fetchAnalytics();
        this.renderDashboard(data);
        this.setupRealTimeUpdates();
    }

    async fetchAnalytics(days = 30) {
        const response = await fetch(`/api/v3/shares/${this.shareUuid}/analytics/?days=${days}`);
        return response.json();
    }

    renderDashboard(data) {
        this.renderSummaryCards(data.summary);
        this.renderGeographicChart(data.geographic_breakdown);
        this.renderDeviceChart(data.device_breakdown);
        this.renderTimelineChart(data.daily_breakdown);
    }

    renderSummaryCards(summary) {
        document.getElementById('total-views').textContent = summary.total_views;
        document.getElementById('total-downloads').textContent = summary.total_downloads;
        document.getElementById('unique-visitors').textContent = summary.unique_visitors;
        document.getElementById('conversion-rate').textContent = `${summary.conversion_rate.toFixed(1)}%`;
    }

    renderGeographicChart(data) {
        // Implementation with Chart.js or similar
        const ctx = document.getElementById('geographic-chart').getContext('2d');
        this.charts.geographic = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(item => item.country),
                datasets: [{
                    data: data.map(item => item.views),
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
                }]
            }
        });
    }

    setupRealTimeUpdates() {
        setInterval(async () => {
            const data = await this.fetchAnalytics();
            this.updateCharts(data);
        }, 30000); // Update every 30 seconds
    }
}
```

## Security Considerations

### Access Control

#### 1. Share Link Security

```python
# Secure UUID generation
import secrets
import uuid

class ShareLink(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.uuid:
            # Use cryptographically secure random UUID
            self.uuid = uuid.UUID(bytes=secrets.token_bytes(16))
        super().save(*args, **kwargs)
```

#### 2. Password Protection

```python
from django.contrib.auth.hashers import make_password, check_password

class ShareLink(models.Model):
    password = models.CharField(max_length=128, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
```

#### 3. Rate Limiting

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='GET')
def share_access_view(request, uuid):
    # Limit access attempts per IP
    pass

@ratelimit(key='user', rate='50/h', method='POST')
def create_share_link(request):
    # Limit share link creation per user
    pass
```

### Data Privacy

#### 1. Analytics Anonymization

```python
import hashlib

def anonymize_ip(ip_address):
    # Hash IP addresses for privacy
    return hashlib.sha256(ip_address.encode()).hexdigest()[:16]

def track_access(share_link, request):
    AssetAnalytics.objects.create(
        asset=share_link.asset,
        event_type='view',
        ip_address=anonymize_ip(get_client_ip(request)),
        # ... other fields
    )
```

#### 2. Data Retention Policies

```python
# tasks.py
@shared_task
def cleanup_analytics_data():
    # Remove analytics data older than 1 year
    cutoff_date = timezone.now() - timedelta(days=365)
    AssetAnalytics.objects.filter(timestamp__lt=cutoff_date).delete()
```

## Best Practices

### Performance Optimization

1. **Caching Strategy**
   - Cache share link metadata
   - Redis for real-time collaboration data
   - CDN for static assets and thumbnails

2. **Database Optimization**
   - Proper indexing on UUID fields
   - Pagination for analytics queries
   - Aggregate data for dashboard views

3. **Real-Time Features**
   - Use WebSocket connection pooling
   - Implement message rate limiting
   - Graceful degradation for high load

### User Experience

1. **Progressive Enhancement**
   - Basic sharing works without JavaScript
   - Enhanced features with JS enabled
   - Mobile-responsive design

2. **Error Handling**
   - Graceful failure for expired links
   - Clear error messages
   - Fallback options

3. **Accessibility**
   - Screen reader support
   - Keyboard navigation
   - High contrast mode support

This comprehensive sharing and collaboration system provides enterprise-grade content distribution with advanced analytics and real-time collaboration features while maintaining security and performance.