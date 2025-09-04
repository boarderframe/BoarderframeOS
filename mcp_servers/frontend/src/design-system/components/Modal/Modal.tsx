import React, { useEffect, useRef, forwardRef } from 'react';
import { createPortal } from 'react-dom';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/cn';
import { Button } from '../Button/Button';

/**
 * Modal Component
 * Accessible modal dialog with focus management and animations
 * 
 * @example
 * <Modal
 *   isOpen={isOpen}
 *   onClose={handleClose}
 *   title="Confirm Action"
 *   size="md"
 * >
 *   <p>Are you sure you want to continue?</p>
 *   <ModalFooter>
 *     <Button variant="ghost" onClick={handleClose}>Cancel</Button>
 *     <Button onClick={handleConfirm}>Confirm</Button>
 *   </ModalFooter>
 * </Modal>
 */

const modalVariants = cva(
  'relative bg-white rounded-lg shadow-xl transform transition-all',
  {
    variants: {
      size: {
        sm: 'max-w-sm w-full',
        md: 'max-w-md w-full',
        lg: 'max-w-lg w-full',
        xl: 'max-w-xl w-full',
        '2xl': 'max-w-2xl w-full',
        '3xl': 'max-w-3xl w-full',
        '4xl': 'max-w-4xl w-full',
        full: 'max-w-[90vw] w-full',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
);

export interface ModalProps extends VariantProps<typeof modalVariants> {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
  className?: string;
  preventScroll?: boolean;
}

export const Modal = forwardRef<HTMLDivElement, ModalProps>(
  (
    {
      isOpen,
      onClose,
      title,
      description,
      children,
      size,
      closeOnOverlayClick = true,
      closeOnEscape = true,
      showCloseButton = true,
      className,
      preventScroll = true,
    },
    ref
  ) => {
    const modalRef = useRef<HTMLDivElement>(null);
    const previousActiveElement = useRef<Element | null>(null);

    // Handle escape key
    useEffect(() => {
      if (!isOpen || !closeOnEscape) return;

      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose();
        }
      };

      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose, closeOnEscape]);

    // Focus management
    useEffect(() => {
      if (isOpen) {
        previousActiveElement.current = document.activeElement;
        modalRef.current?.focus();
      } else {
        (previousActiveElement.current as HTMLElement)?.focus();
      }
    }, [isOpen]);

    // Prevent body scroll when modal is open
    useEffect(() => {
      if (!preventScroll) return;

      if (isOpen) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }

      return () => {
        document.body.style.overflow = '';
      };
    }, [isOpen, preventScroll]);

    if (!isOpen) return null;

    const handleOverlayClick = (e: React.MouseEvent) => {
      if (closeOnOverlayClick && e.target === e.currentTarget) {
        onClose();
      }
    };

    return createPortal(
      <div
        className="fixed inset-0 z-50 overflow-y-auto"
        aria-labelledby="modal-title"
        aria-describedby="modal-description"
        role="dialog"
        aria-modal="true"
      >
        {/* Overlay */}
        <div
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity animate-fade-in"
          onClick={handleOverlayClick}
          aria-hidden="true"
        />

        {/* Modal Container */}
        <div className="flex min-h-full items-center justify-center p-4">
          <div
            ref={modalRef}
            tabIndex={-1}
            className={cn(
              modalVariants({ size }),
              'animate-scale-in',
              className
            )}
          >
            {/* Header */}
            {(title || showCloseButton) && (
              <div className="flex items-start justify-between p-4 border-b border-gray-200">
                <div>
                  {title && (
                    <h2
                      id="modal-title"
                      className="text-lg font-semibold text-gray-900"
                    >
                      {title}
                    </h2>
                  )}
                  {description && (
                    <p
                      id="modal-description"
                      className="mt-1 text-sm text-gray-600"
                    >
                      {description}
                    </p>
                  )}
                </div>
                {showCloseButton && (
                  <button
                    type="button"
                    className="ml-auto -mr-2 -mt-2 p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    onClick={onClose}
                    aria-label="Close modal"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                )}
              </div>
            )}

            {/* Content */}
            <div className="p-4">{children}</div>
          </div>
        </div>
      </div>,
      document.body
    );
  }
);

Modal.displayName = 'Modal';

// Modal Footer Component
export interface ModalFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const ModalFooter: React.FC<ModalFooterProps> = ({ children, className }) => {
  return (
    <div
      className={cn(
        'flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-200',
        className
      )}
    >
      {children}
    </div>
  );
};