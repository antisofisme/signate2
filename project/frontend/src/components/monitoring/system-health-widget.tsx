import React from 'react';

interface SystemHealthWidgetProps {
  cpu?: number;
  memory?: number;
  storage?: number;
}

export const SystemHealthWidget: React.FC<SystemHealthWidgetProps> = ({
  cpu = 0,
  memory = 0,
  storage = 0
}) => {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-medium mb-4">System Health</h3>
      <div className="space-y-3">
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-sm text-muted-foreground">CPU</span>
            <span className="text-sm">{cpu}%</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full"
              style={{ width: `${cpu}%` }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-sm text-muted-foreground">Memory</span>
            <span className="text-sm">{memory}%</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full"
              style={{ width: `${memory}%` }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-sm text-muted-foreground">Storage</span>
            <span className="text-sm">{storage}%</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full"
              style={{ width: `${storage}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthWidget;