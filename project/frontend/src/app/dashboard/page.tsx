import { DashboardStats } from '@/types'
import { StatsCard } from '@/components/dashboard/stats-card'
import { RecentActivity } from '@/components/dashboard/recent-activity'
import { UsageChart } from '@/components/dashboard/usage-chart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, Monitor, Users, HardDrive } from 'lucide-react'

// Mock data - akan diganti dengan API call nanti
const mockStats: DashboardStats = {
  totalScreens: 45,
  onlineScreens: 42,
  totalAssets: 156,
  totalPlaylists: 23,
  storageUsed: 2.1,
  storageLimit: 10,
  recentActivity: [
    {
      id: '1',
      type: 'asset_uploaded',
      description: 'New video uploaded: Product Demo 2024',
      userId: 'user1',
      userName: 'John Doe',
      timestamp: new Date().toISOString(),
    },
    {
      id: '2',
      type: 'screen_connected',
      description: 'Screen "Lobby Display" came online',
      userId: 'user2',
      userName: 'Jane Smith',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    },
    {
      id: '3',
      type: 'playlist_created',
      description: 'New playlist created: "Summer Campaign"',
      userId: 'user1',
      userName: 'John Doe',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    },
  ],
}

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your digital signage network
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Screens"
          value={mockStats.totalScreens}
          description={`${mockStats.onlineScreens} online`}
          icon={Monitor}
          trend={{ value: 12, isPositive: true }}
        />
        <StatsCard
          title="Total Assets"
          value={mockStats.totalAssets}
          description="Media files"
          icon={HardDrive}
          trend={{ value: 8, isPositive: true }}
        />
        <StatsCard
          title="Active Playlists"
          value={mockStats.totalPlaylists}
          description="Currently running"
          icon={Activity}
          trend={{ value: 3, isPositive: true }}
        />
        <StatsCard
          title="Storage Used"
          value={`${mockStats.storageUsed}GB`}
          description={`of ${mockStats.storageLimit}GB`}
          icon={HardDrive}
          trend={{ value: 21, isPositive: false }}
        />
      </div>

      {/* Charts and Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Network Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <UsageChart />
          </CardContent>
        </Card>

        <RecentActivity activities={mockStats.recentActivity} />
      </div>
    </div>
  )
}