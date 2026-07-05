# Lens

> Privacy-first, context-aware desktop assistant that analyzes your active window and provides contextual assistance using local LLMs.

## Overview

Lens is a desktop AI assistant that helps you understand what's on your screen without sending your data to the cloud.

When you request assistance, Lens captures only the currently active window, extracts the visible text using OCR, and sends the extracted context to a locally running Large Language Model (LLM) through Ollama. The generated response is displayed in a lightweight desktop overlay, allowing you to get explanations, summaries, or coding assistance without leaving your workflow.

All processing happens locally on your machine. Screenshots are never saved unless explicitly enabled.

## Features

* 🖥️ Analyze only the active window
* 🤖 Local AI inference using Ollama
* 🔍 OCR-powered text extraction with Tesseract OCR
* 💬 Lightweight Electron overlay
* 🔒 Privacy-first local processing
* ⌨️ Toggle capture on or off instantly
* 📄 Screenshot saving disabled by default
* 🔐 Token-authenticated communication between components
* ⚡ Fast local responses with no cloud dependency

## How It Works

```text
┌─────────────────────┐
│  Electron Desktop   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Flask Observer    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Capture Active      │
│ Window              │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  OCR (Tesseract)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Prompt Generation   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Ollama (DeepSeek)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Desktop Overlay     │
└─────────────────────┘
```

## Project Structure

```text
Lens/
├── assistant-electron/      # Electron desktop application
├── assistant-observer/      # Flask backend, OCR pipeline and AI integration
├── assets/                  # Screenshots and demo assets
├── docs/
│   ├── architecture.md
│   ├── installation.md
│   ├── privacy.md
│   ├── roadmap.md
│   └── troubleshooting.md
├── .gitignore
├── LICENSE
└── README.md
```

## Tech Stack

| Component               | Technology           |
| ----------------------- | -------------------- |
| Desktop Application     | Electron             |
| Backend                 | Flask                |
| AI Model                | Ollama (DeepSeek R1) |
| OCR                     | Tesseract OCR        |
| Screen Capture          | MSS                  |
| Active Window Detection | PyGetWindow          |
| Languages               | Python, JavaScript   |
| Communication           | HTTP (localhost)     |

## Installation

See the complete installation guide in:

```text
docs/installation.md
```

## Usage

1. Start Ollama.
2. Start the Observer backend.
3. Launch the Electron application.
4. Open any application you want to analyze.
5. Click **Ask Assistant** from the system tray.
6. Read the generated summary in the desktop overlay.

## Privacy

Lens is designed with privacy as a core principle.

* Runs entirely on your local machine.
* No cloud APIs are used.
* Only the active window is analyzed.
* Screenshots are not saved by default.
* Communication is restricted to `127.0.0.1`.
* Electron and the Observer authenticate using a shared token.

For more information, see:

```text
docs/privacy.md
```

## Documentation

Additional documentation is available in the `docs` directory.

* Architecture
* Installation
* Privacy
* Troubleshooting
* Roadmap

## Roadmap

See:

```text
docs/roadmap.md
```

## License

This project is licensed under the MIT License.
