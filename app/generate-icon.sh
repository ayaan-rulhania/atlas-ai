#!/bin/bash

# Script to generate Atlas app icon from SVG
# Requires: ImageMagick or Inkscape

SVG_FILE="assets/atlas-logo.svg"
ICONSET_DIR="icon.iconset"

echo "Generating Atlas app icon..."

# Create iconset directory
mkdir -p "$ICONSET_DIR"

# Check for ImageMagick
if command -v convert &> /dev/null; then
    echo "Using ImageMagick..."
    
    # Generate all required icon sizes
    convert -background none "$SVG_FILE" -resize 16x16 "$ICONSET_DIR/icon_16x16.png"
    convert -background none "$SVG_FILE" -resize 32x32 "$ICONSET_DIR/icon_16x16@2x.png"
    convert -background none "$SVG_FILE" -resize 32x32 "$ICONSET_DIR/icon_32x32.png"
    convert -background none "$SVG_FILE" -resize 64x64 "$ICONSET_DIR/icon_32x32@2x.png"
    convert -background none "$SVG_FILE" -resize 128x128 "$ICONSET_DIR/icon_128x128.png"
    convert -background none "$SVG_FILE" -resize 256x256 "$ICONSET_DIR/icon_128x128@2x.png"
    convert -background none "$SVG_FILE" -resize 256x256 "$ICONSET_DIR/icon_256x256.png"
    convert -background none "$SVG_FILE" -resize 512x512 "$ICONSET_DIR/icon_256x256@2x.png"
    convert -background none "$SVG_FILE" -resize 512x512 "$ICONSET_DIR/icon_512x512.png"
    convert -background none "$SVG_FILE" -resize 1024x1024 "$ICONSET_DIR/icon_512x512@2x.png"
    
    # Convert to ICNS
    iconutil -c icns "$ICONSET_DIR" -o "assets/icon.icns"
    
    # Also create PNG for Electron
    convert -background none "$SVG_FILE" -resize 512x512 "assets/icon.png"
    
    echo "✅ Icons generated successfully!"
    echo "   - assets/icon.icns (macOS icon)"
    echo "   - assets/icon.png (Electron icon)"
    
    # Cleanup
    rm -rf "$ICONSET_DIR"
    
elif command -v inkscape &> /dev/null; then
    echo "Using Inkscape..."
    # Similar commands using inkscape
    echo "Inkscape support coming soon..."
else
    echo "❌ Error: Neither ImageMagick nor Inkscape found."
    echo "   Install ImageMagick: brew install imagemagick"
    echo "   Or use online tools (see create-icons.md)"
fi

