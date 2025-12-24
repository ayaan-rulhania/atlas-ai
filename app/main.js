const { app, BrowserWindow, shell, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let flaskProcess = null;

// Default Flask server URL (can be overridden)
const FLASK_URL = process.env.ATLAS_FLASK_URL || 'http://localhost:5000';

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    backgroundColor: '#fafafa',
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true
    },
    icon: path.join(__dirname, 'assets', 'icon.icns')
  });

  // Load the Flask app
  mainWindow.loadURL(FLASK_URL);

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
    }
  });
  
  // Log when page finishes loading to help debug
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('Page loaded, Flask server should be ready');
  });
  
  // Handle failed page loads (network errors)
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error('Page failed to load:', {
      errorCode,
      errorDescription,
      validatedURL
    });
    
    // Only show error for main frame loads, not sub-resources
    if (errorCode === -105 || errorCode === -106) {
      // ERR_NAME_NOT_RESOLVED or ERR_INTERNET_DISCONNECTED
      console.error('Network error detected - Flask server may not be running');
    } else if (errorCode === -118) {
      // ERR_CONNECTION_TIMED_OUT
      console.error('Connection timeout - Flask server may not be responding');
    }
  });
  
  // Handle certificate errors (for local development)
  mainWindow.webContents.on('certificate-error', (event, url, error, certificate, callback) => {
    if (url.startsWith('http://localhost') || url.startsWith('http://127.0.0.1')) {
      // Ignore certificate errors for localhost
      event.preventDefault();
      callback(true);
    } else {
      callback(false);
    }
  });
}

// Start local Flask server if needed
function startFlaskServer() {
  // Check if Flask server is already running
  const http = require('http');
  const checkServer = () => {
    return new Promise((resolve) => {
      const req = http.get(FLASK_URL, (res) => {
        resolve(true);
      });
      req.on('error', () => {
        resolve(false);
      });
      req.setTimeout(1000, () => {
        req.destroy();
        resolve(false);
      });
    });
  };

  checkServer().then((isRunning) => {
    if (!isRunning) {
      console.log('Flask server not running, starting local server...');
      // Start Flask server
      const flaskPath = path.join(__dirname, '..', 'chatbot', 'app.py');
      const pythonPath = process.env.PYTHON_PATH || 'python3';
      
      flaskProcess = spawn(pythonPath, [flaskPath], {
        cwd: path.join(__dirname, '..'),
        env: { ...process.env, PORT: '5000' }
      });

      flaskProcess.stdout.on('data', (data) => {
        console.log(`Flask: ${data}`);
      });

      flaskProcess.stderr.on('data', (data) => {
        console.error(`Flask Error: ${data}`);
      });

      flaskProcess.on('close', (code) => {
        console.log(`Flask process exited with code ${code}`);
      });

      // Wait for server to be ready with retries
      const waitForServer = (retries = 30) => {
        if (retries <= 0) {
          console.error('Flask server failed to start in time');
          createWindow(); // Still create window, user can see error
          return;
        }
        
        const checkReady = () => {
          return new Promise((resolve) => {
            const req = http.get(FLASK_URL, (res) => {
              resolve(true);
            });
            req.on('error', () => {
              resolve(false);
            });
            req.setTimeout(500, () => {
              req.destroy();
              resolve(false);
            });
          });
        };
        
        checkReady().then((ready) => {
          if (ready) {
            console.log('Flask server is ready!');
            createWindow();
          } else {
            setTimeout(() => waitForServer(retries - 1), 500);
          }
        });
      };
      
      // Start checking after a short delay
      setTimeout(() => waitForServer(), 1000);
    } else {
      console.log('Flask server already running');
      createWindow();
    }
  });
}

// IPC handlers for update checking
ipcMain.handle('get-app-version', () => {
  // Check if there's a stored installed version (from previous update)
  const versionFile = path.join(app.getPath('userData'), 'installed-version.json');
  try {
    if (fs.existsSync(versionFile)) {
      const versionData = JSON.parse(fs.readFileSync(versionFile, 'utf8'));
      // Use stored version if it's newer than package.json version
      const packageVersion = app.getVersion();
      const storedVersion = versionData.version;
      // Compare versions (simple string comparison works for semantic versions)
      if (storedVersion && storedVersion !== packageVersion) {
        console.log(`[Update] Using stored version ${storedVersion} (package: ${packageVersion})`);
        return storedVersion;
      }
    }
  } catch (error) {
    console.error('[Update] Error reading stored version:', error);
  }
  return app.getVersion();
});

ipcMain.handle('check-for-updates', async () => {
  const currentVersion = app.getVersion();
  try {
    // Fetch latest version from server
    const http = require('http');
    return new Promise((resolve) => {
      const req = http.get(`${FLASK_URL}/api/version`, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          try {
            const versionData = JSON.parse(data);
            const latestVersion = versionData.latestVersion || currentVersion;
            resolve({
              available: latestVersion !== currentVersion,
              version: latestVersion,
              current: currentVersion,
              updates: versionData.updates || []
            });
          } catch (e) {
            resolve({ available: false, version: currentVersion, current: currentVersion });
          }
        });
      });
      req.on('error', () => {
        resolve({ available: false, version: currentVersion, current: currentVersion });
      });
      req.setTimeout(5000, () => {
        req.destroy();
        resolve({ available: false, version: currentVersion, current: currentVersion });
      });
    });
  } catch (error) {
    return { available: false, error: error.message, current: currentVersion };
  }
});

ipcMain.handle('download-update', async () => {
  // In a real implementation, download the update DMG
  // For now, return success
  return { success: true };
});

ipcMain.handle('install-update', async (event, newVersion) => {
  // Store the new version in a file so it persists after relaunch
  const versionFile = path.join(app.getPath('userData'), 'installed-version.json');
  try {
    fs.writeFileSync(versionFile, JSON.stringify({ version: newVersion, installedAt: new Date().toISOString() }));
    console.log(`[Update] Marked version ${newVersion} as installed`);
    return { success: true, version: newVersion };
  } catch (error) {
    console.error('[Update] Error saving version:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('relaunch-app', () => {
  app.relaunch();
  app.exit(0);
});

// App event handlers
app.whenReady().then(() => {
  startFlaskServer();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      startFlaskServer();
    }
  });
});

app.on('window-all-closed', () => {
  // Clean up Flask process
  if (flaskProcess) {
    flaskProcess.kill();
    flaskProcess = null;
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (flaskProcess) {
    flaskProcess.kill();
    flaskProcess = null;
  }
});

// Handle certificate errors at app level (for local development)
// Note: We also handle this at the window level above for better granularity
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  if (url.startsWith('http://localhost') || url.startsWith('http://127.0.0.1')) {
    event.preventDefault();
    callback(true);
  } else {
    callback(false);
  }
});

