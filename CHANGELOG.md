# Changelog

## v2.0.0 (Production & Public Release)

Major release transforming Lens into a high-performance, multimodal desktop AI companion.

### New Features & Enhancements
- **Real-Time Token Streaming**: Upgraded to Server-Sent Events (SSE) pipeline for instant token-by-token generation with sub-300ms time-to-first-token.
- **Multimodal Vision Integration**: Added native support for local vision models (`qwen3-vl`, `qwen2.5-vl`, `gemma-vl`, `llama3.2-vision`) passing base64 images directly, eliminating mandatory Tesseract OCR installation.
- **Ultra-Fast Zero-Thinking Mode**: Prefill and parameter bypass to disable time-consuming internal reasoning on vision models, slashing response latency from ~30s down to ~1s.
- **Dynamic Model Switcher**: In-HUD dropdown to quickly inspect and switch between installed Ollama vision and reasoning models.
- **Persistent Conversation Thread**: Multi-turn conversational chat with history retention, distinct user message cards, and real-time streaming blocks.
- **Raycast-Grade Command HUD**: Translucent obsidian glassmorphism overlay with Markdown rendering, dynamic typing cursor, and pulse status indicator.
- **Area Snip Tool (`Alt+Shift+S`)**: Custom screen selection overlay with high-DPI devicePixelRatio scaling allowing users to drag and isolate specific screen regions.
- **Preset Action Chips**: Instant 1-click prompts for `Fix Error`, `Explain`, `Optimize`, and `TL;DR` with smart context reuse.
- **Reasoning Drawer**: Collapsible thinking drawer for DeepSeek R1 and reasoning models.
- **Syntax Highlighting & 1-Click Copy**: Offline code blocks with language auto-detection and dedicated copy buttons.
- **Backend Auto-Orchestration**: Electron automatically launches and terminates the Python observer daemon.
- **Global Summon Shortcut**: Default `Alt+L` hotkey for instant summon.

---

## v1.0.0

Initial public release.

### Features
- Active window analysis
- OCR with Tesseract
- Local LLM integration via Ollama
- Electron desktop overlay
- Privacy-first architecture