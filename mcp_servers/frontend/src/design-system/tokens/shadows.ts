/**
 * Design System Shadow Tokens
 * Elevation and depth visual effects
 */

export const shadows = {
  // Elevation levels (Material Design inspired)
  elevation: {
    0: 'none',
    1: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    2: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    3: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    4: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    5: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  },

  // Component shadows
  component: {
    card: {
      default: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      hover: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      active: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
    button: {
      default: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      hover: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      active: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
      focus: '0 0 0 3px rgba(33, 150, 243, 0.25)',
    },
    input: {
      default: 'inset 0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      focus: '0 0 0 3px rgba(33, 150, 243, 0.25)',
      error: '0 0 0 3px rgba(239, 68, 68, 0.25)',
    },
    modal: {
      default: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
      backdrop: 'rgba(0, 0, 0, 0.5)',
    },
    dropdown: {
      default: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    },
    tooltip: {
      default: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },

  // Inset shadows
  inset: {
    sm: 'inset 0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
    lg: 'inset 0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  },

  // Colored shadows
  colored: {
    primary: '0 4px 14px 0 rgba(33, 150, 243, 0.35)',
    secondary: '0 4px 14px 0 rgba(156, 39, 176, 0.35)',
    success: '0 4px 14px 0 rgba(76, 175, 80, 0.35)',
    warning: '0 4px 14px 0 rgba(255, 152, 0, 0.35)',
    error: '0 4px 14px 0 rgba(239, 68, 68, 0.35)',
  },

  // Glow effects
  glow: {
    sm: '0 0 10px rgba(33, 150, 243, 0.5)',
    md: '0 0 20px rgba(33, 150, 243, 0.5)',
    lg: '0 0 30px rgba(33, 150, 243, 0.5)',
  },

  // Dark mode shadows
  dark: {
    elevation: {
      0: 'none',
      1: '0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2)',
      2: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
      3: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)',
      4: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.14)',
      5: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    },
  },
} as const;

export type ShadowTokens = typeof shadows;