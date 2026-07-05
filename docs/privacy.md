# Privacy

Privacy is a core design principle of Lens.

All processing happens locally on your machine. No screenshots, extracted text, or AI prompts are sent to external services.

## Local Processing

Lens communicates only with services running on your local computer.

* Electron Desktop Application
* Flask Observer
* Ollama Local Server

No internet connection is required after the required software and models are installed.

---

## Active Window Only

Lens captures only the currently active application window.

It does not continuously record your desktop or monitor every application running on your system.

---

## Screenshots

Captured screenshots are processed in memory.

By default:

* Screenshots are **not** saved to disk.
* Screenshots exist only for the duration required to perform OCR and AI analysis.

Saving screenshots must be explicitly enabled.

---

## Local Communication

Electron communicates with the Observer using HTTP over:

```text
http://127.0.0.1:5050
```

Communication never leaves the local machine.

---

## Authentication

All requests from Electron to the Observer include an `x-assistant-token` header.

The Observer rejects requests with missing or invalid tokens.

---

## Privacy Toggle

Lens includes a privacy toggle that temporarily disables screen capture.

When disabled:

* No screenshots are captured.
* No OCR is performed.
* No requests are sent to the language model.

---

## Data Storage

Lens does not permanently store:

* Screenshots
* OCR results
* AI prompts
* AI responses

Unless explicitly configured, all data remains in memory only during processing.
