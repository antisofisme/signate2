import React from 'react';

interface ActivityLog {
  id: string;
  userId: string;
  action: string;
  timestamp: string;
  details?: string;
}

interface UserActivityLogProps {
  activities?: ActivityLog[];
}

export const UserActivityLog: React.FC<UserActivityLogProps> = ({ activities = [] }) => {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-medium mb-4">Activity Log</h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {activities.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recent activity</p>
        ) : (
          activities.map((activity) => (
            <div key={activity.id} className="border-l-2 border-primary pl-3 py-1">
              <p className="text-sm">{activity.action}</p>
              <p className="text-xs text-muted-foreground">{activity.timestamp}</p>
              {activity.details && (
                <p className="text-xs text-muted-foreground mt-1">{activity.details}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default UserActivityLog;