import React from 'react';

interface Alert {
  id: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
}

interface AlertsPanelProps {
  alerts?: Alert[];
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({ alerts = [] }) => {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-medium mb-4">Recent Alerts</h3>
      <div className="space-y-2">
        {alerts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No alerts</p>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className="flex items-start space-x-2 p-2 rounded border-l-4 border-l-yellow-500">
              <div className="flex-1">
                <p className="text-sm">{alert.message}</p>
                <p className="text-xs text-muted-foreground">{alert.timestamp}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AlertsPanel;