# Changelog

All notable changes to the Lens project are documented in this file.

---

## Version 2.0.0 (Production Release)

This release upgrades Lens into an on-demand, multimodal desktop assistant powered by local Ollama models.

### Key Enhancements

* Real-Time Token Streaming: Implemented a Server-Sent Events (SSE) pipeline providing instant token-by-token generation with sub-300ms time-to-first-token.
* Native Multimodal Vision: Added direct support for local vision models (`qwen3-vl:8b`, `qwen2.5-vl`, `gemma-vl`, `llama3.2-vision`), passing base64 images directly to Ollama without requiring optical character recognition software.
* Ultra-Fast Fast Mode: Introduced a prefill bypass mechanism to disable time-consuming internal reasoning on vision models, reducing response latency from 30 seconds to approximately 1.2 seconds.
* Dynamic Model Switcher: Added an in-HUD dropdown menu to inspect and switch between installed Ollama vision and reasoning models on the fly.
* Persistent Conversation Thread: Built a conversational message container that retains dialogue history across multiple follow-up questions.
* Desktop Command HUD: Redesigned the overlay interface with obsidian glassmorphic styling, syntax-highlighted code blocks, and 1-click copy buttons.
* Area Snip Tool (`Alt + Shift + S`): Added a fullscreen region selector with devicePixelRatio scaling to capture precise screen regions on high-DPI displays.
* Preset Action Chips: Added 1-click prompts for `AUTO`, `DEBUG`, `EXPLAIN`, `OPTIMIZE`, and `TLDR` with intelligent context reuse.
* Collapsible Reasoning Drawer: Added a real-time thinking inspection drawer for reasoning models such as DeepSeek R1.
* Automated Daemon Orchestration: Configured Electron to manage the lifecycle of the Python observer daemon automatically.
* 1-Click Launchers: Added `setup.bat` and `run.bat` for automated environment configuration and single-click execution on Windows.

---

## Version 1.0.0 (Initial Prototype)

* Basic active window detection using pygetwindow.
* Optical character recognition pipeline using Tesseract OCR.
* Local language model integration using Ollama.
* Frameless Electron desktop window overlay.
* Basic token authentication.