import React, { forwardRef, HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/cn';

/**
 * Badge Component
 * Small label for displaying status, counts, or categories
 * 
 * @example
 * <Badge variant="success">Active</Badge>
 * <Badge variant="warning" size="lg">Pending</Badge>
 * <Badge variant="error" removable onRemove={handleRemove}>Error</Badge>
 */

const badgeVariants = cva(
  'inline-flex items-center font-medium rounded-full transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-gray-100 text-gray-800 hover:bg-gray-200',
        primary: 'bg-blue-100 text-blue-800 hover:bg-blue-200',
        secondary: 'bg-purple-100 text-purple-800 hover:bg-purple-200',
        success: 'bg-green-100 text-green-800 hover:bg-green-200',
        warning: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200',
        error: 'bg-red-100 text-red-800 hover:bg-red-200',
        danger: 'bg-red-100 text-red-800 hover:bg-red-200',
        info: 'bg-blue-100 text-blue-800 hover:bg-blue-200',
        outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50',
      },
      size: {
        xs: 'text-xs px-1.5 py-0.5',
        sm: 'text-xs px-2 py-0.5',
        md: 'text-sm px-2.5 py-0.5',
        lg: 'text-base px-3 py-1',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  children: React.ReactNode;
  icon?: React.ReactNode;
  removable?: boolean;
  onRemove?: () => void;
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, size, children, icon, removable, onRemove, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(badgeVariants({ variant, size }), className)}
        {...props}
      >
        {icon && <span className="mr-1">{icon}</span>}
        {children}
        {removable && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onRemove?.();
            }}
            className="ml-1 -mr-0.5 hover:text-gray-900 focus:outline-none"
            aria-label="Remove badge"
          >
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </span>
    );
  }
);

Badge.displayName = 'Badge';