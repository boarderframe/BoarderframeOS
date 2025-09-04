import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/cn';

/**
 * Toast Component & System
 * Non-intrusive notifications with auto-dismiss
 * 
 * @example
 * import { toast } from './Toast';
 * 
 * toast.success('Operation completed successfully!');
 * toast.error('Something went wrong');
 * toast.info('New update available', { duration: 5000 });
 */

const toastVariants = cva(
  'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg pointer-events-auto transition-all duration-300',
  {
    variants: {
      variant: {
        default: 'bg-white text-gray-900 border border-gray-200',
        success: 'bg-green-50 text-green-900 border border-green-200',
        error: 'bg-red-50 text-red-900 border border-red-200',
        warning: 'bg-yellow-50 text-yellow-900 border border-yellow-200',
        info: 'bg-blue-50 text-blue-900 border border-blue-200',
      },
      position: {
        'top-left': 'top-4 left-4',
        'top-center': 'top-4 left-1/2 -translate-x-1/2',
        'top-right': 'top-4 right-4',
        'bottom-left': 'bottom-4 left-4',
        'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
        'bottom-right': 'bottom-4 right-4',
      },
    },
    defaultVariants: {
      variant: 'default',
      position: 'top-right',
    },
  }
);

export interface ToastProps extends VariantProps<typeof toastVariants> {
  id: string;
  message: string;
  description?: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
  duration?: number;
  onClose: (id: string) => void;
  className?: string;
}

const Toast: React.FC<ToastProps> = ({
  id,
  message,
  description,
  variant,
  icon,
  action,
  duration = 4000,
  onClose,
  className,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);
      
      return () => clearTimeout(timer);
    }
  }, [duration]);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      onClose(id);
    }, 300);
  };

  const getIcon = () => {
    if (icon) return icon;

    switch (variant) {
      case 'success':
        return (
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      case 'info':
        return (
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div
      className={cn(
        toastVariants({ variant }),
        isVisible && !isExiting ? 'animate-slide-in' : '',
        isExiting ? 'animate-slide-out opacity-0' : '',
        className
      )}
      role="alert"
      aria-live="polite"
    >
      {getIcon()}
      <div className="flex-1">
        <p className="font-medium">{message}</p>
        {description && (
          <p className="mt-1 text-sm opacity-90">{description}</p>
        )}
      </div>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="font-medium text-sm hover:underline"
        >
          {action.label}
        </button>
      )}
      <button
        type="button"
        onClick={handleClose}
        className="ml-2 text-gray-400 hover:text-gray-600"
        aria-label="Close notification"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    </div>
  );
};

// Toast Container Component
interface ToastContainerProps {
  toasts: ToastProps[];
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, position = 'top-right' }) => {
  if (toasts.length === 0) return null;

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-center': 'top-4 left-1/2 -translate-x-1/2',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
    'bottom-right': 'bottom-4 right-4',
  };

  return createPortal(
    <div
      className={cn(
        'fixed z-50 pointer-events-none',
        positionClasses[position]
      )}
    >
      <div className="flex flex-col gap-2">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} />
        ))}
      </div>
    </div>,
    document.body
  );
};

// Toast Manager Singleton
class ToastManager {
  private listeners: Set<(toasts: ToastProps[]) => void> = new Set();
  private toasts: ToastProps[] = [];

  subscribe(listener: (toasts: ToastProps[]) => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.listeners.forEach((listener) => listener([...this.toasts]));
  }

  private show(options: Omit<ToastProps, 'id' | 'onClose'>) {
    const id = Math.random().toString(36).substr(2, 9);
    const toast: ToastProps = {
      ...options,
      id,
      onClose: (id: string) => this.remove(id),
    };
    
    this.toasts = [...this.toasts, toast];
    this.notify();
    return id;
  }

  remove(id: string) {
    this.toasts = this.toasts.filter((t) => t.id !== id);
    this.notify();
  }

  success(message: string, options?: Partial<ToastProps>) {
    return this.show({ ...options, message, variant: 'success' });
  }

  error(message: string, options?: Partial<ToastProps>) {
    return this.show({ ...options, message, variant: 'error' });
  }

  warning(message: string, options?: Partial<ToastProps>) {
    return this.show({ ...options, message, variant: 'warning' });
  }

  info(message: string, options?: Partial<ToastProps>) {
    return this.show({ ...options, message, variant: 'info' });
  }

  default(message: string, options?: Partial<ToastProps>) {
    return this.show({ ...options, message, variant: 'default' });
  }

  clear() {
    this.toasts = [];
    this.notify();
  }
}

export const toast = new ToastManager();

// React Hook for Toast
export const useToast = () => {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  useEffect(() => {
    return toast.subscribe(setToasts);
  }, []);

  return { toasts, toast };
};