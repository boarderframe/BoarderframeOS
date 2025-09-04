/**
 * Design System Animation Tokens
 * Consistent animation and transition definitions
 */

export const animation = {
  // Duration values
  duration: {
    instant: '0ms',
    fast: '150ms',
    normal: '250ms',
    slow: '350ms',
    slower: '500ms',
    slowest: '1000ms',
  },

  // Easing functions
  easing: {
    linear: 'linear',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
    smooth: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    elastic: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  },

  // Transition presets
  transition: {
    all: {
      property: 'all',
      duration: '250ms',
      easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
    colors: {
      property: 'background-color, border-color, color, fill, stroke',
      duration: '150ms',
      easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
    opacity: {
      property: 'opacity',
      duration: '150ms',
      easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
    shadow: {
      property: 'box-shadow',
      duration: '150ms',
      easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
    transform: {
      property: 'transform',
      duration: '150ms',
      easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
  },

  // Keyframe animations
  keyframes: {
    fadeIn: {
      from: { opacity: 0 },
      to: { opacity: 1 },
    },
    fadeOut: {
      from: { opacity: 1 },
      to: { opacity: 0 },
    },
    slideInUp: {
      from: { transform: 'translateY(100%)', opacity: 0 },
      to: { transform: 'translateY(0)', opacity: 1 },
    },
    slideInDown: {
      from: { transform: 'translateY(-100%)', opacity: 0 },
      to: { transform: 'translateY(0)', opacity: 1 },
    },
    slideInLeft: {
      from: { transform: 'translateX(-100%)', opacity: 0 },
      to: { transform: 'translateX(0)', opacity: 1 },
    },
    slideInRight: {
      from: { transform: 'translateX(100%)', opacity: 0 },
      to: { transform: 'translateX(0)', opacity: 1 },
    },
    scaleIn: {
      from: { transform: 'scale(0.9)', opacity: 0 },
      to: { transform: 'scale(1)', opacity: 1 },
    },
    scaleOut: {
      from: { transform: 'scale(1)', opacity: 1 },
      to: { transform: 'scale(0.9)', opacity: 0 },
    },
    spin: {
      from: { transform: 'rotate(0deg)' },
      to: { transform: 'rotate(360deg)' },
    },
    pulse: {
      '0%, 100%': { opacity: 1 },
      '50%': { opacity: 0.5 },
    },
    bounce: {
      '0%, 100%': { transform: 'translateY(0)' },
      '50%': { transform: 'translateY(-25%)' },
    },
    shake: {
      '0%, 100%': { transform: 'translateX(0)' },
      '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-10px)' },
      '20%, 40%, 60%, 80%': { transform: 'translateX(10px)' },
    },
    skeleton: {
      '0%': { backgroundPosition: '-200% 0' },
      '100%': { backgroundPosition: '200% 0' },
    },
  },

  // Animation classes
  classes: {
    fadeIn: 'animate-fade-in',
    fadeOut: 'animate-fade-out',
    slideIn: 'animate-slide-in',
    scaleIn: 'animate-scale-in',
    spin: 'animate-spin',
    pulse: 'animate-pulse',
    bounce: 'animate-bounce',
    skeleton: 'animate-skeleton',
  },
} as const;

export type AnimationTokens = typeof animation;