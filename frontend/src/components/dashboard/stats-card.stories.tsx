import type { Meta, StoryObj } from '@storybook/react'
import { StatsCard } from './stats-card'
import { Monitor, Users, HardDrive, Activity } from 'lucide-react'

const meta: Meta<typeof StatsCard> = {
  title: 'Dashboard/StatsCard',
  component: StatsCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div className="w-80">
        <Story />
      </div>
    ),
  ],
}

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    title: 'Total Screens',
    value: '42',
    description: 'Active displays',
    icon: <Monitor className="h-4 w-4" />,
  },
}

export const WithPositiveTrend: Story = {
  args: {
    title: 'Active Users',
    value: '2,847',
    description: 'Current month',
    icon: <Users className="h-4 w-4" />,
    trend: {
      value: 12.5,
      label: 'from last month',
      direction: 'up',
    },
  },
}

export const WithNegativeTrend: Story = {
  args: {
    title: 'Storage Used',
    value: '78%',
    description: 'of 1TB limit',
    icon: <HardDrive className="h-4 w-4" />,
    trend: {
      value: -5.2,
      label: 'from last week',
      direction: 'down',
    },
  },
}

export const WithNeutralTrend: Story = {
  args: {
    title: 'System Health',
    value: '99.9%',
    description: 'Uptime',
    icon: <Activity className="h-4 w-4" />,
    trend: {
      value: 0,
      label: 'stable',
      direction: 'neutral',
    },
  },
}

export const Loading: Story = {
  args: {
    title: 'Loading...',
    value: '...',
    loading: true,
  },
}

export const LargeNumber: Story = {
  args: {
    title: 'Total Views',
    value: 1234567,
    description: 'All time',
    icon: <Activity className="h-4 w-4" />,
    trend: {
      value: 23.1,
      label: 'this quarter',
      direction: 'up',
    },
  },
}