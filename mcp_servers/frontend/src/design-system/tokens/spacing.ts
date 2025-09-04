/**
 * Design System Spacing Tokens
 * Consistent spacing scale for layout and components
 */

export const spacing = {
  // Base spacing unit (4px)
  base: 4,

  // Spacing Scale (based on 4px grid)
  scale: {
    0: '0px',
    px: '1px',
    0.5: '2px',
    1: '4px',
    1.5: '6px',
    2: '8px',
    2.5: '10px',
    3: '12px',
    3.5: '14px',
    4: '16px',
    5: '20px',
    6: '24px',
    7: '28px',
    8: '32px',
    9: '36px',
    10: '40px',
    11: '44px',
    12: '48px',
    14: '56px',
    16: '64px',
    20: '80px',
    24: '96px',
    28: '112px',
    32: '128px',
    36: '144px',
    40: '160px',
    44: '176px',
    48: '192px',
    52: '208px',
    56: '224px',
    60: '240px',
    64: '256px',
    72: '288px',
    80: '320px',
    96: '384px',
  },

  // Component-specific spacing
  component: {
    button: {
      paddingX: '16px',
      paddingY: '8px',
      gap: '8px',
    },
    card: {
      padding: '16px',
      gap: '12px',
    },
    input: {
      paddingX: '12px',
      paddingY: '8px',
    },
    modal: {
      padding: '24px',
      gap: '16px',
    },
    section: {
      padding: '32px',
      gap: '24px',
    },
  },

  // Layout spacing
  layout: {
    containerPadding: '16px',
    sectionSpacing: '48px',
    gridGap: '16px',
    stackGap: '8px',
  },

  // Margin presets
  margin: {
    none: '0',
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
    auto: 'auto',
  },

  // Padding presets
  padding: {
    none: '0',
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
  },

  // Gap presets (for flexbox/grid)
  gap: {
    none: '0',
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
  },
} as const;

export type SpacingTokens = typeof spacing;