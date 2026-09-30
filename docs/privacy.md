# Privacy and Security Policy

Privacy is the primary engineering requirement of Lens. The application was built as an open source, zero-surveillance alternative to background screen logging tools such as Windows Recall.

This document outlines the technical measures implemented to ensure complete data security.

---

## 1. 100% Local Processing

Lens communicates only with processes running on your local machine (`127.0.0.1`):
* Electron Desktop Application (Local client)
* Flask Observer Daemon (Port 5050)
* Ollama Local Server (Port 11434)

No remote servers, cloud proxies, or third-party APIs are contacted at any time. Lens operates with full functionality on a computer that is completely disconnected from the internet.

---

## 2. On-Demand Activation vs Background Surveillance

Many existing productivity tools continuously record the screen in the background, creating persistent databases of everything you browse, write, or view.

Lens operates with a strict on-demand model:
* Screen capture only occurs when you deliberately press `Alt + L` or `Alt + Shift + S`.
* Once inference completes, the capture pipeline returns to an idle state.
* No background timers, polling routines, or continuous screen recorders exist in the codebase.

---

## 3. Ephemeral In-Memory Storage

Screen captures and extracted text are processed exclusively in volatile memory (RAM):
* Captured screen frames are stored as in-memory byte arrays.
* Once the response tokens are generated, the in-memory image buffers are released.
* Lens does not write screenshots or conversation logs to your hard drive by default.
* If you wish to save screenshots for debugging, this must be explicitly enabled in configuration (`SAVE_SCREENSHOTS=true`).

---

## 4. Active Window Isolation

When you summon Lens (`Alt + L`), it captures only the bounding box of the active application window rather than your entire multi-monitor desktop.

When using Area Snip mode (`Alt + Shift + S`), only the precise pixels inside your selected rectangle are captured. Content outside your selection is never examined.

---

## 5. Local Authentication

Every request between the Electron frontend and the Observer backend is authenticated via an encrypted shared token passed in the `x-assistant-token` HTTP header.

Any request from unauthorized local processes that lack this token is immediately rejected with an HTTP 401 Unauthorized status.

---

## 6. Hardware Privacy Killswitch

Lens includes a global privacy shortcut (`Ctrl + Shift + P` on Windows/Linux, `Cmd + Shift + P` on macOS) that toggles the capture daemon state:
* When privacy mode is active, the screen capture engine is disabled at the daemon level.
* Any trigger requests sent while privacy mode is active are rejected with an HTTP 403 Forbidden status.
* A status indicator in the HUD confirms when privacy mode is engaged.

---

## 7. Zero Telemetry and Open Source Verification

* No analytical trackers: Lens does not include Google Analytics, Mixpanel, Sentry, or any third-party tracking libraries.
* No telemetry: No usage counts, error logs, or user identifiers are collected or transmitted.
* Complete Auditability: The entire codebase is open source under the MIT License, allowing anyone to inspect every network call and system hook.
