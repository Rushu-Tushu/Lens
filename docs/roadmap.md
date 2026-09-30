# Roadmap

This document outlines completed milestones and planned enhancements for Lens.

---

## Completed in Release 2.0.0

* Real-time token streaming using Server-Sent Events (SSE).
* Native Multimodal Vision support for local models (`qwen3-vl:8b`, `qwen2.5-vl`, `gemma-vl`, `llama3.2-vision`).
* Ultra-Fast Fast Mode bypass to reduce vision model latency to approximately 1.2 seconds.
* In-HUD dynamic model switcher allowing users to inspect and switch installed Ollama models without restarting.
* Desktop Command HUD with glassmorphic styling, syntax-highlighted code blocks, and 1-click copy buttons.
* Area Snip tool (`Alt + Shift + S`) with automatic high-DPI scaling across display configurations.
* Multi-turn conversational chat thread preserving complete conversation history.
* Preset action chips (`AUTO`, `DEBUG`, `EXPLAIN`, `OPTIMIZE`, `TLDR`) with context caching to avoid duplicate screen captures.
* Deliberation drawer supporting real-time thinking inspection for reasoning models such as DeepSeek R1.
* Automatic daemon orchestration: Electron automatically starts and terminates the Python observer daemon.
* Global keyboard summon shortcut (`Alt + L`).
* 1-Click automated Windows launcher scripts (`setup.bat` and `run.bat`).

---

## Planned Future Enhancements

* Standalone 1-click installer: Bundled `.exe` package using PyInstaller and electron-builder.
* Local voice queries: Voice-to-text integration powered by a local Whisper model.
* Multi-monitor enhancements: Active display auto-detection for mixed multi-monitor orientations.
* Conversation export: Searchable history archive with Markdown and JSON export capabilities.
* Editor companion extensions: Native VS Code and JetBrains plugins.
* Local model manager: In-HUD downloader to pull new models directly from the Ollama registry.
