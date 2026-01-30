# How Live Updates Work in Atlas macOS App

## Current Implementation (Placeholder)

The current update mechanism is a **placeholder/skeleton** that demonstrates the UI and flow. Here's how it's designed to work:

## Update Flow

### 1. **User Triggers Update Check**
   - User clicks the install/update button (download icon) in the app
   - App detects it's running in Electron (macOS app)
   - Redirects to `/update` page instead of `/install`

### 2. **Update Check Process**
   ```
   User clicks button → /update page loads → JavaScript checks for updates
   ```

   **Current code (update.html):**
   - Simulates checking (1.5 second delay)
   - Always shows "up to date" (placeholder)
   
   **What it SHOULD do:**
   ```javascript
   // 1. Get current app version
   const currentVersion = app.getVersion(); // e.g., "1.0.0"
   
   // 2. Fetch latest version from server
   const response = await fetch('/api/version'); // or external API
   const { latestVersion, downloadUrl } = await response.json();
   
   // 3. Compare versions
   if (latestVersion !== currentVersion) {
     // Show "Update Available" with download button
   } else {
     // Show "Up to date"
   }
   ```

### 3. **Download Process** (When Update Available)
   ```
   User clicks "Download Update" → Progress bar shows → DMG downloads
   ```

   **Current code:**
   - Simulates download progress (0-100%)
   - Shows progress bar animation
   
   **What it SHOULD do:**
   ```javascript
   // 1. Download DMG file
   const dmgUrl = '/download/atlas-macos.dmg'; // or latest version URL
   const response = await fetch(dmgUrl);
   const blob = await response.blob();
   
   // 2. Save to temp directory
   const fs = require('fs');
   const tempPath = path.join(os.tmpdir(), 'Atlas-update.dmg');
   fs.writeFileSync(tempPath, blob);
   
   // 3. Show progress
   // Use response.body.getReader() for streaming progress
   ```

### 4. **Installation Process**
   ```
   Download completes → Install DMG → Replace app → Relaunch
   ```

   **Current code:**
   - Simulates installation
   - Shows "Installing update..." message
   
   **What it SHOULD do:**
   ```javascript
   // 1. Mount DMG
   const { exec } = require('child_process');
   exec(`hdiutil attach "${dmgPath}"`, (error, stdout) => {
     // 2. Copy new app to Applications
     exec(`cp -R "/Volumes/Atlas Installer/Atlas.app" "/Applications/"`, () => {
       // 3. Unmount DMG
       exec(`hdiutil detach "/Volumes/Atlas Installer"`, () => {
         // 4. Relaunch app
         app.relaunch();
         app.exit(0);
       });
     });
   });
   ```

### 5. **Relaunch**
   ```
   App closes → New version launches automatically
   ```

   **Current code:**
   - Uses `window.location.href = '/'` (doesn't actually relaunch)
   
   **What it SHOULD do:**
   ```javascript
   // In Electron main process (main.js)
   app.relaunch();
   app.exit(0);
   ```

## How Updates Reach Outdated Versions

### Option 1: **Server-Side Version Endpoint** (Recommended)
```
Old App (v1.0.0) → Checks /api/version → Server says "v1.1.0 available" → Downloads update
```

**Implementation:**
1. Add `/api/version` endpoint in Flask:
   ```python
   @app.route('/api/version')
   def get_version():
       return jsonify({
           'current': '1.0.0',
           'latest': '1.1.0',
           'downloadUrl': '/download/atlas-macos.dmg',
           'releaseNotes': '...'
       })
   ```

2. Update checker compares versions
3. If newer version exists, downloads from server

### Option 2: **External Update Server**
```
Old App → Checks update.atlas-ai.com/version → Downloads from CDN
```

**Benefits:**
- Works even if local server is down
- Can serve updates from CDN (faster)
- Can track update adoption

### Option 3: **Auto-Update Service** (electron-updater)
```
Old App → Uses electron-updater → Checks GitHub releases → Auto-updates
```

**Implementation:**
- Use `electron-updater` package
- Publish releases to GitHub
- App automatically checks and updates

## Current Status

**What Works:**
- ✅ UI for update checking
- ✅ Progress bar display
- ✅ Electron detection
- ✅ Routing to update page in app

**What's Missing:**
- ❌ Real version checking
- ❌ Actual DMG download
- ❌ DMG mounting/installation
- ❌ App replacement
- ❌ Proper relaunch

## Next Steps to Implement Full Updates

1. **Add version endpoint:**
   ```python
   # In chatbot/app.py
   @app.route('/api/version')
   def get_version():
       return jsonify({
           'latest': '1.0.0',
           'downloadUrl': '/download/atlas-macos.dmg'
       })
   ```

2. **Implement real version check in update.html:**
   ```javascript
   const response = await fetch('/api/version');
   const { latest, current } = await response.json();
   if (latest !== current) {
     // Show update button
   }
   ```

3. **Add download functionality:**
   - Use Electron's `ipcRenderer.invoke('download-update')`
   - Stream download with progress
   - Save to temp directory

4. **Add installation:**
   - Mount DMG using `hdiutil`
   - Copy app to Applications
   - Unmount DMG
   - Relaunch app

5. **Use electron-updater (Recommended):**
   ```bash
   npm install electron-updater
   ```
   - Handles all of the above automatically
   - Supports auto-updates from GitHub/GitLab/etc.

## Summary

**Current:** Placeholder UI that simulates the update process

**How it would work:**
1. Old app checks server for latest version
2. If newer version exists, downloads DMG
3. Installs new version
4. Relaunches with new version

**Key Point:** The old app can always check the server (which has the latest version info), so it knows when updates are available and can download them.

