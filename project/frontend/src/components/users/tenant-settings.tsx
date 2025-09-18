import React from 'react';

interface TenantSettingsProps {
  tenantId?: string;
}

export const TenantSettings: React.FC<TenantSettingsProps> = ({ tenantId }) => {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-medium mb-4">Tenant Settings</h3>
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium">Tenant Name</label>
          <input
            type="text"
            className="mt-1 block w-full rounded border border-input px-3 py-2"
            placeholder="Enter tenant name"
          />
        </div>
        <div>
          <label className="text-sm font-medium">Domain</label>
          <input
            type="text"
            className="mt-1 block w-full rounded border border-input px-3 py-2"
            placeholder="Enter domain"
          />
        </div>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded">
          Save Settings
        </button>
      </div>
    </div>
  );
};

export default TenantSettings;