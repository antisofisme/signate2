import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  FileText,
  Users,
  Settings,
  BarChart3,
  Shield,
  Folder,
  PlusCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { useSidebar } from '@/store/appStore';
import { useAuthStore, useHasRole } from '@/store/authStore';
import { NavigationItem } from '@/types';

const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { sidebarOpen, sidebarCollapsed, setSidebarOpen, toggleSidebarCollapsed } = useSidebar();
  const { user, tenant } = useAuthStore();
  const canManage = useHasRole(['admin', 'manager']);
  const isAdmin = useHasRole('admin');

  const navigationItems: NavigationItem[] = [
    {
      title: 'Dashboard',
      href: '/dashboard',
      icon: Home,
      description: 'Overview and analytics',
    },
    {
      title: 'Content',
      href: '/dashboard/content',
      icon: FileText,
      description: 'Manage your content',
      children: [
        {
          title: 'All Content',
          href: '/dashboard/content',
          icon: Folder,
        },
        {
          title: 'Create New',
          href: '/dashboard/content/new',
          icon: PlusCircle,
        },
      ],
    },
    {
      title: 'Analytics',
      href: '/dashboard/analytics',
      icon: BarChart3,
      description: 'Performance metrics',
    },
  ];

  // Add management items for users with appropriate permissions
  if (canManage) {
    navigationItems.push({
      title: 'Users',
      href: '/dashboard/users',
      icon: Users,
      description: 'User management',
    });
  }

  // Add admin-only items
  if (isAdmin) {
    navigationItems.push(
      {
        title: 'Security',
        href: '/dashboard/security',
        icon: Shield,
        description: 'Security settings',
      },
      {
        title: 'Settings',
        href: '/dashboard/settings',
        icon: Settings,
        description: 'System configuration',
      }
    );
  }

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Desktop Sidebar */}
      <div
        className={cn(
          'fixed top-0 left-0 z-50 h-full bg-card border-r transition-all duration-300 ease-in-out hidden lg:block',
          sidebarCollapsed ? 'w-16' : 'w-64'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center border-b px-4">
            {sidebarCollapsed ? (
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-lg">A</span>
              </div>
            ) : (
              <Link href="/dashboard" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <span className="text-primary-foreground font-bold text-lg">A</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-lg font-bold">Anthias</span>
                  {tenant && (
                    <span className="text-xs text-muted-foreground truncate">
                      {tenant.name}
                    </span>
                  )}
                </div>
              </Link>
            )}
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 px-3 py-4">
            <nav className="space-y-2">
              {navigationItems.map((item) => (
                <div key={item.href}>
                  <Link href={item.href}>
                    <Button
                      variant={isActive(item.href) ? 'secondary' : 'ghost'}
                      className={cn(
                        'w-full justify-start',
                        sidebarCollapsed ? 'px-2' : 'px-3'
                      )}
                      disabled={item.disabled}
                    >
                      {item.icon && (
                        <item.icon
                          className={cn(
                            'h-5 w-5',
                            sidebarCollapsed ? 'mr-0' : 'mr-3'
                          )}
                        />
                      )}
                      {!sidebarCollapsed && (
                        <span className="truncate">{item.title}</span>
                      )}
                    </Button>
                  </Link>

                  {/* Sub-navigation */}
                  {!sidebarCollapsed && item.children && isActive(item.href) && (
                    <div className="ml-6 mt-2 space-y-1">
                      {item.children.map((child) => (
                        <Link key={child.href} href={child.href}>
                          <Button
                            variant={pathname === child.href ? 'secondary' : 'ghost'}
                            size="sm"
                            className="w-full justify-start"
                          >
                            {child.icon && (
                              <child.icon className="h-4 w-4 mr-2" />
                            )}
                            <span className="truncate">{child.title}</span>
                          </Button>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </nav>
          </ScrollArea>

          {/* User info and collapse button */}
          <div className="border-t p-4">
            {!sidebarCollapsed && user && (
              <div className="mb-4 space-y-1">
                <p className="text-sm font-medium truncate">
                  {user.firstName} {user.lastName}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {user.email}
                </p>
              </div>
            )}

            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebarCollapsed}
              className="w-full"
            >
              {sidebarCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed left-0 top-0 h-full w-64 bg-card border-r">
            <div className="flex h-full flex-col">
              {/* Logo */}
              <div className="flex h-16 items-center border-b px-4">
                <Link href="/dashboard" className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                    <span className="text-primary-foreground font-bold text-lg">A</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-lg font-bold">Anthias</span>
                    {tenant && (
                      <span className="text-xs text-muted-foreground truncate">
                        {tenant.name}
                      </span>
                    )}
                  </div>
                </Link>
              </div>

              {/* Navigation */}
              <ScrollArea className="flex-1 px-3 py-4">
                <nav className="space-y-2">
                  {navigationItems.map((item) => (
                    <div key={item.href}>
                      <Link href={item.href} onClick={() => setSidebarOpen(false)}>
                        <Button
                          variant={isActive(item.href) ? 'secondary' : 'ghost'}
                          className="w-full justify-start px-3"
                          disabled={item.disabled}
                        >
                          {item.icon && (
                            <item.icon className="h-5 w-5 mr-3" />
                          )}
                          <span className="truncate">{item.title}</span>
                        </Button>
                      </Link>

                      {/* Sub-navigation */}
                      {item.children && isActive(item.href) && (
                        <div className="ml-6 mt-2 space-y-1">
                          {item.children.map((child) => (
                            <Link
                              key={child.href}
                              href={child.href}
                              onClick={() => setSidebarOpen(false)}
                            >
                              <Button
                                variant={pathname === child.href ? 'secondary' : 'ghost'}
                                size="sm"
                                className="w-full justify-start"
                              >
                                {child.icon && (
                                  <child.icon className="h-4 w-4 mr-2" />
                                )}
                                <span className="truncate">{child.title}</span>
                              </Button>
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </nav>
              </ScrollArea>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export { Sidebar };