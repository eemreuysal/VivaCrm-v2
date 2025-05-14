const fs = require('fs');
const svg2img = require('svg2img');

// Read the SVG file
const svgContent = fs.readFileSync('./logo.svg', 'utf8');

// Convert SVG to PNG
svg2img(svgContent, {
  width: 200,
  height: 60,
  preserveAspectRatio: true
}, (error, buffer) => {
  if (error) {
    console.error('Error converting SVG to PNG:', error);
    return;
  }

  // Save PNG file
  fs.writeFileSync('./logo.png', buffer);
  console.log('PNG file created successfully');

  // Convert to base64
  const base64String = buffer.toString('base64');
  console.log('\nBase64 encoded PNG:');
  console.log(base64String);
});