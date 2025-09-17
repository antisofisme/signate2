import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from './button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { cn } from '@/lib/utils';
import { ErrorProps } from '@/types';

const ErrorComponent: React.FC<ErrorProps> = ({
  className,
  title = 'Something went wrong',
  message,
  onRetry,
  children
}) => {
  return (
    <Card className={cn('max-w-md mx-auto', className)}>
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertTriangle className="w-6 h-6 text-destructive" />
        </div>
        <CardTitle className="text-destructive">{title}</CardTitle>
        <CardDescription>{message}</CardDescription>
      </CardHeader>
      <CardContent className="text-center space-y-4">
        {children}
        <div className="flex justify-center space-x-2">
          {onRetry && (
            <Button onClick={onRetry} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          )}
          <Button
            onClick={() => window.location.href = '/'}
            variant="default"
            size="sm"
          >
            <Home className="w-4 h-4 mr-2" />
            Go Home
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// 404 Error Page
export const NotFound: React.FC<{
  title?: string;
  message?: string;
  showHomeButton?: boolean;
}> = ({
  title = 'Page Not Found',
  message = 'The page you are looking for does not exist.',
  showHomeButton = true
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-6xl font-bold text-muted-foreground">404</h1>
          <h2 className="text-2xl font-semibold">{title}</h2>
          <p className="text-muted-foreground max-w-md">{message}</p>
        </div>
        {showHomeButton && (
          <Button onClick={() => window.location.href = '/'}>
            <Home className="w-4 h-4 mr-2" />
            Return Home
          </Button>
        )}
      </div>
    </div>
  );
};

// Unauthorized Error
export const Unauthorized: React.FC<{
  message?: string;
  onLogin?: () => void;
}> = ({
  message = 'You do not have permission to access this resource.',
  onLogin
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 rounded-full bg-yellow-500/10 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-yellow-500" />
          </div>
          <CardTitle>Access Denied</CardTitle>
          <CardDescription>{message}</CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <div className="flex justify-center space-x-2">
            {onLogin && (
              <Button onClick={onLogin} variant="default">
                Sign In
              </Button>
            )}
            <Button
              onClick={() => window.location.href = '/'}
              variant="outline"
            >
              <Home className="w-4 h-4 mr-2" />
              Go Home
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Server Error
export const ServerError: React.FC<{
  error?: Error;
  onRetry?: () => void;
}> = ({
  error,
  onRetry
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-destructive" />
          </div>
          <CardTitle>Server Error</CardTitle>
          <CardDescription>
            Something went wrong on our end. Please try again later.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          {error && (
            <div className="p-3 bg-muted rounded text-sm text-left font-mono">
              {error.message}
            </div>
          )}
          <div className="flex justify-center space-x-2">
            {onRetry && (
              <Button onClick={onRetry} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            )}
            <Button
              onClick={() => window.location.href = '/'}
              variant="default"
            >
              <Home className="w-4 h-4 mr-2" />
              Go Home
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Network Error
export const NetworkError: React.FC<{
  onRetry?: () => void;
}> = ({ onRetry }) => {
  return (
    <ErrorComponent
      title="Connection Failed"
      message="Unable to connect to the server. Please check your internet connection and try again."
      onRetry={onRetry}
    />
  );
};

// Inline Error Alert
export const ErrorAlert: React.FC<{
  title?: string;
  message: string;
  onDismiss?: () => void;
  variant?: 'destructive' | 'warning';
}> = ({
  title,
  message,
  onDismiss,
  variant = 'destructive'
}) => {
  const bgColor = variant === 'destructive' ? 'bg-destructive/10' : 'bg-yellow-500/10';
  const textColor = variant === 'destructive' ? 'text-destructive' : 'text-yellow-600';
  const borderColor = variant === 'destructive' ? 'border-destructive/20' : 'border-yellow-500/20';

  return (
    <div className={cn(
      'rounded-lg border p-4 space-y-2',
      bgColor,
      borderColor
    )}>
      <div className="flex items-start space-x-3">
        <AlertTriangle className={cn('w-5 h-5 mt-0.5', textColor)} />
        <div className="flex-1 space-y-1">
          {title && (
            <h5 className={cn('font-medium', textColor)}>{title}</h5>
          )}
          <p className={cn('text-sm', textColor)}>{message}</p>
        </div>
        {onDismiss && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDismiss}
            className={cn('h-8 w-8 p-0', textColor)}
          >
            ×
          </Button>
        )}
      </div>
    </div>
  );
};

export default ErrorComponent;