# Architecture

## Overview

Lens follows a local-first, privacy-respecting client-server architecture designed for zero cloud reliance and sub-second on-demand screen intelligence.

The system consists of three local processes:
1. **Electron Desktop App**: System tray, global keyboard shortcuts, Raycast-style glassmorphic streaming HUD, and area snip selector.
2. **Flask Observer Daemon**: Active window detection, bounding-box capture, multimodal vision encoding, fallback OCR, conversation memory, and Server-Sent Events (SSE) streaming.
3. **Ollama Local Server**: Multi-modal vision (`qwen2.5-vl`, `qwen3-vl`, `gemma-vl`, `llama3.2-vision`) and text reasoning inference (`deepseek-r1:8b`).

```
┌───────────────────────────────────────────────────────────┐
│                 Electron Desktop Client                   │
│   • Global Shortcuts (Alt+L, Alt+Shift+S)                 │
│   • Glassmorphic Streaming HUD (popup.html)               │
│   • Interactive Snip Area Selector (snip.html)            │
└─────────────────────────────┬─────────────────────────────┘
                              │ Server-Sent Events (SSE)
                              ▼
┌───────────────────────────────────────────────────────────┐
│              Flask Observer Backend (:5050)               │
│   • Active Window Discovery (pygetwindow)                 │
│   • Screen / Region Capture (mss)                         │
│   • Direct Vision Pipeline (Base64 JPEG)                  │
│   • Fallback OCR Engine (pytesseract)                     │
│   • Session Conversation Memory                           │
└─────────────────────────────┬─────────────────────────────┘
                              │ HTTP Streaming (/api/generate)
                              ▼
┌───────────────────────────────────────────────────────────┐
│                    Ollama Local Server                    │
│   • qwen2.5-vl / qwen3-vl / gemma-vl (Multimodal)         │
│   • deepseek-r1 / llama3.2 (Text & Reasoning)             │
└───────────────────────────────────────────────────────────┘
```

---

## Request Flow

### 1. Window Analysis (`Alt + L` or Tray Click)
1. User presses `Alt + L` while focused on any application.
2. Electron positions the translucent HUD on the active monitor and initiates a POST request to `/analyze/stream`.
3. The Observer identifies the active window's bounding box and captures the pixels via `mss`.
4. **Vision or OCR Branch**:
   - If a multimodal model is configured (e.g., `qwen2.5-vl`, `gemma-vl`), the image is base64-encoded and sent directly in the Ollama request.
   - If a text-only model is configured (e.g., `deepseek-r1`), the image is processed with Tesseract OCR.
5. Ollama streams tokens back via NDJSON.
6. The Observer relays tokens via Server-Sent Events (SSE) directly to Electron.
7. The HUD renders Markdown in real-time with syntax-highlighted code blocks.

### 2. Area Snip Mode (`Alt + Shift + S`)
1. User presses `Alt + Shift + S`.
2. Electron opens a fullscreen transparent window with interactive crosshairs.
3. User drags a rectangle over the desired error or snippet.
4. On release, the bounding box coordinates are dispatched to `/analyze/stream` with `{ bbox: [x, y, w, h] }`.

### 3. Screen Context Chat (Follow-Up Queries)
1. User types into the bottom chat input bar of the HUD.
2. Electron posts to `/chat/stream` with the user query and session ID.
3. The Observer injects the cached window context and streams the follow-up answer.

---

## Security & Isolation

- **Zero Cloud Network Traffic**: Strictly bound to `127.0.0.1`.
- **Ephemeral RAM Processing**: Screenshots are never written to disk by default.
- **Session Authentication**: Secured via `x-assistant-token` header.
- **Privacy Kill-Switch**: `Ctrl + Shift + P` globally suspends capture capabilities.
