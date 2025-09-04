/**
 * Design System Typography Tokens
 * Consistent type scale and font definitions
 */

export const typography = {
  // Font Families
  fontFamily: {
    sans: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(', '),
    serif: ['Georgia', 'Cambria', '"Times New Roman"', 'Times', 'serif'].join(', '),
    mono: [
      'ui-monospace',
      'SFMono-Regular',
      '"SF Mono"',
      'Consolas',
      '"Liberation Mono"',
      'Menlo',
      'monospace',
    ].join(', '),
  },

  // Font Sizes (rem-based for accessibility)
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
    '6xl': '3.75rem', // 60px
    '7xl': '4.5rem',  // 72px
    '8xl': '6rem',    // 96px
    '9xl': '8rem',    // 128px
  },

  // Font Weights
  fontWeight: {
    thin: 100,
    extralight: 200,
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
    black: 900,
  },

  // Line Heights
  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
    body: 1.5,
    heading: 1.2,
  },

  // Letter Spacing
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },

  // Typography Variants
  variants: {
    h1: {
      fontSize: '3rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.025em',
      marginBottom: '1rem',
    },
    h2: {
      fontSize: '2.25rem',
      fontWeight: 600,
      lineHeight: 1.25,
      letterSpacing: '-0.025em',
      marginBottom: '0.875rem',
    },
    h3: {
      fontSize: '1.875rem',
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.02em',
      marginBottom: '0.75rem',
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.35,
      letterSpacing: '-0.01em',
      marginBottom: '0.625rem',
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '0em',
      marginBottom: '0.5rem',
    },
    h6: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '0em',
      marginBottom: '0.5rem',
    },
    subtitle1: {
      fontSize: '1.125rem',
      fontWeight: 500,
      lineHeight: 1.5,
      letterSpacing: '0em',
    },
    subtitle2: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
      letterSpacing: '0.01em',
    },
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0em',
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0.01em',
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 600,
      lineHeight: 1.75,
      letterSpacing: '0.05em',
      textTransform: 'uppercase' as const,
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0.03em',
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      lineHeight: 2,
      letterSpacing: '0.1em',
      textTransform: 'uppercase' as const,
    },
    code: {
      fontFamily: 'monospace',
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.5,
    },
  },

  // Text Decoration
  textDecoration: {
    none: 'none',
    underline: 'underline',
    overline: 'overline',
    lineThrough: 'line-through',
  },

  // Text Transform
  textTransform: {
    none: 'none',
    uppercase: 'uppercase',
    lowercase: 'lowercase',
    capitalize: 'capitalize',
  },
} as const;

export type TypographyTokens = typeof typography;