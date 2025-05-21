/**
 * PurgeCSS Configuration
 * Kullanılmayan CSS'leri temizlemek için
 */

module.exports = {
  content: [
    './templates/**/*.{html,js}',
    './static/js/**/*.js',
    './accounts/templates/**/*.html',
    './customers/templates/**/*.html',
    './dashboard/templates/**/*.html',
    './orders/templates/**/*.html',
    './products/templates/**/*.html',
    './reports/templates/**/*.html',
  ],
  css: ['./static/css/dist/main.css'],
  defaultExtractor: content => {
    // Tailwind CSS class extraction
    const broadMatches = content.match(/[^<>"'`\s]*[^<>"'`\s:]/g) || []
    const innerMatches = content.match(/[^<>"'`\s.()]*[^<>"'`\s.():]/g) || []
    
    return broadMatches.concat(innerMatches)
  },
  safelist: {
    // DaisyUI component classes
    standard: [
      /^btn/,
      /^modal/,
      /^drawer/,
      /^alert/,
      /^badge/,
      /^card/,
      /^navbar/,
      /^menu/,
      /^table/,
      /^form/,
      /^input/,
      /^textarea/,
      /^select/,
      /^checkbox/,
      /^radio/,
      /^toggle/,
      /^range/,
      /^rating/,
      /^tabs/,
      /^avatar/,
      /^dropdown/,
      /^tooltip/,
      /^progress/,
      /^stat/,
      /^steps/,
      /^breadcrumbs/,
      /^pagination/,
      /^indicator/,
      /^divider/,
      /^hero/,
      /^footer/,
    ],
    deep: [
      // Color variations
      /primary/,
      /secondary/,
      /accent/,
      /success/,
      /warning/,
      /error/,
      /info/,
      
      // Size variations
      /xs$/,
      /sm$/,
      /md$/,
      /lg$/,
      /xl$/,
      
      // State variations
      /active$/,
      /disabled$/,
      /loading$/,
      /focus$/,
      /hover$/,
    ],
    greedy: [
      // Dark mode classes
      /dark:/,
      
      // Responsive classes
      /sm:/,
      /md:/,
      /lg:/,
      /xl:/,
      /2xl:/,
    ]
  },
  output: './static/css/dist/main.min.css'
}