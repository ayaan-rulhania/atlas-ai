const { app, BrowserWindow, shell, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

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
    mainWindow.show();
  });
  
  // Log when page finishes loading to help debug
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('Page loaded, Flask server should be ready');
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
ipcMain.handle('check-for-updates', async () => {
  // In a real implementation, you would check against a version endpoint
  // For now, return that app is up to date
  const currentVersion = app.getVersion();
  try {
    // You would fetch latest version from your server here
    // const latestVersion = await fetchLatestVersion();
    // return { available: latestVersion !== currentVersion, version: latestVersion };
    return { available: false, version: currentVersion, current: currentVersion };
  } catch (error) {
    return { available: false, error: error.message };
  }
});

ipcMain.handle('download-update', async () => {
  // In a real implementation, download the update DMG
  // For now, return success
  return { success: true };
});

ipcMain.handle('install-update', async () => {
  // In a real implementation, install the downloaded update
  // For now, return success
  return { success: true };
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

// Handle certificate errors (for local development)
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  if (url.startsWith('http://localhost') || url.startsWith('http://127.0.0.1')) {
    event.preventDefault();
    callback(true);
  } else {
    callback(false);
  }
});

