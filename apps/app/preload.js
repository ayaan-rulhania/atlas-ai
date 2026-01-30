// Preload script for Electron
// This runs in a context that has access to both Node.js and the renderer

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the Node.js APIs without exposing the entire Node.js API
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  },
  isElectron: true,
  // Expose IPC methods for update checking
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  downloadUpdate: () => ipcRenderer.invoke('download-update'),
  installUpdate: (version) => ipcRenderer.invoke('install-update', version),
  relaunch: () => ipcRenderer.invoke('relaunch-app')
});

