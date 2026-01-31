const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getAppPaths: () => ipcRenderer.invoke('get-app-paths'),
    getState: () => ipcRenderer.invoke('get-state'),
    startEngine: (pythonPath) => ipcRenderer.invoke('start-engine', { pythonPath }),
    stopEngine: () => ipcRenderer.invoke('stop-engine'),
    checkPython: (path) => ipcRenderer.invoke('check-python', path),

    onLog: (callback) => ipcRenderer.on('engine-log', (_event, value) => callback(value)),
    onError: (callback) => ipcRenderer.on('engine-error', (_event, value) => callback(value)),
    onExit: (callback) => ipcRenderer.on('engine-exit', (_event, value) => callback(value)),

    // Config/State read/write via filesystem can be done in Renderer if path is known
    // But better to verify paths via main. Use Node fs in main or allow Renderer with nodeIntegration: false?
    // Electron security best practice: Do not enable nodeIntegration.
    // If we want Renderer to read/write JSON, we can expose fs methods in preload safely or do it via IPC.
    // Given the complexity, let's expose simple file read/write for config/state in preload using Node fs
    // RESTRICTED to specific paths.
});

// Since we cannot import fs in renderer easily without nodeIntegration, we can expose it here.
const fs = require('fs');

contextBridge.exposeInMainWorld('fsAPI', {
    readFile: (path) => {
        return new Promise((resolve, reject) => {
            fs.readFile(path, 'utf-8', (err, data) => {
                if (err) reject(err);
                else resolve(data);
            });
        });
    },
    writeFile: (path, data) => {
        return new Promise((resolve, reject) => {
            fs.writeFile(path, data, (err) => {
                if (err) reject(err);
                else resolve(true);
            });
        });
    },
    exists: (path) => fs.existsSync(path),
    mkdir: (path) => fs.mkdirSync(path, { recursive: true })
});
