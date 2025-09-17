import React from 'react';
import { cn } from '@/lib/utils';
import { LoadingProps } from '@/types';

const Loading: React.FC<LoadingProps> = ({
  className,
  size = 'md',
  text = 'Loading...',
  children
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className={cn('flex flex-col items-center justify-center space-y-4', className)}>
      <div className={cn('animate-spin rounded-full border-2 border-muted border-t-primary', sizeClasses[size])} />
      {text && (
        <p className="text-sm text-muted-foreground animate-pulse">{text}</p>
      )}
      {children}
    </div>
  );
};

// Spinner component for inline use
export const Spinner: React.FC<{ size?: 'sm' | 'md' | 'lg'; className?: string }> = ({
  size = 'md',
  className
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-2',
  };

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-muted border-t-primary',
        sizeClasses[size],
        className
      )}
    />
  );
};

// Page loading component
export const PageLoading: React.FC<{ message?: string }> = ({ message = 'Loading page...' }) => {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="loading-dots">
          <div></div>
          <div></div>
          <div></div>
          <div></div>
        </div>
        <p className="text-lg text-muted-foreground">{message}</p>
      </div>
    </div>
  );
};

// Button loading state
export const ButtonLoading: React.FC<{ text?: string }> = ({ text = 'Loading' }) => {
  return (
    <div className="flex items-center space-x-2">
      <Spinner size="sm" />
      <span>{text}</span>
    </div>
  );
};

// Table loading component
export const TableLoading: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4
}) => {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex space-x-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <div
              key={colIndex}
              className="h-4 bg-muted rounded animate-pulse flex-1"
              style={{
                animationDelay: `${(rowIndex * columns + colIndex) * 0.1}s`
              }}
            />
          ))}
        </div>
      ))}
    </div>
  );
};

// Skeleton loader component
export const Skeleton: React.FC<{
  className?: string;
  height?: string;
  width?: string;
}> = ({ className, height = 'h-4', width = 'w-full' }) => {
  return (
    <div
      className={cn(
        'bg-muted rounded animate-pulse',
        height,
        width,
        className
      )}
    />
  );
};

// Card skeleton
export const CardSkeleton: React.FC = () => {
  return (
    <div className="rounded-lg border bg-card p-6 space-y-4">
      <div className="space-y-2">
        <Skeleton height="h-6" width="w-3/4" />
        <Skeleton height="h-4" width="w-1/2" />
      </div>
      <div className="space-y-2">
        <Skeleton height="h-4" />
        <Skeleton height="h-4" />
        <Skeleton height="h-4" width="w-5/6" />
      </div>
      <div className="flex space-x-2">
        <Skeleton height="h-8" width="w-20" />
        <Skeleton height="h-8" width="w-16" />
      </div>
    </div>
  );
};

export default Loading;