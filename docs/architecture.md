# Architecture

## Overview

Lens follows a local-first, privacy-respecting client-server architecture designed for zero cloud reliance and sub-second on-demand screen intelligence.

The system consists of three independent local processes communicating over localhost:
1. Electron Desktop Client: Provides the system tray, global keyboard hooks, glassmorphic HUD overlay, model switcher, and interactive area snip selector.
2. Flask Observer Daemon: Manages Windows active window detection, DPI-aware pixel capture, multimodal vision encoding, fallback OCR, conversation memory, and Server-Sent Events (SSE) streaming.
3. Ollama Local Server: Handles local neural model inference for vision models (`qwen3-vl:8b`, `qwen2.5-vl`, `gemma-vl`, `llama3.2-vision`) and reasoning models (`deepseek-r1:8b`).

```text
+-----------------------------------------------------------+
|                 Electron Desktop Client                   |
|   - Global Shortcuts (Alt+L, Alt+Shift+S)                 |
|   - Glassmorphic Streaming HUD (popup.html)               |
|   - Interactive Snip Area Selector (snip.html)            |
|   - In-HUD Model Switcher and Fast Mode Toggle            |
+-----------------------------+-----------------------------+
                              | Server-Sent Events (SSE)
                              | Header: x-assistant-token
                              v
+-----------------------------------------------------------+
|              Flask Observer Daemon (Port 5050)            |
|   - Active Window Discovery (win32gui / pygetwindow)      |
|   - DPI-Aware Screen / Region Capture (mss)               |
|   - Direct Vision Pipeline (Base64 JPEG)                  |
|   - Fallback OCR Engine (pytesseract)                     |
|   - Context Caching and Session Memory                    |
+-----------------------------+-----------------------------+
                              | HTTP Streaming (/api/chat)
                              v
+-----------------------------------------------------------+
|                    Ollama Local Server                    |
|   - Multimodal Vision: qwen3-vl, qwen2.5-vl, gemma-vl     |
|   - Text Reasoning: deepseek-r1, llama3.2                 |
+-----------------------------------------------------------+
```

---

## Detailed Request Flows

### 1. Active Window Analysis (`Alt + L`)
1. The user presses `Alt + L` while working in any desktop application (such as code editor, browser, or terminal).
2. Electron captures the current cursor position, determines the nearest display monitor, and positions the HUD in the top-right work area.
3. Electron dispatches a POST request to `http://127.0.0.1:5050/analyze/stream` with the user token and selected analysis mode (`general`, `fix`, `explain`, `optimize`, or `tldr`).
4. The Observer runs `get_active_window_info()`:
   - On Windows, it invokes Win32 API calls (`GetForegroundWindow`, `GetWindowRect`).
   - If the foreground window is Lens itself (or a taskbar utility), it walks the OS z-order to identify the actual application window directly beneath.
5. The window rectangle is passed to `mss` for in-memory pixel capture. If the captured frame exceeds 1920 pixels in width, it is downscaled using Lanczos resampling to preserve sharpness while minimizing inference memory.
6. Routing logic determines model capability:
   - If a vision model is active (`qwen3-vl:8b`), the image is converted to Base64 JPEG and attached directly to the prompt payload.
   - If a text-only model is active (`llama3.2:3b`), the image is passed to Tesseract OCR to extract plain text.
7. If Fast Mode is active, an assistant prefill tag (`<think>\n</think>`) is injected into the chat request, immediately skipping internal reasoning loops and initiating response streaming in approximately 1.2 seconds.
8. Ollama streams response tokens over HTTP. The Observer translates these chunks into Server-Sent Events (`event: think`, `event: chunk`, `event: done`).
9. Electron receives the SSE stream, updating the Markdown viewer with live syntax-highlighted code blocks and 1-click copy buttons.

### 2. Area Snip Mode (`Alt + Shift + S`)
1. The user presses `Alt + Shift + S`.
2. Electron opens a fullscreen, transparent, frameless window with custom crosshairs.
3. The user drags a selection box over the desired screen region (such as a specific stack trace, graph, or error code).
4. Coordinates are scaled by `window.devicePixelRatio` to ensure 1:1 pixel accuracy on high-DPI displays (125%, 150%, 200%).
5. The coordinates are dispatched to `/analyze/stream` with `{ bbox: [left, top, width, height] }`.
6. Only the selected pixels are captured and analyzed.

### 3. Screen Context Chat (Follow-Up Queries)
1. The user types a follow-up instruction in the bottom terminal chat bar of the HUD.
2. Electron appends the user query to the local conversation thread and posts to `/chat/stream`.
3. The Observer loads the cached screen image and context from the active session.
4. The follow-up response streams directly into a new message card within the existing thread, preserving the full conversational history.

### 4. Smart Context Reuse on Mode Switching
When a user switches between action tabs (`DEBUG`, `EXPLAIN`, `OPTIMIZE`, `TLDR`) within an active session:
1. Electron passes `reuse_context: true` in the request payload.
2. The Observer reuses the existing in-memory screen frame instead of capturing the display again.
3. This prevents the HUD overlay from accidentally capturing itself and provides instant mode switching.

---

## Security and Process Isolation

1. Strict Local Loopback: All communication is bound to `127.0.0.1`. No sockets listen on public network interfaces.
2. RAM-Only Ephemeral Processing: Screenshots and extracted text exist exclusively in volatile memory during inference. Files are not written to disk unless explicitly enabled via the `save_screenshots` configuration flag.
3. Local Token Authentication: Every request requires the `x-assistant-token` header, preventing unauthorized local processes from invoking endpoints.
4. Instant Privacy Killswitch: Pressing `Ctrl + Shift + P` globally suspends all screen capture capabilities.
5. Zero Telemetry: No analytics packages, tracking scripts, or external network calls exist in the codebase.
