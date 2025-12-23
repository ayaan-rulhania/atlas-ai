# Atlas macOS App

Native macOS application for Atlas AI, built with Electron.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the app in development mode:
```bash
npm start
```

## Building

To build the macOS app (.dmg file):

```bash
npm run build:mac
```

The built .dmg file will be in the `dist` directory.

## Configuration

The app will try to connect to a Flask server at `http://localhost:5000` by default. You can override this by setting the `ATLAS_FLASK_URL` environment variable:

```bash
ATLAS_FLASK_URL=http://localhost:5000 npm start
```

If the Flask server is not running, the app will attempt to start it automatically using Python 3.

## Assets

The Atlas logo SVG is in `assets/atlas-logo.svg`. To generate icons:

### Quick Method (Using Script)
```bash
./generate-icon.sh
```

This will create:
- `assets/icon.icns` - App icon for macOS (from Atlas logo)
- `assets/icon.png` - App icon (PNG format, 512x512)

### Manual Method
See `assets/create-icons.md` for detailed instructions on creating icons manually.

### Icon Requirements
- `icon.icns` - App icon for macOS (required)
- `icon.png` - App icon (PNG format, optional, used as fallback)

