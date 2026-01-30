#!/bin/bash

# Build script for Atlas macOS app

echo "Building Atlas macOS app..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build the app
echo "Building Electron app..."
npm run build:mac

# Check if build was successful
if [ -f "dist/Atlas-*.dmg" ]; then
    echo "Build successful! DMG file created in dist/ directory"
    ls -lh dist/*.dmg
else
    echo "Build failed or DMG file not found"
    exit 1
fi

