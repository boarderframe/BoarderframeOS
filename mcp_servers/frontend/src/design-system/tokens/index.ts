/**
 * Design System Tokens
 * Central export for all design tokens
 */

export { colors } from './colors';
export { typography } from './typography';
export { spacing } from './spacing';
export { animation } from './animation';
export { shadows } from './shadows';

export type { ColorTokens } from './colors';
export type { TypographyTokens } from './typography';
export type { SpacingTokens } from './spacing';
export type { AnimationTokens } from './animation';
export type { ShadowTokens } from './shadows';

// Breakpoints for responsive design
export const breakpoints = {
  xs: '0px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

// Z-index scale
export const zIndex = {
  hide: -1,
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  fixed: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  tooltip: 1600,
  toast: 1700,
  max: 9999,
} as const;

// Border radius
export const borderRadius = {
  none: '0px',
  sm: '2px',
  md: '4px',
  lg: '8px',
  xl: '12px',
  '2xl': '16px',
  '3xl': '24px',
  full: '9999px',
} as const;

// Border width
export const borderWidth = {
  0: '0px',
  1: '1px',
  2: '2px',
  4: '4px',
  8: '8px',
} as const;

export type BreakpointTokens = typeof breakpoints;
export type ZIndexTokens = typeof zIndex;
export type BorderRadiusTokens = typeof borderRadius;
export type BorderWidthTokens = typeof borderWidth;