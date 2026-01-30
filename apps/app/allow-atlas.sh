#!/bin/bash

# Script to allow Atlas macOS app to run by removing quarantine attribute

APP_PATH="/Applications/Atlas.app"

if [ ! -d "$APP_PATH" ]; then
    echo "Atlas app not found at $APP_PATH"
    echo ""
    echo "Please make sure you have:"
    echo "1. Opened the DMG file"
    echo "2. Dragged Atlas.app to your Applications folder"
    echo ""
    read -p "Press Enter to continue..."
    exit 1
fi

echo "Removing quarantine attribute from Atlas.app..."
xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Success! Atlas should now be able to run."
    echo ""
    echo "You can now:"
    echo "1. Open Atlas from your Applications folder"
    echo "2. Or double-click it - it should launch without the security warning"
else
    echo "⚠️  Could not remove quarantine attribute (it may already be removed)"
    echo ""
    echo "Try this instead:"
    echo "1. Right-click on Atlas.app in Applications"
    echo "2. Select 'Open'"
    echo "3. Click 'Open' in the security dialog"
fi

