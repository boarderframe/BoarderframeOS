/**
 * MCP-UI Design System
 * Comprehensive component library for MCP server interfaces
 */

// Design Tokens
export * from './tokens';

// Theme System
export { ThemeProvider, useTheme, ThemeToggle } from './theme/ThemeProvider';
export type { Theme, ResolvedTheme, ThemeProviderProps } from './theme/ThemeProvider';

// Utility Functions
export { cn } from './utils/cn';
export { mcpBridge, useMCPBridge, MCPMessages } from './utils/postMessageBridge';
export type { MCPMessage, MCPResponse } from './utils/postMessageBridge';

// Core Components
export { Button } from './components/Button/Button';
export type { ButtonProps } from './components/Button/Button';

export { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
} from './components/Card/Card';
export type { 
  CardProps, 
  CardHeaderProps, 
  CardTitleProps, 
  CardDescriptionProps, 
  CardContentProps, 
  CardFooterProps 
} from './components/Card/Card';

export { Input } from './components/Input/Input';
export type { InputProps } from './components/Input/Input';

export { Modal, ModalFooter } from './components/Modal/Modal';
export type { ModalProps, ModalFooterProps } from './components/Modal/Modal';

export { Badge } from './components/Badge/Badge';
export type { BadgeProps } from './components/Badge/Badge';

export { toast, ToastContainer, useToast } from './components/Toast/Toast';
export type { ToastProps } from './components/Toast/Toast';

// E-commerce Components
export { ProductCard } from './components/ProductCard/ProductCard';
export type { ProductCardProps, Product } from './components/ProductCard/ProductCard';

// Kroger Specific Components
export { ShoppingCart } from './components/KrogerCart/ShoppingCart';
export type { ShoppingCartProps, CartItem } from './components/KrogerCart/ShoppingCart';

// Component Variants
export const variants = {
  button: ['primary', 'secondary', 'success', 'danger', 'warning', 'ghost', 'link', 'outline'],
  badge: ['default', 'primary', 'secondary', 'success', 'warning', 'error', 'info', 'outline'],
  card: ['default', 'elevated', 'outlined', 'ghost'],
  input: ['default', 'error', 'success', 'warning'],
  modal: ['sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl', 'full'],
} as const;

// Size Scales
export const sizes = {
  button: ['xs', 'sm', 'md', 'lg', 'xl'],
  badge: ['xs', 'sm', 'md', 'lg'],
  input: ['sm', 'md', 'lg'],
  modal: ['sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl', 'full'],
  spacing: ['xs', 'sm', 'md', 'lg', 'xl', '2xl', '3xl'],
} as const;

// Accessibility Helpers
export const a11y = {
  srOnly: 'absolute w-px h-px p-0 -m-px overflow-hidden whitespace-nowrap border-0',
  focusRing: 'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
  disabled: 'disabled:opacity-50 disabled:cursor-not-allowed',
} as const;

// Animation Classes
export const animations = {
  fadeIn: 'animate-fade-in',
  fadeOut: 'animate-fade-out',
  slideIn: 'animate-slide-in',
  slideOut: 'animate-slide-out',
  scaleIn: 'animate-scale-in',
  scaleOut: 'animate-scale-out',
  spin: 'animate-spin',
  pulse: 'animate-pulse',
  bounce: 'animate-bounce',
  skeleton: 'animate-skeleton',
} as const;