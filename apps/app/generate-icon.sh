#!/bin/bash

# Script to generate Atlas app icon from SVG
# Uses macOS sips and iconutil (built-in tools)

ICONSET_DIR="icon.iconset"
ICON_1024="assets/icon-1024.png"

echo "Generating Atlas app icon..."

# Create iconset directory
mkdir -p "$ICONSET_DIR"

# Check for macOS sips (built-in)
if command -v sips &> /dev/null && command -v iconutil &> /dev/null; then
    echo "Using macOS sips and iconutil..."
    
    # First create 1024x1024 base icon if it doesn't exist
    if [ ! -f "$ICON_1024" ]; then
        echo "Creating 1024x1024 base icon..."
        python3 << 'PYTHON_SCRIPT'
from PIL import Image, ImageDraw

# Create a 1024x1024 icon with Atlas logo (stacked squares)
img = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw stacked squares pattern (Atlas logo)
square_size = 200
spacing = 80
start_y = (1024 - (square_size * 3 + spacing * 2)) // 2
start_x = (1024 - square_size) // 2

# Top square
draw.rectangle([start_x, start_y, start_x + square_size, start_y + square_size], 
               fill='black', outline='black', width=8)
# Middle square
draw.rectangle([start_x, start_y + square_size + spacing, 
                start_x + square_size, start_y + square_size * 2 + spacing], 
               fill='black', outline='black', width=8)
# Bottom square
draw.rectangle([start_x, start_y + (square_size + spacing) * 2, 
                start_x + square_size, start_y + (square_size + spacing) * 2 + square_size], 
               fill='black', outline='black', width=8)

img.save('assets/icon-1024.png')
print('Created 1024x1024 icon')
PYTHON_SCRIPT
    fi
    
    # Generate all required icon sizes using sips
    echo "Generating icon sizes..."
    sips -z 16 16 "$ICON_1024" --out "$ICONSET_DIR/icon_16x16.png" > /dev/null
    sips -z 32 32 "$ICON_1024" --out "$ICONSET_DIR/icon_16x16@2x.png" > /dev/null
    sips -z 32 32 "$ICON_1024" --out "$ICONSET_DIR/icon_32x32.png" > /dev/null
    sips -z 64 64 "$ICON_1024" --out "$ICONSET_DIR/icon_32x32@2x.png" > /dev/null
    sips -z 128 128 "$ICON_1024" --out "$ICONSET_DIR/icon_128x128.png" > /dev/null
    sips -z 256 256 "$ICON_1024" --out "$ICONSET_DIR/icon_128x128@2x.png" > /dev/null
    sips -z 256 256 "$ICON_1024" --out "$ICONSET_DIR/icon_256x256.png" > /dev/null
    sips -z 512 512 "$ICON_1024" --out "$ICONSET_DIR/icon_256x256@2x.png" > /dev/null
    sips -z 512 512 "$ICON_1024" --out "$ICONSET_DIR/icon_512x512.png" > /dev/null
    sips -z 1024 1024 "$ICON_1024" --out "$ICONSET_DIR/icon_512x512@2x.png" > /dev/null
    
    # Convert to ICNS
    iconutil -c icns "$ICONSET_DIR" -o "assets/icon.icns"
    
    # Also create PNG for Electron
    sips -z 512 512 "$ICON_1024" --out "assets/icon.png" > /dev/null
    
    echo "✅ Icons generated successfully!"
    echo "   - assets/icon.icns (macOS icon)"
    echo "   - assets/icon.png (Electron icon)"
    
    # Cleanup
    rm -rf "$ICONSET_DIR"
    
elif command -v convert &> /dev/null; then
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

