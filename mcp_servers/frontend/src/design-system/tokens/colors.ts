/**
 * Design System Color Tokens
 * Semantic color system with light/dark mode support
 */

export const colors = {
  // Brand Colors
  brand: {
    primary: {
      50: '#e3f2fd',
      100: '#bbdefb',
      200: '#90caf9',
      300: '#64b5f6',
      400: '#42a5f5',
      500: '#2196f3', // Primary brand color
      600: '#1e88e5',
      700: '#1976d2',
      800: '#1565c0',
      900: '#0d47a1',
    },
    secondary: {
      50: '#f3e5f5',
      100: '#e1bee7',
      200: '#ce93d8',
      300: '#ba68c8',
      400: '#ab47bc',
      500: '#9c27b0',
      600: '#8e24aa',
      700: '#7b1fa2',
      800: '#6a1b9a',
      900: '#4a148c',
    },
    accent: {
      50: '#fff3e0',
      100: '#ffe0b2',
      200: '#ffcc80',
      300: '#ffb74d',
      400: '#ffa726',
      500: '#ff9800',
      600: '#fb8c00',
      700: '#f57c00',
      800: '#ef6c00',
      900: '#e65100',
    },
  },

  // Semantic Colors
  semantic: {
    success: {
      light: '#4caf50',
      main: '#2e7d32',
      dark: '#1b5e20',
      contrast: '#ffffff',
    },
    warning: {
      light: '#ff9800',
      main: '#ed6c02',
      dark: '#e65100',
      contrast: '#ffffff',
    },
    error: {
      light: '#ef5350',
      main: '#d32f2f',
      dark: '#c62828',
      contrast: '#ffffff',
    },
    info: {
      light: '#03a9f4',
      main: '#0288d1',
      dark: '#01579b',
      contrast: '#ffffff',
    },
  },

  // Neutral Colors
  neutral: {
    0: '#ffffff',
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
    1000: '#000000',
  },

  // Surface Colors
  surface: {
    light: {
      background: '#ffffff',
      paper: '#f8f9fa',
      elevated: '#ffffff',
      overlay: 'rgba(0, 0, 0, 0.5)',
    },
    dark: {
      background: '#121212',
      paper: '#1e1e1e',
      elevated: '#242424',
      overlay: 'rgba(255, 255, 255, 0.1)',
    },
  },

  // Text Colors
  text: {
    light: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
      disabled: 'rgba(0, 0, 0, 0.38)',
      hint: 'rgba(0, 0, 0, 0.38)',
    },
    dark: {
      primary: 'rgba(255, 255, 255, 0.87)',
      secondary: 'rgba(255, 255, 255, 0.6)',
      disabled: 'rgba(255, 255, 255, 0.38)',
      hint: 'rgba(255, 255, 255, 0.38)',
    },
  },

  // Action Colors
  action: {
    light: {
      active: 'rgba(0, 0, 0, 0.54)',
      hover: 'rgba(0, 0, 0, 0.04)',
      selected: 'rgba(0, 0, 0, 0.08)',
      disabled: 'rgba(0, 0, 0, 0.26)',
      disabledBackground: 'rgba(0, 0, 0, 0.12)',
    },
    dark: {
      active: 'rgba(255, 255, 255, 0.54)',
      hover: 'rgba(255, 255, 255, 0.08)',
      selected: 'rgba(255, 255, 255, 0.16)',
      disabled: 'rgba(255, 255, 255, 0.3)',
      disabledBackground: 'rgba(255, 255, 255, 0.12)',
    },
  },

  // Special Purpose Colors
  special: {
    divider: {
      light: 'rgba(0, 0, 0, 0.12)',
      dark: 'rgba(255, 255, 255, 0.12)',
    },
    backdrop: {
      light: 'rgba(0, 0, 0, 0.5)',
      dark: 'rgba(0, 0, 0, 0.8)',
    },
    skeleton: {
      light: 'rgba(0, 0, 0, 0.11)',
      dark: 'rgba(255, 255, 255, 0.13)',
    },
  },

  // Kroger Brand Colors
  kroger: {
    blue: '#0063a4',
    lightBlue: '#0095da',
    darkBlue: '#003865',
    orange: '#ff6900',
    green: '#00a862',
    red: '#e31837',
    yellow: '#ffc220',
    gray: '#6b7280',
  },
} as const;

export type ColorTokens = typeof colors;