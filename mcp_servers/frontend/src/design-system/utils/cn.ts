import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function to merge Tailwind CSS classes
 * Combines clsx for conditional classes and tailwind-merge for proper override handling
 * 
 * @example
 * cn('text-red-500', condition && 'text-blue-500', 'p-4')
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}