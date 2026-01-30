# Assets Directory

Place the following assets here:

1. **icon.icns** - macOS app icon (ICNS format)
   - Can be created from PNG using: `iconutil -c icns icon.iconset`
   - Or use online tools to convert PNG to ICNS

2. **icon.png** - App icon in PNG format (512x512 or 1024x1024 recommended)

3. **dmg-icon.icns** - DMG volume icon (ICNS format)

4. **dmg-background.png** - DMG background image (540x380 pixels recommended)

## Creating Icons

You can create icons from the Atlas logo SVG:
1. Export the logo as PNG at 1024x1024
2. Use `iconutil` or online tools to convert to ICNS format
3. Place files in this directory

## Temporary Solution

For now, the app will work without custom icons (Electron will use default icons).
You can build and test the app, then add custom icons later.

