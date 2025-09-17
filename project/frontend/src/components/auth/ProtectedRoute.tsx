import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { PageLoading } from '@/components/ui/loading';
import { Unauthorized } from '@/components/ui/error';
import { UserRole } from '@/types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: UserRole | UserRole[];
  redirectTo?: string;
  fallback?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  redirectTo = '/auth/login',
  fallback,
}) => {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, getProfile } = useAuthStore();

  useEffect(() => {
    // Try to get profile if we have a token but no user data
    const token = document.cookie
      .split('; ')
      .find(row => row.startsWith('auth_token='))
      ?.split('=')[1];

    if (token && !user && !isLoading) {
      getProfile().catch(() => {
        // If profile fetch fails, redirect to login
        router.push(redirectTo);
      });
    }
  }, [user, isLoading, getProfile, router, redirectTo]);

  // Show loading while checking authentication
  if (isLoading) {
    return <PageLoading message="Checking authentication..." />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    router.push(redirectTo);
    return <PageLoading message="Redirecting to login..." />;
  }

  // Check role requirements
  if (requiredRole) {
    const hasRequiredRole = Array.isArray(requiredRole)
      ? requiredRole.includes(user.role)
      : user.role === requiredRole;

    if (!hasRequiredRole) {
      if (fallback) {
        return <>{fallback}</>;
      }
      return (
        <Unauthorized
          message="You do not have the required permissions to access this page."
          onLogin={() => router.push('/auth/login')}
        />
      );
    }
  }

  return <>{children}</>;
};

// Higher-order component for protecting pages
export function withProtection<P extends object>(
  Component: React.ComponentType<P>,
  options?: Omit<ProtectedRouteProps, 'children'>
) {
  const ProtectedComponent: React.FC<P> = (props) => {
    return (
      <ProtectedRoute {...options}>
        <Component {...props} />
      </ProtectedRoute>
    );
  };

  ProtectedComponent.displayName = `withProtection(${Component.displayName || Component.name})`;

  return ProtectedComponent;
}

// Hook for role-based conditional rendering
export function useRoleAccess(requiredRole: UserRole | UserRole[]) {
  const { user } = useAuthStore();

  if (!user) return false;

  return Array.isArray(requiredRole)
    ? requiredRole.includes(user.role)
    : user.role === requiredRole;
}

// Component for role-based conditional rendering
export const RoleGuard: React.FC<{
  requiredRole: UserRole | UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ requiredRole, children, fallback = null }) => {
  const hasAccess = useRoleAccess(requiredRole);

  return hasAccess ? <>{children}</> : <>{fallback}</>;
};

export default ProtectedRoute;