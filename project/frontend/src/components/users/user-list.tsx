import React from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  status: 'active' | 'inactive';
}

interface UserListProps {
  users?: User[];
}

export const UserList: React.FC<UserListProps> = ({ users = [] }) => {
  return (
    <div className="rounded-lg border">
      <div className="p-4 border-b">
        <h3 className="font-medium">Users</h3>
      </div>
      <div className="divide-y">
        {users.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground">
            No users found
          </div>
        ) : (
          users.map((user) => (
            <div key={user.id} className="p-4 flex items-center justify-between">
              <div>
                <h4 className="font-medium">{user.name}</h4>
                <p className="text-sm text-muted-foreground">{user.email}</p>
              </div>
              <div className="text-right">
                <p className="text-sm">{user.role}</p>
                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  user.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {user.status}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default UserList;