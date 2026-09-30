// assistant-electron/main.js
const { app, BrowserWindow, Tray, Menu, nativeImage, globalShortcut, screen, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const fetch = require('node-fetch');
require('dotenv').config();

const BACKEND_URL = process.env.ASSISTANT_OBSERVER || 'http://127.0.0.1:5050';
const TOKEN = process.env.ASSISTANT_TOKEN || 'local_secret_token';

let tray = null;
let popupWindow = null;
let snipWindow = null;
let backendProcess = null;

// ==================== WINDOW CREATION ====================

function createPopupWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;

  const iconPath = path.join(__dirname, 'lens-logo.png');
  popupWindow = new BrowserWindow({
    width: 560,
    height: 480,
    show: false,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: true,
    hasShadow: true,
    icon: iconPath,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  popupWindow.loadFile(path.join(__dirname, 'popup.html'));
  popupWindow.setSkipTaskbar(true);

  popupWindow.on('blur', () => {
    // Keep window visible when user interacts, or let them dismiss with Esc
  });
}

function positionPopupAtCursor() {
  if (!popupWindow) return;
  try {
    const cursorPos = screen.getCursorScreenPoint();
    const display = screen.getDisplayNearestPoint(cursorPos);
    const margin = 20;
    const winBounds = popupWindow.getBounds();

    // Position at top-right of active display
    let x = display.workArea.x + display.workArea.width - winBounds.width - margin;
    let y = display.workArea.y + margin;

    popupWindow.setPosition(Math.round(x), Math.round(y));
  } catch (e) {
    console.warn('[Lens] Positioning failed:', e);
  }
}

// ==================== SNIP WINDOW ====================

function openSnipWindow() {
  if (snipWindow) {
    snipWindow.focus();
    return;
  }

  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.bounds;

  snipWindow = new BrowserWindow({
    x: 0,
    y: 0,
    width: width,
    height: height,
    fullscreen: true,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  snipWindow.loadFile(path.join(__dirname, 'snip.html'));
  snipWindow.on('closed', () => {
    snipWindow = null;
  });
}

// ==================== BACKEND AUTO-ORCHESTRATION ====================

async function checkBackendHealth() {
  try {
    const res = await fetch(`${BACKEND_URL}/status`, { timeout: 800 });
    return res.ok;
  } catch (e) {
    return false;
  }
}

function startBackendDaemon() {
  const observerDir = path.resolve(__dirname, '..', 'assistant-observer');
  const venvPython = process.platform === 'win32'
    ? path.join(observerDir, 'venv', 'Scripts', 'python.exe')
    : path.join(observerDir, 'venv', 'bin', 'python');

  const pythonExec = fs.existsSync(venvPython) ? venvPython : 'python';

  console.log(`[Lens] Launching Observer backend using: ${pythonExec}`);
  try {
    backendProcess = spawn(pythonExec, ['app.py'], {
      cwd: observerDir,
      env: { ...process.env, ASSISTANT_TOKEN: TOKEN },
      stdio: 'ignore'
    });

    backendProcess.on('error', (err) => {
      console.error('[Lens] Observer daemon failed to start:', err.message);
    });

    backendProcess.on('exit', (code) => {
      console.log(`[Lens] Observer daemon exited with code ${code}`);
    });
  } catch (err) {
    console.warn('[Lens] Could not auto-spawn observer:', err.message);
  }
}

// ==================== STREAMING CLIENT ====================

async function streamRequest(endpoint, payload) {
  if (!popupWindow) return;

  if (!popupWindow.isVisible()) {
    positionPopupAtCursor();
    popupWindow.showInactive();
  }

  popupWindow.webContents.send('stream-start', {
    mode: payload.mode || 'general',
    isChat: endpoint.includes('chat')
  });

  try {
    const res = await fetch(`${BACKEND_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-assistant-token': TOKEN
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errText = await res.text();
      popupWindow.webContents.send('stream-error', `HTTP ${res.status}: ${errText.slice(0, 300)}`);
      return;
    }

    let buffer = '';
    let currentEvent = 'chunk';

    res.body.on('data', (chunk) => {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep partial trailing line

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          const rawData = line.slice(6);
          try {
            const data = JSON.parse(rawData);
            if (currentEvent === 'metadata') {
              popupWindow.webContents.send('stream-meta', data);
            } else if (currentEvent === 'think') {
              popupWindow.webContents.send('stream-think', data);
            } else if (currentEvent === 'chunk') {
              popupWindow.webContents.send('stream-chunk', data);
            } else if (currentEvent === 'done') {
              popupWindow.webContents.send('stream-done', data);
            } else if (currentEvent === 'error') {
              popupWindow.webContents.send('stream-error', data.error);
            }
          } catch (pe) {
            // Ignore non-json lines
          }
        }
      }
    });

    res.body.on('end', () => {
      popupWindow.webContents.send('stream-done');
    });

    res.body.on('error', (err) => {
      popupWindow.webContents.send('stream-error', String(err));
    });

  } catch (err) {
    console.error('[Lens] Stream request failed:', err);
    popupWindow.webContents.send('stream-error', `Connection error: Is the Observer running on ${BACKEND_URL}?`);
  }
}

function triggerAnalyze(options = {}) {
  const payload = {
    mode: options.mode || 'general',
    custom_prompt: options.custom_prompt || '',
    bbox: options.bbox || null,
    session_id: 'active_session',
    reuse_context: !!options.reuse_context,
    model: options.model || null
  };
  streamRequest('/analyze/stream', payload);
}

function sendChatMessage(message) {
  streamRequest('/chat/stream', {
    message: message,
    session_id: 'active_session'
  });
}

// ==================== APP LIFECYCLE ====================

app.whenReady().then(async () => {
  console.log('[Lens] Desktop app initialized');

  // Check if observer daemon is active; if not, spawn it
  const isHealthy = await checkBackendHealth();
  if (!isHealthy) {
    startBackendDaemon();
  }

  // System Tray Setup
  const iconPath = path.join(__dirname, 'lens-logo.png');
  const trayIcon = nativeImage.createFromPath(iconPath);
  tray = new Tray(trayIcon);

  const contextMenu = Menu.buildFromTemplate([
    { label: 'Summon Assistant (Alt+L)', click: () => triggerAnalyze() },
    { label: 'Snip Area (Alt+Shift+S)', click: () => openSnipWindow() },
    { type: 'separator' },
    { label: 'Toggle Privacy (Ctrl+Shift+P)', click: () => togglePrivacy() },
    { type: 'separator' },
    { label: 'Quit Lens', click: () => app.quit() }
  ]);

  tray.setToolTip('Lens: Privacy-First Desktop AI');
  tray.setContextMenu(contextMenu);
  tray.on('click', () => triggerAnalyze());

  createPopupWindow();

  // Register Global Shortcuts
  // 1. Primary summon shortcut: Alt+L
  let summonKey = 'Alt+L';
  const summonOk = globalShortcut.register(summonKey, () => {
    triggerAnalyze();
  });
  if (!summonOk) {
    console.warn(`[Lens] Could not register global shortcut: ${summonKey}`);
  } else {
    console.log(`[Lens] Registered global summon shortcut: ${summonKey}`);
  }

  // 2. Snip shortcut: Alt+Shift+S
  globalShortcut.register('Alt+Shift+S', () => {
    openSnipWindow();
  });

  // 3. Privacy toggle: Ctrl+Shift+P
  const privacyKey = process.platform === 'darwin' ? 'Command+Shift+P' : 'Control+Shift+P';
  globalShortcut.register(privacyKey, () => {
    togglePrivacy();
  });
});

async function togglePrivacy() {
  try {
    const res = await fetch(`${BACKEND_URL}/toggle_privacy`, {
      method: 'POST',
      headers: { 'x-assistant-token': TOKEN }
    });
    const data = await res.json();
    if (popupWindow) {
      popupWindow.webContents.send('stream-meta', {
        title: `Privacy ${data.capture_enabled ? 'Active (Ready)' : 'Paused (Disabled)'}`
      });
    }
  } catch (err) {
    console.error('[Lens] Toggle privacy failed:', err);
  }
}

// ==================== IPC HANDLERS ====================

ipcMain.on('window-close', () => {
  if (popupWindow) popupWindow.hide();
});

ipcMain.on('window-minimize', () => {
  if (popupWindow) popupWindow.minimize();
});

let isExpanded = false;
ipcMain.on('window-maximize', () => {
  if (!popupWindow) return;
  const primaryDisplay = screen.getPrimaryDisplay();
  const workArea = primaryDisplay.workArea;

  if (isExpanded) {
    popupWindow.setSize(560, 480);
    positionPopupAtCursor();
    isExpanded = false;
  } else {
    const newWidth = Math.min(880, workArea.width - 60);
    const newHeight = Math.min(680, workArea.height - 60);
    popupWindow.setSize(newWidth, newHeight);
    positionPopupAtCursor();
    isExpanded = true;
  }
});

ipcMain.on('trigger-analyze', (event, data) => {
  triggerAnalyze(data || {});
});

ipcMain.on('trigger-snip', () => {
  if (popupWindow) popupWindow.hide();
  openSnipWindow();
});

ipcMain.on('snip-selected', (event, bbox) => {
  if (snipWindow) {
    snipWindow.close();
    snipWindow = null;
  }
  triggerAnalyze({ bbox: [bbox.left, bbox.top, bbox.width, bbox.height] });
});

ipcMain.on('snip-cancelled', () => {
  if (snipWindow) {
    snipWindow.close();
    snipWindow = null;
  }
});

ipcMain.on('send-chat', (event, data) => {
  sendChatMessage(data.message);
});

ipcMain.on('hide-window', () => {
  if (popupWindow) popupWindow.hide();
});

ipcMain.handle('get-status', async () => {
  try {
    const res = await fetch(`${BACKEND_URL}/status`, {
      headers: { 'x-assistant-token': TOKEN },
      timeout: 1500
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn('[Lens] get-status check failed:', e.message);
  }
  return { ollama_online: false, installed_models: [], active_model: 'unknown' };
});

ipcMain.handle('set-config', async (event, config) => {
  try {
    const res = await fetch(`${BACKEND_URL}/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-assistant-token': TOKEN
      },
      body: JSON.stringify(config)
    });
    return await res.json();
  } catch (e) {
    console.error('[Lens] set-config failed:', e.message);
    return { ok: false, error: e.message };
  }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (backendProcess) {
    console.log('[Lens] Terminating Observer daemon...');
    backendProcess.kill();
  }
});
