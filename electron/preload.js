const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  appVersion: () => '2.0.0',
  isElectron: true,
  getAutoLaunch: () => ipcRenderer.invoke('get-auto-launch'),
  setAutoLaunch: (enable) => ipcRenderer.invoke('set-auto-launch', enable),
  showNotification: (title, body) => ipcRenderer.invoke('show-notification', { title, body })
});

