# Creating Atlas App Icons

The Atlas logo (stacked squares) needs to be converted to icon formats for macOS.

## Quick Method (Using Online Tools)

1. **Create PNG from SVG:**
   - Use an online SVG to PNG converter (like https://convertio.co/svg-png/)
   - Upload `atlas-logo.svg`
   - Export at 512x512 and 1024x1024 sizes
   - Save as `icon.png` (1024x1024) and `icon-512.png` (512x512)

2. **Create ICNS from PNG:**
   - Use https://cloudconvert.com/png-to-icns or similar
   - Upload the 1024x1024 PNG
   - Download as `icon.icns`

## macOS Method (Using iconutil)

If you have macOS, you can use the built-in `iconutil`:

1. **Create iconset directory:**
   ```bash
   mkdir -p icon.iconset
   ```

2. **Convert SVG to PNG at different sizes:**
   ```bash
   # You'll need to use a tool like Inkscape or ImageMagick
   # For ImageMagick: convert atlas-logo.svg -resize 512x512 icon.iconset/icon_512x512.png
   ```

3. **Create all required sizes:**
   - icon_16x16.png
   - icon_16x16@2x.png (32x32)
   - icon_32x32.png
   - icon_32x32@2x.png (64x64)
   - icon_128x128.png
   - icon_128x128@2x.png (256x256)
   - icon_256x256.png
   - icon_256x256@2x.png (512x512)
   - icon_512x512.png
   - icon_512x512@2x.png (1024x1024)

4. **Convert to ICNS:**
   ```bash
   iconutil -c icns icon.iconset
   ```

## Temporary Solution

For now, Electron will use a default icon. The app will work fine, and you can add custom icons later.

