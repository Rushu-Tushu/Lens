# Installation Guide

This document provides complete instructions for installing, configuring, and verifying Lens on your system.

---

## System Requirements

| Requirement | Minimum | Recommended |
| :--- | :--- | :--- |
| Operating System | Windows 10 (64-bit), macOS 12+, or modern Linux | Windows 11 (64-bit) |
| Processor | 4-core x86_64 / ARM64 processor | 8-core CPU or Apple Silicon |
| Memory | 8 GB RAM | 16 GB or more RAM |
| Graphics (VRAM) | Integrated Graphics | Dedicated NVIDIA/AMD GPU or Apple M-series (6 GB+ VRAM) |
| Disk Storage | 10 GB free space (for Ollama model storage) | NVMe SSD |

---

## Prerequisites

Before setting up Lens, ensure the following tools are installed on your machine:

1. Python (version 3.10 or later)
   - Ensure the option "Add Python to PATH" is selected during installation.
   - Verify in your terminal: `python --version`

2. Node.js (version 20 or later)
   - Includes npm (Node Package Manager).
   - Verify in your terminal: `node --version` and `npm --version`

3. Git
   - For cloning the repository.
   - Verify in your terminal: `git --version`

4. Ollama
   - Required for local model execution.
   - Download and install from: https://ollama.com
   - Verify in your terminal: `ollama --version`

5. Tesseract OCR (Optional)
   - Only required if you intend to use text-only models like `llama3.2:3b`.
   - Not required when using vision models like `qwen3-vl:8b`, which process screen pixels directly.

---

## Step 1: Install and Prepare Ollama Models

Start the Ollama application or run `ollama serve` in a terminal.

Download your preferred vision model:

```bash
# Recommended default model (multimodal vision, fast speed)
ollama pull qwen3-vl:8b
```

If you also wish to use text reasoning models:

```bash
# Optional: DeepSeek R1 reasoning model
ollama pull deepseek-r1:8b
```

Verify that the models are downloaded:

```bash
ollama list
```

---

## Step 2: Clone the Repository

Clone the project repository to your local machine:

```bash
git clone https://github.com/RuSapkal69/Personal_AI_Assistant.git
cd Personal_AI_Assistant
```

---

## Step 3: Installation Methods

### Method A: 1-Click Automated Setup (Windows)

On Windows systems, an automated installation script handles environment creation and dependency resolution:

1. Double-click `setup.bat` or execute it from the terminal:
   ```cmd
   setup.bat
   ```

2. The script will automatically:
   - Verify your Python, Node.js, and Ollama installations.
   - Create a dedicated Python virtual environment at `assistant-observer/venv`.
   - Install required Python dependencies from `requirements.txt`.
   - Initialize `.env` files from `.env.example` in both directories.
   - Install Electron dependencies via `npm install`.

3. Once setup completes successfully, start Lens by double-clicking `run.bat` or executing:
   ```cmd
   run.bat
   ```

---

### Method B: Manual Step-by-Step Installation

If you prefer to configure each component manually or are running on macOS or Linux, follow these steps:

#### 1. Configure the Python Observer Daemon

Navigate to the observer directory:
```bash
cd assistant-observer
```

Create and activate a virtual environment:
```bash
# On Windows:
python -m venv venv
venv\Scripts\activate

# On macOS / Linux:
# python3 -m venv venv
# source venv/bin/activate
```

Install Python dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Create the environment file:
```bash
cp .env.example .env
```

The default values in `assistant-observer/.env` are:
```env
ASSISTANT_TOKEN=local_secret_token
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3-vl:8b
PORT=5050
```

Return to the root directory:
```bash
cd ..
```

#### 2. Configure the Electron Desktop Client

Navigate to the desktop client directory:
```bash
cd assistant-electron
```

Install node dependencies:
```bash
npm install
```

Create the client environment file:
```bash
cp .env.example .env
```

The default values in `assistant-electron/.env` are:
```env
ASSISTANT_TOKEN=local_secret_token
ASSISTANT_OBSERVER=http://127.0.0.1:5050
```

#### 3. Start Lens

From the `assistant-electron` directory, launch the application:
```bash
npm start
```

The Electron client automatically verifies that the Python Observer daemon is running. If the daemon is offline, Electron spawns it automatically using the virtual environment interpreter.

---

## Verifying the Installation

1. Check System Tray:
   A Lens icon will appear in the Windows notification area or system tray.

2. Test Global Shortcuts:
   - Focus on any open window (such as code editor or browser).
   - Press `Alt + L`.
   - The translucent Lens HUD will appear in the top-right corner of your screen, displaying the title of the active window and analyzing its visible content.

3. Test Area Snip Mode:
   - Press `Alt + Shift + S`.
   - Click and drag a rectangle over any portion of the screen.
   - Upon releasing the mouse button, the isolated region will be sent to Lens for analysis.

4. Test Health Check Endpoint:
   In a separate terminal, test the Observer health endpoint:
   ```bash
   curl http://127.0.0.1:5050/status
   ```
   A successful response returns a JSON payload containing:
   ```json
   {
     "active_model": "qwen3-vl:8b",
     "capture_enabled": true,
     "disable_thinking": true,
     "installed_models": ["qwen3-vl:8b"],
     "ollama_online": true,
     "save_screenshots": false
   }
   ```
