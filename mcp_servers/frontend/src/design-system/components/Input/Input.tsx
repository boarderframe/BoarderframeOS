import React, { forwardRef, InputHTMLAttributes, useState } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/cn';

/**
 * Input Component
 * Accessible form input with validation states and icons
 * 
 * @example
 * <Input
 *   label="Email"
 *   type="email"
 *   placeholder="Enter your email"
 *   error="Invalid email address"
 *   required
 * />
 */

const inputVariants = cva(
  'w-full px-3 py-2 text-gray-900 placeholder-gray-500 border rounded-md focus:outline-none focus:ring-2 focus:ring-offset-0 transition-all duration-200 disabled:bg-gray-100 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        default: 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
        error: 'border-red-500 focus:border-red-500 focus:ring-red-500',
        success: 'border-green-500 focus:border-green-500 focus:ring-green-500',
        warning: 'border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500',
      },
      size: {
        sm: 'text-sm py-1.5',
        md: 'text-base py-2',
        lg: 'text-lg py-2.5',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface InputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  label?: string;
  helperText?: string;
  error?: string | boolean;
  success?: string | boolean;
  warning?: string | boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onRightIconClick?: () => void;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant,
      size,
      label,
      helperText,
      error,
      success,
      warning,
      leftIcon,
      rightIcon,
      onRightIconClick,
      required,
      disabled,
      type = 'text',
      id,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false);
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    // Determine variant based on state
    let inputVariant: 'default' | 'error' | 'success' | 'warning' = variant || 'default';
    if (error) inputVariant = 'error';
    else if (success) inputVariant = 'success';
    else if (warning) inputVariant = 'warning';

    // Helper text logic
    const getHelperText = () => {
      if (typeof error === 'string') return error;
      if (typeof success === 'string') return success;
      if (typeof warning === 'string') return warning;
      return helperText;
    };

    const getHelperTextColor = () => {
      if (error) return 'text-red-600';
      if (success) return 'text-green-600';
      if (warning) return 'text-yellow-600';
      return 'text-gray-600';
    };

    const inputType = type === 'password' && showPassword ? 'text' : type;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            type={inputType}
            className={cn(
              inputVariants({ variant: inputVariant, size }),
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              className
            )}
            disabled={disabled}
            required={required}
            aria-invalid={!!error}
            aria-describedby={getHelperText() ? `${inputId}-helper` : undefined}
            {...props}
          />
          {(rightIcon || type === 'password') && (
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
              onClick={
                type === 'password'
                  ? () => setShowPassword(!showPassword)
                  : onRightIconClick
              }
              tabIndex={-1}
              aria-label={type === 'password' ? 'Toggle password visibility' : 'Icon button'}
            >
              {type === 'password' ? (
                showPassword ? (
                  // Eye off icon
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  // Eye icon
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )
              ) : (
                rightIcon
              )}
            </button>
          )}
        </div>
        {getHelperText() && (
          <p
            id={`${inputId}-helper`}
            className={cn('mt-1 text-sm', getHelperTextColor())}
          >
            {getHelperText()}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';