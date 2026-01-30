# Installing Atlas macOS App

## macOS Security Warning

When you first try to open Atlas, macOS may show a security warning saying it "could not verify" the app. This is normal for unsigned applications.

### To Open Atlas:

**Option 1: Right-Click Method (Recommended)**
1. In Finder, locate the Atlas app
2. Right-click (or Control+Click) on the Atlas app
3. Select "Open" from the context menu
4. Click "Open" in the security dialog that appears
5. The app will launch and macOS will remember your choice

**Option 2: System Settings**
1. When you see the security warning, click "Done"
2. Go to System Settings > Privacy & Security
3. Scroll down to the security section
4. You should see a message about Atlas being blocked
5. Click "Open Anyway" next to the Atlas message

**Option 3: Remove Quarantine Attribute (Recommended)**
Run this command in Terminal to remove the quarantine attribute:
```bash
xattr -d com.apple.quarantine /Applications/Atlas.app
```

Or use the provided script from the app directory:
```bash
cd /path/to/atlas-ai/app
./allow-atlas.sh
```

This will allow Atlas to run without any security warnings.

## Why This Happens

Atlas is built with Electron and is not currently code-signed with an Apple Developer certificate. This is a security feature of macOS called Gatekeeper that protects users from potentially harmful software.

For a production release, you would need to:
1. Enroll in the Apple Developer Program ($99/year)
2. Get a Developer ID Application certificate
3. Sign the app before distribution

For local development and testing, the methods above work perfectly fine.

## Troubleshooting

If you still can't open the app after trying the methods above, check:
- That you dragged the app from the DMG to Applications folder
- That you're using macOS 10.12 or later
- That your Mac's security settings allow apps from "identified developers"

