/**
 * User Management Dashboard
 * Main page for user administration and tenant management
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Plus, Users, Settings, Shield, Activity } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

import DashboardLayout from '@/components/layout/DashboardLayout';
import UserList from '@/components/users/user-list';
import TenantSettings from '@/components/users/tenant-settings';
import RoleManagement from '@/components/users/role-management';
import UserActivityLog from '@/components/users/user-activity-log';
import CreateUserModal from '@/components/users/create-user-modal';

import { useAuth } from '@/hooks/auth';
import { useUserStore } from '@/stores/users';

const UserManagementPage: React.FC = () => {
  const router = useRouter();
  const { user, hasPermission } = useAuth();
  const {
    users,
    loading,
    stats,
    fetchUsers,
    fetchUserStats
  } = useUserStore();

  const [activeTab, setActiveTab] = useState('users');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    if (!hasPermission('user_management.read')) {
      router.push('/dashboard');
      return;
    }

    fetchUsers();
    fetchUserStats();
  }, []);

  const handleCreateUser = () => {
    setIsCreateModalOpen(true);
  };

  const handleUserCreated = () => {
    fetchUsers();
    fetchUserStats();
    setIsCreateModalOpen(false);
  };

  if (!hasPermission('user_management.read')) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">You don't have permission to access this page.</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">User Management</h1>
            <p className="text-muted-foreground">
              Manage users, roles, and tenant settings
            </p>
          </div>
          {hasPermission('user_management.create') && (
            <Button onClick={handleCreateUser} className="gap-2">
              <Plus className="h-4 w-4" />
              Add User
            </Button>
          )}
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Users</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.totalUsers || 0}</div>
              <p className="text-xs text-muted-foreground">
                {stats?.newUsersThisMonth || 0} new this month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Users</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.activeUsers || 0}</div>
              <p className="text-xs text-muted-foreground">
                {stats?.activeUsersChange || 0}% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Roles</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.totalRoles || 0}</div>
              <p className="text-xs text-muted-foreground">
                Across all tenants
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tenant Usage</CardTitle>
              <Settings className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.tenantUsage || '0%'}</div>
              <p className="text-xs text-muted-foreground">
                Current storage usage
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="roles">Roles & Permissions</TabsTrigger>
            <TabsTrigger value="tenant">Tenant Settings</TabsTrigger>
            <TabsTrigger value="activity">Activity Log</TabsTrigger>
          </TabsList>

          <div className="mt-6">
            <TabsContent value="users">
              <Card>
                <CardHeader>
                  <CardTitle>User Management</CardTitle>
                  <CardDescription>
                    Manage user accounts, status, and permissions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <UserList
                    users={users}
                    loading={loading}
                    onUserUpdate={() => {
                      fetchUsers();
                      fetchUserStats();
                    }}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="roles">
              <Card>
                <CardHeader>
                  <CardTitle>Role & Permission Management</CardTitle>
                  <CardDescription>
                    Configure roles and assign permissions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <RoleManagement />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="tenant">
              <Card>
                <CardHeader>
                  <CardTitle>Tenant Settings</CardTitle>
                  <CardDescription>
                    Configure tenant-specific settings and preferences
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <TenantSettings />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="activity">
              <Card>
                <CardHeader>
                  <CardTitle>User Activity Log</CardTitle>
                  <CardDescription>
                    Monitor user actions and system events
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <UserActivityLog />
                </CardContent>
              </Card>
            </TabsContent>
          </div>
        </Tabs>
      </div>

      {/* Create User Modal */}
      <CreateUserModal
        open={isCreateModalOpen}
        onOpenChange={setIsCreateModalOpen}
        onUserCreated={handleUserCreated}
      />
    </DashboardLayout>
  );
};

export default UserManagementPage;