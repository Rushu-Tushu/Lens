# Installation

This guide explains how to set up and run Lens on a Windows machine.

## Prerequisites

Install the following software before continuing:

| Software             | Purpose                             |
| -------------------- | ----------------------------------- |
| Python 3.10 or later | Observer backend                    |
| Node.js 20 or later  | Electron desktop application        |
| Git                  | Clone the repository                |
| Ollama               | Run the local language model        |
| Tesseract OCR        | Extract text from the active window |

---

# 1. Clone the Repository

```bash
git clone https://github.com/Rushu-Tushu/Lens.git
cd Lens
```

---

# 2. Install Ollama

Download and install Ollama from:

https://ollama.com/download

After installation, pull the desired model.

Example:

```bash
ollama pull deepseek-r1:8b
```

You can replace the model with any Ollama-compatible model by updating the configuration.

---

# 3. Install Tesseract OCR

Download and install Tesseract OCR.

During installation, remember the installation path (for example, `C:\Program Files\Tesseract-OCR`).

If Tesseract is not added to your system PATH automatically, add it manually.

Verify the installation:

```bash
tesseract --version
```

---

# 4. Configure the Observer

Navigate to the Observer directory.

```bash
cd assistant-observer
```

Create a virtual environment.

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
venv\Scripts\activate
```

Install the required packages.

```bash
pip install -r requirements.txt
```

Create a `.env` file.

```env
ASSISTANT_TOKEN=local_secret_token
OLLAMA_URL=http://127.0.0.1:11434/api/generate
```

---

# 5. Configure the Electron Application

Open another terminal.

```bash
cd assistant-electron
```

Install dependencies.

```bash
npm install
```

Create a `.env` file.

```env
ASSISTANT_OBSERVER=http://127.0.0.1:5050
ASSISTANT_TOKEN=local_secret_token
```

---

# 6. Start Lens

## Terminal 1

Start Ollama.

```bash
ollama run deepseek-r1:8b
```

---

## Terminal 2

Start the Observer.

```bash
cd assistant-observer
venv\Scripts\activate
python app.py
```

Expected output:

```text
* Running on http://127.0.0.1:5050
```

---

## Terminal 3

Start the Electron application.

```bash
cd assistant-electron
npm start
```

Expected output:

```text
Electron app is ready
```

A system tray icon should now appear.

---

# Verifying the Installation

To verify that the Observer is running correctly, open another terminal and execute:

```bash
curl -X POST http://127.0.0.1:5050/analyze ^
-H "x-assistant-token: local_secret_token"
```

A successful response returns JSON similar to:

```json
{
  "title": "...",
  "summary": "...",
  "assistant": "..."
}
```

---

# Running Lens

1. Ensure Ollama is running.
2. Start the Observer.
3. Launch the Electron application.
4. Open any application containing visible text.
5. Click **Ask Assistant** from the system tray.
6. Read the generated response in the desktop overlay.

---

# Common Setup Issues

## Tesseract not found

Ensure Tesseract is installed and available in your system PATH.

Verify with:

```bash
tesseract --version
```

---

## Ollama connection failed

Ensure Ollama is running.

Verify with:

```bash
ollama list
```

---

## Unauthorized error

Confirm that both `.env` files use the same value for:

```text
ASSISTANT_TOKEN
```

---

## Electron cannot connect to the Observer

Ensure the Observer is running on:

```text
http://127.0.0.1:5050
```

and that the Electron `.env` file contains the correct `ASSISTANT_OBSERVER` value.
