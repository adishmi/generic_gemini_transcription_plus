import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'path';
import fs from 'fs';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

// ESM dirname workaround
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow;
let pythonProcess = null;

const createWindow = () => {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.cjs'),
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: false
        },
    });

    // In dev, load vite server
    if (process.env.VITE_DEV_SERVER_URL) {
        mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
        mainWindow.webContents.openDevTools();
    } else {
        // In prod, load index.html
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }
};

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (process.platform !== 'darwin') app.quit();
});

// --- Python Sidecar Logic ---

ipcMain.handle('get-app-paths', () => {
    const userData = app.getPath('userData');

    // Project root config (source of truth for seeding)
    // __dirname is electron/, ../ is AudioFlow/, ../../ is Gemini Transcribe/
    const settingsPath = path.join(userData, 'settings.json');

    return {
        userData,
        userData,
        settingsPath,
        statePath: path.join(userData, 'state.json'),
    };
});

ipcMain.handle('get-state', async () => {
    const userData = app.getPath('userData');
    const statePath = path.join(userData, 'state.json');
    try {
        if (fs.existsSync(statePath)) {
            const data = fs.readFileSync(statePath, 'utf-8');
            return JSON.parse(data);
        }
    } catch (e) {
        console.error("Failed to read state:", e);
    }
    return { active_jobs: {} };
});

ipcMain.handle('start-engine', async (event, { pythonPath }) => {
    if (pythonProcess) {
        console.log('Engine already running. Restarting...');
        pythonProcess.kill();
        pythonProcess = null;
    }

    const userData = app.getPath('userData');
    // We now use the settings.json in userData as the active config
    const settingsPath = path.join(userData, 'settings.json');
    const statePath = path.join(userData, 'state.json');

    // --- SIDECAR LOGIC ---
    let finalPython = pythonPath;
    let backendPath = path.join(__dirname, '../backend/engine.py');
    let args = ['-u', backendPath, '--config', settingsPath, '--state', statePath];

    if (app.isPackaged) {
        // In production, use the bundled executable
        const exePath = path.join(process.resourcesPath, 'backend/engine_backend');
        finalPython = exePath;
        args = ['--config', settingsPath, '--state', statePath]; // Sidecar doesn't need python -u or engine.py script arg
        console.log('Running packaged sidecar:', finalPython);
    } else {
        // In development, handle venv
        const venvPython = path.join(__dirname, '../backend/venv/bin/python');
        if ((!pythonPath || pythonPath === 'python3') && fs.existsSync(venvPython)) {
            finalPython = venvPython;
            console.log('Using local venv:', finalPython);
        }
        console.log(`Spawning Python: ${finalPython} ${backendPath} --config ${settingsPath}`);
    }

    pythonProcess = spawn(finalPython, args, {
        cwd: app.isPackaged ? process.resourcesPath : path.dirname(backendPath),
        stdio: ['ignore', 'pipe', 'pipe']
    });

    pythonProcess.stdout.on('data', (data) => {
        const str = data.toString();
        // console.log(`[Python]: ${str}`);
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('engine-log', str);
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        const str = data.toString();
        console.error(`[Python ERR]: ${str}`);
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('engine-error', str);
        }
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('engine-exit', code);
        }
        pythonProcess = null;
    });

    return true;
});

ipcMain.handle('check-python', async (event, pathCheck) => {
    return new Promise((resolve) => {
        const check = spawn(pathCheck || 'python3', ['--version']);
        check.on('error', () => resolve(false));
        check.on('close', (code) => resolve(code === 0));
    });
});

ipcMain.handle('stop-engine', () => {
    if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
    }
    return true;
});
