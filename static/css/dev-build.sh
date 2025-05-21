#!/bin/bash
# Development build script for VivaCRM CSS

echo "Starting CSS development build..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Run Tailwind build with watch
echo "Building CSS with Tailwind..."
npx tailwindcss -i ./src/main.css -o ./dist/main.css --watch