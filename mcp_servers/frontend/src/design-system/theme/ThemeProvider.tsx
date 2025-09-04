import React, { createContext, useContext, useEffect, useState } from 'react';

/**
 * Theme Provider
 * Manages light/dark mode and custom theme settings
 * 
 * @example
 * <ThemeProvider defaultTheme="light">
 *   <App />
 * </ThemeProvider>
 */

export type Theme = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
  attribute?: string;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'system',
  storageKey = 'ui-theme',
  attribute = 'data-theme',
  enableSystem = true,
  disableTransitionOnChange = false,
}) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Try to get theme from localStorage
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey);
      if (stored === 'light' || stored === 'dark' || stored === 'system') {
        return stored;
      }
    }
    return defaultTheme;
  });

  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>('light');

  // Detect system theme preference
  const getSystemTheme = (): ResolvedTheme => {
    if (typeof window === 'undefined') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };

  // Update resolved theme based on current theme setting
  useEffect(() => {
    const updateResolvedTheme = () => {
      if (theme === 'system' && enableSystem) {
        setResolvedTheme(getSystemTheme());
      } else if (theme === 'light' || theme === 'dark') {
        setResolvedTheme(theme);
      }
    };

    updateResolvedTheme();

    // Listen for system theme changes
    if (theme === 'system' && enableSystem) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => updateResolvedTheme();
      
      // Modern browsers
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
      }
      // Legacy browsers
      else if (mediaQuery.addListener) {
        mediaQuery.addListener(handleChange);
        return () => mediaQuery.removeListener(handleChange);
      }
    }
  }, [theme, enableSystem]);

  // Apply theme to document
  useEffect(() => {
    const root = window.document.documentElement;

    // Disable transitions if requested
    if (disableTransitionOnChange) {
      root.style.transition = 'none';
    }

    // Remove old theme classes/attributes
    root.classList.remove('light', 'dark');
    root.removeAttribute('data-theme');

    // Apply new theme
    if (attribute === 'class') {
      root.classList.add(resolvedTheme);
    } else {
      root.setAttribute(attribute, resolvedTheme);
    }

    // Re-enable transitions
    if (disableTransitionOnChange) {
      const timeout = setTimeout(() => {
        root.style.transition = '';
      }, 0);
      return () => clearTimeout(timeout);
    }
  }, [resolvedTheme, attribute, disableTransitionOnChange]);

  // Save theme preference
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(storageKey, theme);
    }
  }, [theme, storageKey]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const toggleTheme = () => {
    setThemeState((prev) => {
      if (prev === 'light') return 'dark';
      if (prev === 'dark') return 'light';
      // If system, toggle based on resolved theme
      return resolvedTheme === 'light' ? 'dark' : 'light';
    });
  };

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Theme Toggle Component
export const ThemeToggle: React.FC<{ className?: string }> = ({ className }) => {
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={className}
      aria-label={`Switch to ${resolvedTheme === 'light' ? 'dark' : 'light'} mode`}
    >
      {resolvedTheme === 'light' ? (
        // Moon icon for dark mode
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
          />
        </svg>
      ) : (
        // Sun icon for light mode
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
      )}
    </button>
  );
};