# Troubleshooting Guide

This guide covers common issues and resolutions when running Lens.

---

## 1. Ollama Connection Errors

### Symptoms
* The HUD displays: `Connection error: Is the Observer running on http://127.0.0.1:5050?`
* The status badge shows Ollama as offline.

### Causes and Solutions
1. The Ollama service is not running.
   - Open a terminal and run:
     ```bash
     ollama serve
     ```
   - Alternatively, open the Ollama desktop application from your system menu.

2. Verify that Ollama is responding on localhost:
   - Run in your terminal:
     ```bash
     curl http://127.0.0.1:11434/api/tags
     ```
   - If this command fails, check whether your local firewall is blocking port 11434 on localhost.

3. Verify that the required model is installed:
   - Run:
     ```bash
     ollama list
     ```
   - If `qwen3-vl:8b` is missing, install it:
     ```bash
     ollama pull qwen3-vl:8b
     ```

---

## 2. Observer Daemon Does Not Start

### Symptoms
* Electron starts, but pressing `Alt + L` produces an error or no response.
* Port 5050 is unreachable.

### Causes and Solutions
1. Virtual environment missing or incomplete:
   - Navigate to `assistant-observer` and verify that `venv/Scripts/python.exe` exists.
   - If missing, run:
     ```bash
     setup.bat
     ```

2. Port 5050 is already in use by another application:
   - Check if another service is occupying port 5050:
     ```cmd
     netstat -ano | findstr :5050
     ```
   - If occupied, change the port in `assistant-observer/.env` (for example, `PORT=5055`) and update `assistant-electron/.env` to match (`ASSISTANT_OBSERVER=http://127.0.0.1:5055`).

3. Python dependencies missing:
   - Reinstall the requirements in the virtual environment:
     ```cmd
     assistant-observer\venv\Scripts\pip install -r assistant-observer\requirements.txt
     ```

---

## 3. Global Shortcut Does Not Trigger

### Symptoms
* Pressing `Alt + L` or `Alt + Shift + S` does not summon the HUD.

### Causes and Solutions
1. Another application has registered the shortcut with higher priority.
   - Some IDEs or gaming overlays register `Alt + L` or `Alt + Shift + S`.
   - You can click the Lens system tray icon to trigger analysis manually.
   - To customize shortcuts, edit the key string in `assistant-electron/main.js` (for example, change `'Alt+L'` to `'Alt+Space'`).

2. Privacy Mode is active:
   - If you previously pressed `Ctrl + Shift + P`, screen capture is temporarily paused.
   - Press `Ctrl + Shift + P` again to resume normal capture operations.

---

## 4. Unauthorized Error (HTTP 401)

### Symptoms
* The HUD displays: `HTTP 401: {"error": "unauthorized"}`

### Causes and Solutions
1. The authentication tokens in both `.env` files do not match.
   - Open `assistant-observer/.env` and verify the `ASSISTANT_TOKEN` value.
   - Open `assistant-electron/.env` and ensure the `ASSISTANT_TOKEN` value is identical.
   - Restart the application.

---

## 5. Slow Response Times on Vision Models

### Symptoms
* Responses take 30 to 45 seconds to begin streaming.

### Causes and Solutions
1. The model is running an internal thinking process.
   - Click the model badge in the HUD title bar.
   - Ensure the "Fast Mode (No Thinking)" checkbox is checked.
   - Lens will inject a bypass tag to skip the reasoning loop, reducing response latency to approximately 1.2 seconds.

2. Insufficient GPU VRAM:
   - If your graphics card has less than 6 GB VRAM, Ollama may offload model layers to system RAM, which slows down generation.
   - Close other VRAM-intensive applications or select a smaller model such as `llama3.2:3b`.

---

## 6. Snip Area Offset on Scaled Displays

### Symptoms
* In Area Snip mode (`Alt + Shift + S`), the captured region is shifted or zoomed in.

### Causes and Solutions
1. Windows display scaling factor mismatch:
   - Lens automatically adjusts for Windows display scaling (125%, 150%, 200%) using `window.devicePixelRatio`.
   - If you are running multiple monitors with different scaling factors, ensure Lens is updated to version 2.0.0 or later.
