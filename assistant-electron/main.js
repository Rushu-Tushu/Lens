// assistant-electron/main.js
const { app, BrowserWindow, Tray, Menu, nativeImage, globalShortcut, screen } = require('electron');
const path = require('path');
const fetch = require('node-fetch');
require('dotenv').config();

const BACKEND_URL = process.env.ASSISTANT_OBSERVER;
const TOKEN = process.env.ASSISTANT_TOKEN;

let tray = null;
let popupWindow = null;

function createWindow() {
  popupWindow = new BrowserWindow({
    width: 480,
    height: 220,
    show: false,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    hasShadow: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  popupWindow.loadFile(path.join(__dirname, 'popup.html'));
  // remove from task switcher (Windows)
  popupWindow.setSkipTaskbar(true);
}

app.whenReady().then(() => {
  console.log("Electron app is ready");

  const iconPath = path.join(__dirname, 'AI.png');
  let trayIcon = nativeImage.createFromPath(iconPath);
  tray = new Tray(trayIcon);
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Ask Assistant (analyze now)', click: () => triggerAnalyze() },
    { type: 'separator' },
    { label: 'Toggle Privacy Hotkey (Ctrl/Cmd+Shift+P)', enabled: false },
    { label: 'Quit', click: () => { app.quit(); } }
  ]);
  tray.setToolTip('AI Laptop Companion (Toggle)');
  tray.setContextMenu(contextMenu);
  tray.on('click', () => {
    try {
      tray.popUpContextMenu();
    } catch (e) {
      console.error('tray.popUpContextMenu failed', e);
    }
  });

  createWindow();

  // Register global hotkey Ctrl/Cmd+Shift+P to toggle privacy
  const hotkey = process.platform === 'darwin' ? 'Command+Shift+P' : 'Control+Shift+P';
  const ok = globalShortcut.register(hotkey, async () => {
    // Call observer to toggle privacy
    try {
      const res = await fetch(`${BACKEND_URL}/toggle_privacy`, {
        method: 'POST',
        headers: { 'x-assistant-token': TOKEN }
      });
      const data = await res.json();
      console.log('toggle_privacy response', data);
      // Show a quick popup indicating new state
      showTemporaryMessage(`Capture ${data.capture_enabled ? 'enabled' : 'disabled'}`, 1200);
    } catch (err) {
      console.error('toggle_privacy error', err);
      showTemporaryMessage('Toggle failed', 1200);
    }
  });
  if (!ok) console.warn('Global shortcut registration failed');

});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

function showTemporaryMessage(msg, ms=1500) {
  if (!popupWindow) return;
  popupWindow.show();
  popupWindow.webContents.send('analysis-done', { title: 'Assistant', assistant: msg });
  setTimeout(()=> popupWindow.hide(), ms);
}

async function triggerAnalyze() {
  if (!popupWindow) return;
  // Position popup at top-right of active display
  try {
    const display = screen.getDisplayNearestPoint(screen.getCursorScreenPoint());
    const margin = 16;
    const x = display.workArea.x + display.workArea.width - 480 - margin;
    const y = display.workArea.y + margin;
    popupWindow.setPosition(x, y);
  } catch (e) {
    console.warn('Positioning failed', e);
  }

  popupWindow.webContents.send('analysis-start');
  popupWindow.show();

  try {
    const res = await fetch(`${BACKEND_URL}/analyze`, {
      method: 'POST',
      headers: { 'x-assistant-token': TOKEN }
    });

    // Read raw text first (so we can inspect HTML or error pages)
    const raw = await res.text();
    console.log('analyze raw response (first 2000 chars):', raw.slice(0, 2000));

    let data = null;
    try {
      data = JSON.parse(raw);
      console.log('analyze parsed json', data);
    } catch (parseErr) {
      console.error('analyze: failed to parse JSON, raw content logged above', parseErr);
      // show a helpful extract in the popup so you can see the server HTML/error
      const snippet = raw.replace(/\n/g, ' ').slice(0, 1200);
      popupWindow.webContents.send('analysis-error', `Server returned non-JSON response (first 1200 chars):\n\n${snippet}`);
      return;
    }

    if (data.error) {
      popupWindow.webContents.send('analysis-error', data.error);
    } else {
      popupWindow.webContents.send('analysis-done', data);
    }
  } catch (err) {
    console.error('analyze fetch error', err);
    popupWindow.webContents.send('analysis-error', String(err));
  }
}

