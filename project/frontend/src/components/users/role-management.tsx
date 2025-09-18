import React from 'react';

interface Role {
  id: string;
  name: string;
  permissions: string[];
}

interface RoleManagementProps {
  roles?: Role[];
}

export const RoleManagement: React.FC<RoleManagementProps> = ({ roles = [] }) => {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-medium mb-4">Role Management</h3>
      <div className="space-y-2">
        {roles.length === 0 ? (
          <p className="text-sm text-muted-foreground">No roles configured</p>
        ) : (
          roles.map((role) => (
            <div key={role.id} className="border rounded p-3">
              <h4 className="font-medium">{role.name}</h4>
              <p className="text-sm text-muted-foreground">
                {role.permissions.length} permissions
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default RoleManagement;