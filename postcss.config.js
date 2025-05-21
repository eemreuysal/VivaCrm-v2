/**
 * PostCSS Configuration
 * Handles CSS processing for VivaCRM
 */

module.exports = {
  plugins: {
    // Import handling
    'postcss-import': {},
    
    // Tailwind CSS
    'tailwindcss': {},
    
    // Auto-prefixer for browser compatibility
    'autoprefixer': {},
    
    // CSS Nesting (for better organization)
    'postcss-nesting': {},
    
    // Custom Properties (CSS Variables) optimization
    'postcss-custom-properties': {
      preserve: true
    },
    
    // Production optimizations
    ...process.env.NODE_ENV === 'production' ? {
      // Minification
      'cssnano': {
        preset: ['default', {
          discardComments: {
            removeAll: true,
          },
          reduceIdents: false,
        }]
      },
      
      // Remove unused CSS
      '@fullhuman/postcss-purgecss': {
        content: [
          './templates/**/*.html',
          './static/js/**/*.js',
          './**/templates/**/*.html',
        ],
        defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || [],
        safelist: {
          standard: [
            /^(modal|dropdown|collapse|alert)/,
            /data-theme$/,
            /^hljs/
          ],
          deep: [
            /^menu/,
            /^navbar/,
            /^dashboard/
          ]
        }
      }
    } : {}
  }
};