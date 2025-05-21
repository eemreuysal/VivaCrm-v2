/**
 * VivaCRM CSS Build Script
 * Modern CSS pipeline with PostCSS
 */

const fs = require('fs');
const path = require('path');
const postcss = require('postcss');
const tailwindcss = require('tailwindcss');
const autoprefixer = require('autoprefixer');
const cssnano = require('cssnano');
const atImport = require('postcss-import');

// Configuration
const config = {
    input: './src/main.css',
    output: './dist/main.css',
    outputMin: './dist/main.min.css',
    tailwindConfig: '../../tailwind.config.js' // Adjust path if needed
};

// Build function
async function build() {
    try {
        // Read input file
        const css = fs.readFileSync(path.resolve(__dirname, config.input), 'utf8');
        
        // Process CSS with PostCSS
        const result = await postcss([
            atImport(),
            require('postcss-nested'),
            tailwindcss(config.tailwindConfig),
            autoprefixer(),
        ]).process(css, { 
            from: config.input,
            to: config.output 
        });
        
        // Create dist directory if it doesn't exist
        const distDir = path.dirname(path.resolve(__dirname, config.output));
        if (!fs.existsSync(distDir)) {
            fs.mkdirSync(distDir, { recursive: true });
        }
        
        // Write unminified version
        fs.writeFileSync(
            path.resolve(__dirname, config.output), 
            result.css
        );
        
        // Create minified version
        const minified = await postcss([
            cssnano({
                preset: ['default', {
                    discardComments: { removeAll: true },
                    colormin: false
                }]
            })
        ]).process(result.css, { 
            from: config.output,
            to: config.outputMin 
        });
        
        // Write minified version
        fs.writeFileSync(
            path.resolve(__dirname, config.outputMin), 
            minified.css
        );
        
        console.log('CSS build completed successfully!');
        console.log(`Output: ${config.output}`);
        console.log(`Minified: ${config.outputMin}`);
        
    } catch (error) {
        console.error('Build failed:', error);
        process.exit(1);
    }
}

// Run build
build();