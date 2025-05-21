/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.{html,js}",
    "./static/js/**/*.js",
    "./**/templates/**/*.{html,js}",
    "./static/css/src/**/*.css",
    "./accounts/**/*.{html,js,py}",
    "./core/**/*.{html,js,py}",
    "./customers/**/*.{html,js,py}",
    "./dashboard/**/*.{html,js,py}",
    "./products/**/*.{html,js,py}",
    "./orders/**/*.{html,js,py}",
    "./reports/**/*.{html,js,py}",
    "./invoices/**/*.{html,js,py}",
    "./admin_panel/**/*.{html,js,py}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom VivaCRM brand colors
        'viva-primary': {
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
        'viva-secondary': {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        'viva-accent': {
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
        }
      },
      fontFamily: {
        sans: ['Inter var', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['Fira Code', 'Courier New', 'monospace']
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '104': '26rem',
        '112': '28rem',
      },
      minHeight: {
        'content': 'calc(100vh - 4rem)',
      },
      animation: {
        'slide-in': 'slideIn 0.2s ease-out',
        'slide-out': 'slideOut 0.2s ease-in',
        'fade-in': 'fadeIn 0.2s ease-out',
        'fade-out': 'fadeOut 0.2s ease-in',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideOut: {
          '0%': { transform: 'translateY(0)', opacity: '1' },
          '100%': { transform: 'translateY(-100%)', opacity: '0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms')({
      strategy: 'class',
    }),
    require('@tailwindcss/typography'),
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        vivacrm: {
          "primary": "#22c55e",           // Green
          "primary-content": "#ffffff",   
          "secondary": "#3b82f6",         // Blue
          "secondary-content": "#ffffff", 
          "accent": "#f59e0b",            // Amber
          "accent-content": "#ffffff",    
          "neutral": "#374151",           // Gray
          "neutral-content": "#ffffff",   
          "base-100": "#ffffff",          // White background
          "base-200": "#f9fafb",          // Light gray
          "base-300": "#f3f4f6",          // Lighter gray
          "base-content": "#1f2937",      // Dark text
          "info": "#3b82f6",              
          "info-content": "#ffffff",      
          "success": "#22c55e",           
          "success-content": "#ffffff",   
          "warning": "#f59e0b",           
          "warning-content": "#ffffff",   
          "error": "#ef4444",             
          "error-content": "#ffffff",     
        },
        vivacrmDark: {
          "primary": "#22c55e",           // Green
          "primary-content": "#ffffff",   
          "secondary": "#3b82f6",         // Blue
          "secondary-content": "#ffffff", 
          "accent": "#f59e0b",            // Amber
          "accent-content": "#ffffff",    
          "neutral": "#1f2937",           // Dark gray
          "neutral-content": "#ffffff",   
          "base-100": "#111827",          // Dark background
          "base-200": "#1f2937",          // Darker gray
          "base-300": "#374151",          // Lighter gray
          "base-content": "#f9fafb",      // Light text
          "info": "#3b82f6",              
          "info-content": "#ffffff",      
          "success": "#22c55e",           
          "success-content": "#ffffff",   
          "warning": "#f59e0b",           
          "warning-content": "#ffffff",   
          "error": "#ef4444",             
          "error-content": "#ffffff",     
        },
      },
    ],
    darkTheme: "vivacrmDark",
    base: true,
    styled: true,
    utils: true,
    logs: false,
  },
}