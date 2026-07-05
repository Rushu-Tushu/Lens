# Architecture

## Overview

Lens follows a simple client-server architecture that runs entirely on the local machine.

The Electron desktop application acts as the user interface, while a lightweight Flask server performs screen analysis, OCR, prompt generation, and communication with the local language model through Ollama.

```
┌─────────────────────────────┐
│       Electron App          │
│  (System Tray & Overlay)    │
└──────────────┬──────────────┘
               │ HTTP Request
               ▼
┌─────────────────────────────┐
│      Flask Observer         │
├─────────────────────────────┤
│ • Active Window Detection   │
│ • Screen Capture            │
│ • OCR Processing            │
│ • Prompt Generation         │
│ • Privacy Controls          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│     Ollama Local Server     │
│      DeepSeek R1 Model      │
└──────────────┬──────────────┘
               │
               ▼
        AI Response
               │
               ▼
      Electron Overlay
```

---

# Request Flow

The following sequence occurs whenever the user requests assistance.

1. The user clicks **Ask Assistant** from the Electron system tray.
2. Electron sends a request to the local Flask Observer.
3. The Observer determines the currently active window.
4. Only the active window is captured.
5. The captured image is processed using Tesseract OCR.
6. The extracted text is converted into a prompt.
7. The prompt is sent to Ollama running locally.
8. The generated response is cleaned and formatted.
9. Electron displays the response inside the desktop overlay.

---

# Components

## Electron

Responsible for:

* System tray application
* Global keyboard shortcuts
* Transparent popup window
* Sending requests to the Observer
* Displaying AI responses

---

## Observer (Flask)

Responsible for:

* Authentication
* Active window detection
* Window capture
* OCR processing
* Prompt generation
* Communication with Ollama
* Returning structured JSON responses

---

## Tesseract OCR

Extracts readable text from the captured window before it is sent to the language model.

---

## Ollama

Runs the local language model used for understanding and generating responses.

Lens currently supports any model available through Ollama.

---

# Privacy Design

Lens is designed to minimize unnecessary data collection.

* Only the active window is captured.
* Nothing is uploaded to external services.
* Communication happens only through localhost.
* Screenshots are not stored unless explicitly enabled.
* Capture can be disabled instantly using the privacy toggle.

---

# Communication

Electron and the Observer communicate through HTTP on localhost.

```
Electron
    │
POST /analyze
    │
    ▼
Observer
    │
JSON Response
    ▼
Electron
```

Authentication is performed using a shared token sent in the `x-assistant-token` header.

---

# Project Layout

```
assistant-electron/
    Electron application

assistant-observer/
    Flask API
    OCR
    Prompt generation
    Ollama integration

docs/
    Project documentation

assets/
    Images and demo files
```
