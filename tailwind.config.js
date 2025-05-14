/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
    "./**/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdf4',   /* Very light green */
          100: '#dcfce7',  /* Light green */
          200: '#bbf7d0',  
          300: '#86efac',  
          400: '#4ade80',  
          500: '#22c55e',  /* Main green */
          600: '#16a34a',  
          700: '#15803d',  
          800: '#166534',  
          900: '#14532d',  /* Dark green */
          950: '#052e16',
        },
        secondary: {
          50: '#eff6ff',   /* Very light blue */
          100: '#dbeafe',  /* Light blue */
          200: '#bfdbfe',  
          300: '#93c5fd',  
          400: '#60a5fa',  
          500: '#3b82f6',  /* Main blue */
          600: '#2563eb',  
          700: '#1d4ed8',  
          800: '#1e40af',  
          900: '#1e3a8a',  /* Dark blue */
          950: '#172554',
        },
        accent: {
          50: '#fffbeb',    /* Very light amber */
          100: '#fef3c7',   /* Light amber */
          200: '#fde68a',   
          300: '#fcd34d',   
          400: '#fbbf24',   
          500: '#f59e0b',   /* Main amber */
          600: '#d97706',   
          700: '#b45309',   
          800: '#92400e',   
          900: '#78350f',   /* Dark amber */
          950: '#451a03',
        },
        neutral: {
          50: '#f9fafb',    /* Very light gray */
          100: '#f3f4f6',   /* Light gray */
          200: '#e5e7eb',   
          300: '#d1d5db',   
          400: '#9ca3af',   
          500: '#6b7280',   /* Main gray */
          600: '#4b5563',   
          700: '#374151',   
          800: '#1f2937',   
          900: '#111827',   /* Dark gray */
          950: '#030712',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          950: '#052e16',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
          950: '#451a03',
        },
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
          950: '#450a0a',
        },
      },
      fontFamily: {
        sans: ['Inter var', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['Fira Code', 'Courier New', 'monospace']
      },
      fontSize: {
        'xs': 'var(--viva-text-xs)',
        'sm': 'var(--viva-text-sm)',
        'base': 'var(--viva-text-base)',
        'lg': 'var(--viva-text-lg)',
        'xl': 'var(--viva-text-xl)',
        '2xl': 'var(--viva-text-2xl)',
        '3xl': 'var(--viva-text-3xl)',
        '4xl': 'var(--viva-text-4xl)',
        '5xl': 'var(--viva-text-5xl)',
        '6xl': 'var(--viva-text-6xl)',
      },
      lineHeight: {
        'none': 'var(--viva-leading-none)',
        'tight': 'var(--viva-leading-tight)',
        'snug': 'var(--viva-leading-snug)',
        'normal': 'var(--viva-leading-normal)',
        'relaxed': 'var(--viva-leading-relaxed)',
        'loose': 'var(--viva-leading-loose)',
      },
      zIndex: {
        '0': 'var(--viva-z-0)',
        '10': 'var(--viva-z-10)',
        '20': 'var(--viva-z-20)',
        '30': 'var(--viva-z-30)',
        '40': 'var(--viva-z-40)',
        '50': 'var(--viva-z-50)',
      },
      boxShadow: {
        'sm': 'var(--viva-shadow-sm)',
        'DEFAULT': 'var(--viva-shadow-default)',
        'md': 'var(--viva-shadow-md)',
        'lg': 'var(--viva-shadow-lg)',
        'xl': 'var(--viva-shadow-xl)',
        '2xl': 'var(--viva-shadow-2xl)',
        'inner': 'var(--viva-shadow-inner)',
        'none': 'var(--viva-shadow-none)',
        'card': 'var(--viva-shadow-default)',
      },
      borderRadius: {
        'none': 'var(--viva-radius-none)',
        'sm': 'var(--viva-radius-sm)',
        'DEFAULT': 'var(--viva-radius-default)',
        'md': 'var(--viva-radius-md)',
        'lg': 'var(--viva-radius-lg)',
        'xl': 'var(--viva-radius-xl)',
        '2xl': 'var(--viva-radius-2xl)',
        '3xl': 'var(--viva-radius-3xl)',
        'full': 'var(--viva-radius-full)',
      },
      spacing: {
        'px': 'var(--viva-spacing-px)',
        '0': 'var(--viva-spacing-0)',
        '0.5': 'var(--viva-spacing-0_5)',
        '1': 'var(--viva-spacing-1)',
        '1.5': 'var(--viva-spacing-1_5)',
        '2': 'var(--viva-spacing-2)',
        '2.5': 'var(--viva-spacing-2_5)',
        '3': 'var(--viva-spacing-3)',
        '3.5': 'var(--viva-spacing-3_5)',
        '4': 'var(--viva-spacing-4)',
        '5': 'var(--viva-spacing-5)',
        '6': 'var(--viva-spacing-6)',
        '7': 'var(--viva-spacing-7)',
        '8': 'var(--viva-spacing-8)',
        '9': 'var(--viva-spacing-9)',
        '10': 'var(--viva-spacing-10)',
        '12': 'var(--viva-spacing-12)',
        '14': 'var(--viva-spacing-14)',
        '16': 'var(--viva-spacing-16)',
        '20': 'var(--viva-spacing-20)',
        '24': 'var(--viva-spacing-24)',
        '28': 'var(--viva-spacing-28)',
        '32': 'var(--viva-spacing-32)',
        '36': 'var(--viva-spacing-36)',
        '40': 'var(--viva-spacing-40)',
        '44': 'var(--viva-spacing-44)',
        '48': 'var(--viva-spacing-48)',
        '52': 'var(--viva-spacing-52)',
        '56': 'var(--viva-spacing-56)',
        '60': 'var(--viva-spacing-60)',
        '64': 'var(--viva-spacing-64)',
        '72': 'var(--viva-spacing-72)',
        '80': 'var(--viva-spacing-80)',
        '96': 'var(--viva-spacing-96)',
      },
      minHeight: {
        'content': 'calc(100vh - 4rem)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        vivacrm: {
          "primary": "#22c55e",         // Green
          "primary-content": "#ffffff", // White text on primary buttons
          "secondary": "#3b82f6",       // Blue
          "secondary-content": "#ffffff", // White text on secondary buttons
          "accent": "#f59e0b",          // Amber
          "accent-content": "#ffffff",  // White text on accent buttons
          "neutral": "#374151",         // Gray
          "neutral-content": "#ffffff", // White text on neutral buttons
          "base-100": "#f9fafb",        // Light gray background
          "info": "#3b82f6",            // Blue
          "info-content": "#ffffff",    // White text on info buttons
          "success": "#22c55e",         // Green
          "success-content": "#ffffff", // White text on success buttons
          "warning": "#f59e0b",         // Amber
          "warning-content": "#ffffff", // White text on warning buttons
          "error": "#ef4444",           // Red
          "error-content": "#ffffff",   // White text on error buttons
        },
        vivacrmDark: {
          "primary": "#22c55e",         // Green
          "primary-content": "#ffffff", // White text on primary buttons
          "secondary": "#3b82f6",       // Blue
          "secondary-content": "#ffffff", // White text on secondary buttons
          "accent": "#f59e0b",          // Amber
          "accent-content": "#ffffff",  // White text on accent buttons
          "neutral": "#1f2937",         // Dark gray
          "neutral-content": "#ffffff", // White text on neutral buttons
          "base-100": "#111827",        // Dark background
          "base-200": "#1f2937",        // Darker background
          "base-300": "#374151",        // Darkest background
          "info": "#3b82f6",            // Blue
          "info-content": "#ffffff",    // White text on info buttons
          "success": "#22c55e",         // Green
          "success-content": "#ffffff", // White text on success buttons
          "warning": "#f59e0b",         // Amber
          "warning-content": "#ffffff", // White text on warning buttons
          "error": "#ef4444",           // Red
          "error-content": "#ffffff",   // White text on error buttons
        },
      },
    ],
    // darkTheme: "vivacrmDark",
  },
}