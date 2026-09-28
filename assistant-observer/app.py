# assistant-observer/app.py
from flask import Flask, request, jsonify, Response, stream_with_context
import mss, io, time, hashlib, os, base64
from PIL import Image
import pytesseract
import requests
import json
import html
import re

from dotenv import load_dotenv
load_dotenv()

# Active window detection
try:
    import pygetwindow as gw
except Exception:
    gw = None

APP_PORT = int(os.environ.get("PORT", 5050))
ASSISTANT_TOKEN = os.environ.get("ASSISTANT_TOKEN", "local_secret_token")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-vl:8b")

app = Flask(__name__)     

# State and session storage
_state = {
    "capture_enabled": True,
    "save_screenshots": False,
    "save_folder": os.path.join(os.getcwd(), "saved_screenshots"),
    "active_model": OLLAMA_MODEL,
    "disable_thinking": True  # Default to False thinking for maximum speed
}
_ocr_cache = {}
_sessions = {}  # session_id -> { "window_title": str, "ocr_snippet": str, "image_b64": str, "is_vision": bool, "history": list }

VISION_KEYWORDS = ["vl", "vision", "qwen", "gemma", "llava", "moondream", "minicpm"]

def set_dpi_awareness():
    """Ensure process is Per-Monitor DPI Aware on Windows so coordinates match mss."""
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

set_dpi_awareness()

def is_vision_model(model_name: str) -> bool:
    """Check if model name matches known vision-capable model families."""
    if not model_name:
        return False
    name = model_name.lower()
    return any(k in name for k in VISION_KEYWORDS)

def image_to_base64(img: Image.Image) -> str:
    """Convert PIL image to base64 string for Ollama vision models."""
    bio = io.BytesIO()
    # JPEG with 85 quality gives great speed and keeps resolution sharp for vision models
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.save(bio, format="JPEG", quality=85)
    return base64.b64encode(bio.getvalue()).decode('utf-8')

def clean_assistant_text(s: str) -> str:
    """Clean model output for display: remove internal tokens, decode entities, trim whitespace."""
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"<\/?think>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>\n]{1,30}>", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    s = "".join(ch for ch in s if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return s

def ensure_default_desktop():
    """Ensure the current thread is attached to the interactive 'default' desktop on Windows."""
    try:
        if os.name == 'nt':
            import ctypes
            user32 = ctypes.windll.user32
            hDesk = user32.OpenDesktopW("default", 0, False, 0x01FF) # GENERIC_ALL
            if hDesk:
                user32.SetThreadDesktop(hDesk)
    except Exception:
        pass

def get_active_window_info():
    """
    Retrieve title and bounding box of currently active window.
    If the foreground window is Lens or a shell utility, walks down the z-order to find
    the active application window underneath.
    """
    ensure_default_desktop()
    
    # 1. Try win32gui GetForegroundWindow directly
    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            t = win32gui.GetWindowText(hwnd).strip()
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            if w > 60 and h > 60 and "lens" not in t.lower() and t not in ["Program Manager", "Settings"]:
                return t, (rect[0], rect[1], w, h)
    except Exception:
        pass

    # 2. If foreground window is Lens or HUD, enumerate visible windows to get the top app
    try:
        import win32gui
        top_apps = []
        def enum_cb(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                t = win32gui.GetWindowText(hwnd).strip()
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                if w > 100 and h > 100 and t:
                    if "lens" not in t.lower() and t not in ["Program Manager", "Settings"]:
                        top_apps.append((t, (rect[0], rect[1], w, h)))
            return True
        win32gui.EnumWindows(enum_cb, None)
        if top_apps:
            return top_apps[0]
    except Exception:
        pass

    # 3. Fallback to pygetwindow
    try:
        if gw:
            w = gw.getActiveWindow()
            if w and w.width > 60 and w.height > 60:
                title = (w.title or "window").strip()
                if "lens" not in title.lower():
                    bbox = (int(w.left), int(w.top), int(w.width), int(w.height))
                    return title, bbox
    except Exception:
        pass

    return "Desktop / Primary Screen", None

def capture_window(bbox=None):
    """Capture screen region or full primary monitor."""
    ensure_default_desktop()
    with mss.mss() as sct:
        if bbox:
            left, top, width, height = bbox
            region = {"left": max(0, int(left)), "top": max(0, int(top)), "width": max(10, int(width)), "height": max(10, int(height))}
            sshot = sct.grab(region)
        else:
            # monitors[1] is the primary physical display; monitors[0] is virtual span
            mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sshot = sct.grab(mon)
        img = Image.frombytes("RGB", sshot.size, sshot.rgb)
        return img

def image_hash_bytes(img):
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return hashlib.sha256(bio.getvalue()).hexdigest()

def ocr_with_cache(img, max_chars=3500):
    """OCR the image with short cache for text models."""
    key = image_hash_bytes(img)
    now = time.time()
    cached = _ocr_cache.get(key)
    if cached and now - cached[0] < 1.0:
        return cached[1]

    custom_config = r'--oem 3 --psm 6'
    try:
        text = pytesseract.image_to_string(img, config=custom_config)
    except Exception:
        try:
            text = pytesseract.image_to_string(img)
        except Exception as ocr_err:
            text = f"[OCR unavailable: {ocr_err}]"
    text = text.strip()[:max_chars]
    _ocr_cache[key] = (now, text)
    if len(_ocr_cache) > 100:
        oldest = sorted(_ocr_cache.items(), key=lambda kv: kv[1][0])[0][0]
        _ocr_cache.pop(oldest, None)
    return text

def build_prompt_for_mode(mode: str, window_title: str, context_text: str = "", custom_prompt: str = "") -> str:
    """Build tailored prompts depending on the user's intent."""
    if custom_prompt:
        return (
            f"You are Lens, an elite AI screen assistant. The user is looking at: '{window_title}'.\n"
            f"Screen context:\n{context_text}\n\n"
            f"User request: {custom_prompt}\n"
            "Provide a concise, direct, helpful answer. Format response in Markdown."
        )

    if mode == "fix":
        return (
            f"You are Lens, an elite debugging assistant. Window title: '{window_title}'.\n"
            f"Visible screen content:\n{context_text}\n\n"
            "Diagnose the error or bug visible on the screen. Provide:\n"
            "1. **Root Cause** (1-2 sentences)\n"
            "2. **The Fix** (copy-pasteable code block or shell command)\n"
            "3. **Prevention Tip** (1 sentence)\n"
            "Be direct, accurate, and concise. Use Markdown."
        )
    elif mode == "explain":
        return (
            f"You are Lens, an expert explainer. Window title: '{window_title}'.\n"
            f"Visible content:\n{context_text}\n\n"
            "Provide:\n"
            "1. **Executive Summary** (1 sentence)\n"
            "2. **Key Concepts / Logic** (bullet points explaining what this does)\n"
            "3. **Key Takeaway or Caveat**\n"
            "Format in Markdown with clean formatting."
        )
    elif mode == "optimize":
        return (
            f"You are Lens, a staff-level code and productivity optimizer. Window title: '{window_title}'.\n"
            f"Visible code/content:\n{context_text}\n\n"
            "Analyze the visible code or workflow. Provide:\n"
            "1. **Top Optimization / Smell Found**\n"
            "2. **Optimized Solution** (with code diff or improved version)\n"
            "3. **Expected Impact** (performance, readability, or reliability)\n"
            "Format in Markdown."
        )
    elif mode == "tldr":
        return (
            f"You are Lens. Window title: '{window_title}'.\n"
            f"Visible content:\n{context_text}\n\n"
            "Provide an instant **3-bullet TL;DR** of what is currently on the screen. Max 60 words total."
        )
    else:  # General / Auto-detect
        is_code = any(tok in context_text for tok in [";", "{", "}", "def ", "int ", "#include", "class ", "=>", "function ", "import ", "const "])
        if is_code:
            return (
                f"You are Lens, an intelligent coding companion. Window title: '{window_title}'.\n"
                f"Visible code:\n```\n{context_text[:1500]}\n```\n\n"
                "Provide:\n"
                "1. **What this code does** (1-2 sentences)\n"
                "2. **Key observation / improvement**\n"
                "3. **Quick copyable tip or fix** (if applicable)\n"
                "Keep formatting clean and modern in Markdown."
            )
        else:
            return (
                f"You are Lens, a context-aware desktop companion. Window title: '{window_title}'.\n"
                f"Visible screen text:\n\"\"\"\n{context_text[:1500]}\n\"\"\"\n\n"
                "Provide:\n"
                "1. **Summary** (2-3 sentences explaining what's happening)\n"
                "2. **Actionable suggestion or next step**\n"
                "Format in clean Markdown."
            )

def stream_ollama(prompt: str, images: list = None, model: str = None, timeout: int = 180):
    """
    Stream tokens from Ollama chat API.
    Handles thinking tokens (Qwen-VL / DeepSeek) and content tokens.
    Supports turning off thinking for qwen3-vl:8b and other models.
    Yields dicts with {"type": "content"|"think", "text": "...", "done": bool}.
    """
    target_model = model or _state.get("active_model") or OLLAMA_MODEL
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"

    messages = [{"role": "user", "content": prompt}]
    if images:
        messages[0]["images"] = images

    # Check if thinking should be disabled (user requested for qwen3-vl:8b or state flag)
    should_disable_thinking = _state.get("disable_thinking", True)
    if "qwen" in target_model.lower():
        should_disable_thinking = True

    # For qwen3-vl:8b, inject assistant prefill <think>\n</think> to completely bypass 30s+ reasoning
    if should_disable_thinking:
        messages.append({"role": "assistant", "content": "<think>\n</think>"})

    payload = {
        "model": target_model,
        "messages": messages,
        "stream": True,
        "options": {
            "num_ctx": 4096,
            "temperature": 0.2,
            "top_p": 0.9
        }
    }
    if should_disable_thinking:
        payload["think"] = False

    in_think_tag = False
    try:
        resp = requests.post(url, json=payload, stream=True, timeout=timeout)
        resp.raise_for_status()

        for line in resp.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode('utf-8'))
            except Exception:
                continue

            msg = chunk.get("message", {})
            think_piece = msg.get("thinking", "") or chunk.get("thinking", "")
            content_piece = msg.get("content", "") or chunk.get("response", "")
            done = chunk.get("done", False)

            # Check for inline <think> tags (e.g. DeepSeek R1 or models printing raw tags)
            if "<think>" in content_piece:
                in_think_tag = True
                content_piece = content_piece.replace("<think>", "")
            if "</think>" in content_piece:
                in_think_tag = False
                content_piece = content_piece.replace("</think>", "")

            if think_piece and not should_disable_thinking:
                yield {
                    "type": "think",
                    "text": think_piece,
                    "done": False
                }

            if content_piece and not in_think_tag:
                yield {
                    "type": "content",
                    "text": content_piece,
                    "done": False
                }

            if done:
                yield {"type": "content", "text": "", "done": True}
                break

    except Exception as e:
        yield {"type": "error", "text": str(e), "done": True}

# ==================== REST & STREAMING ROUTES ====================

def resolve_model(model_override=None):
    if model_override:
        return model_override
    active = _state.get("active_model") or OLLAMA_MODEL
    try:
        tags_resp = requests.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=1)
        if tags_resp.status_code == 200:
            installed = [m.get("name") for m in tags_resp.json().get("models", [])]
            if installed and not any(active in m or m in active for m in installed):
                # Pick installed vision model if available (e.g. qwen3-vl:8b)
                candidates = [m for m in installed if is_vision_model(m)]
                active = candidates[0] if candidates else installed[0]
                _state["active_model"] = active
    except Exception:
        pass
    return active

@app.route("/status", methods=["GET"])
def get_status():
    """Health check route returning Ollama status and installed models."""
    ollama_online = False
    models = []
    try:
        tags_resp = requests.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=2)
        if tags_resp.status_code == 200:
            ollama_online = True
            data = tags_resp.json()
            models = [m.get("name") for m in data.get("models", [])]
    except Exception:
        pass

    active = resolve_model()

    return jsonify({
        "capture_enabled": _state["capture_enabled"],
        "active_model": active,
        "ollama_online": ollama_online,
        "installed_models": models,
        "save_screenshots": _state["save_screenshots"],
        "disable_thinking": _state["disable_thinking"]
    })

@app.route("/analyze/stream", methods=["POST"])
def analyze_stream():
    """
    Main streaming analysis endpoint using Server-Sent Events (SSE).
    Streams tokens in real time directly to Electron.
    """
    token = request.headers.get("x-assistant-token") or request.args.get("token")
    if token != ASSISTANT_TOKEN:
        return jsonify({"error": "unauthorized"}), 401

    if not _state["capture_enabled"]:
        return jsonify({"error": "capture_disabled"}), 403

    body = request.get_json(silent=True) or {}
    mode = body.get("mode", "general")
    custom_prompt = body.get("custom_prompt", "")
    bbox = body.get("bbox")  # Optional [left, top, width, height] for Snip mode
    session_id = body.get("session_id", "default_session")
    model_override = body.get("model")
    reuse_context = body.get("reuse_context", False)

    active_model = resolve_model(model_override)
    is_vision = is_vision_model(active_model)

    existing_session = _sessions.get(session_id)
    if reuse_context and existing_session and existing_session.get("image_b64"):
        # Reuse existing screen context to prevent re-capturing the HUD itself
        title = existing_session.get("window_title", "Current Window")
        images_payload = [existing_session["image_b64"]] if is_vision else None
        ocr_snippet = existing_session.get("ocr_snippet", "")
        saved_path = existing_session.get("saved_path")
        if is_vision:
            prompt = build_prompt_for_mode(mode, title, context_text="[See attached image of the window]", custom_prompt=custom_prompt)
        else:
            prompt = build_prompt_for_mode(mode, title, context_text=ocr_snippet, custom_prompt=custom_prompt)
    else:
        # 1. Fresh screen capture
        if bbox:
            title = "Snip Selection"
        else:
            title, bbox = get_active_window_info()

        img = capture_window(bbox)

        # 2. Downscale if very large
        max_w = 1920
        if img.width > max_w:
            ratio = max_w / img.width
            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

        # 3. Vision vs OCR routing
        images_payload = None
        ocr_snippet = ""

        if is_vision:
            # Multimodal: Pass image directly to Ollama vision model
            images_payload = [image_to_base64(img)]
            prompt = build_prompt_for_mode(mode, title, context_text="[See attached image of the window]", custom_prompt=custom_prompt)
        else:
            # Text-only model: Use Tesseract OCR
            ocr_text = ocr_with_cache(img, max_chars=3500)
            ocr_snippet = ocr_text[:1200]
            prompt = build_prompt_for_mode(mode, title, context_text=ocr_text, custom_prompt=custom_prompt)

        # Save screenshot if configured
        saved_path = None
        if _state["save_screenshots"]:
            os.makedirs(_state["save_folder"], exist_ok=True)
            ts = int(time.time())
            fname = f"screenshot_{ts}.png"
            saved_path = os.path.join(_state["save_folder"], fname)
            img.save(saved_path)

        # Store in session state for follow-up questions
        _sessions[session_id] = {
            "window_title": title,
            "ocr_snippet": ocr_snippet,
            "image_b64": images_payload[0] if images_payload else None,
            "is_vision": is_vision,
            "saved_path": saved_path,
            "history": [{"role": "user", "prompt": prompt}]
        }

    def generate_sse():
        meta = {
            "title": title,
            "mode": mode,
            "model": active_model,
            "is_vision": is_vision,
            "saved_path": saved_path
        }
        yield f"event: metadata\ndata: {json.dumps(meta)}\n\n"

        full_reply = []
        think_reply = []
        for item in stream_ollama(prompt, images=images_payload, model=active_model):
            if item.get("type") == "error":
                yield f"event: error\ndata: {json.dumps({'error': item['text']})}\n\n"
                return
            if item.get("done"):
                yield f"event: done\ndata: {json.dumps({'done': True, 'full_reply': ''.join(full_reply), 'think_reply': ''.join(think_reply)})}\n\n"
                return
            
            text_piece = item.get("text", "")
            if item.get("type") == "think":
                think_reply.append(text_piece)
                yield f"event: think\ndata: {json.dumps({'text': text_piece})}\n\n"
            elif item.get("type") == "content":
                full_reply.append(text_piece)
                yield f"event: chunk\ndata: {json.dumps(item)}\n\n"

    return Response(stream_with_context(generate_sse()), mimetype="text/event-stream")

@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    """
    Multi-turn follow-up chat with the screen context.
    """
    token = request.headers.get("x-assistant-token") or request.args.get("token")
    if token != ASSISTANT_TOKEN:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id", "default_session")
    user_message = body.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "empty_message"}), 400

    session = _sessions.get(session_id, {})
    window_title = session.get("window_title", "Current Window")
    ocr_snippet = session.get("ocr_snippet", "")
    image_b64 = session.get("image_b64")
    is_vision = session.get("is_vision", False)
    active_model = resolve_model(body.get("model"))

    prompt = (
        f"You are Lens. The user is asking a follow-up question regarding the active window '{window_title}'.\n"
        f"Screen context:\n{ocr_snippet}\n\n"
        f"Follow-up question: {user_message}\n"
        "Provide a direct, helpful response in clean Markdown."
    )

    images_payload = [image_b64] if (is_vision and image_b64) else None

    # Track in history
    if "history" in session:
        session["history"].append({"role": "user", "prompt": user_message})

    def generate_sse():
        yield f"event: metadata\ndata: {json.dumps({'type': 'chat', 'title': window_title, 'model': active_model})}\n\n"
        full_reply = []
        think_reply = []
        for item in stream_ollama(prompt, images=images_payload, model=active_model):
            if item.get("type") == "error":
                yield f"event: error\ndata: {json.dumps({'error': item['text']})}\n\n"
                return
            if item.get("done"):
                if "history" in session:
                    session["history"].append({"role": "assistant", "reply": "".join(full_reply)})
                yield f"event: done\ndata: {json.dumps({'done': True, 'full_reply': ''.join(full_reply), 'think_reply': ''.join(think_reply)})}\n\n"
                return
            
            text_piece = item.get("text", "")
            if item.get("type") == "think":
                think_reply.append(text_piece)
                yield f"event: think\ndata: {json.dumps({'text': text_piece})}\n\n"
            elif item.get("type") == "content":
                full_reply.append(text_piece)
                yield f"event: chunk\ndata: {json.dumps(item)}\n\n"

    return Response(stream_with_context(generate_sse()), mimetype="text/event-stream")

@app.route("/toggle_privacy", methods=["POST"])
def toggle_privacy():
    token = request.headers.get("x-assistant-token") or request.args.get("token")
    if token != ASSISTANT_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    _state["capture_enabled"] = not _state["capture_enabled"]
    return jsonify({"capture_enabled": _state["capture_enabled"]})

@app.route("/config", methods=["POST"])
def config():
    token = request.headers.get("x-assistant-token") or request.args.get("token")
    if token != ASSISTANT_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    if "save_screenshots" in body:
        _state["save_screenshots"] = bool(body["save_screenshots"])
    if "save_folder" in body:
        _state["save_folder"] = str(body["save_folder"])
    if "active_model" in body:
        _state["active_model"] = str(body["active_model"])
    if "disable_thinking" in body:
        _state["disable_thinking"] = bool(body["disable_thinking"])
    return jsonify({"ok": True, "state": _state})

@app.route("/analyze", methods=["POST"])
def analyze_legacy():
    """Non-streaming fallback endpoint."""
    token = request.headers.get("x-assistant-token") or request.args.get("token")
    if token != ASSISTANT_TOKEN:
        return jsonify({"error": "unauthorized"}), 401

    if not _state["capture_enabled"]:
        return jsonify({"error": "capture_disabled"}), 403

    title, bbox = get_active_window_info()
    img = capture_window(bbox)
    ocr_text = ocr_with_cache(img, max_chars=3000)
    prompt = build_prompt_for_mode("general", title, ocr_text)

    full_text = []
    for chunk in stream_ollama(prompt, model=_state["active_model"]):
        if chunk.get("type") == "content":
            full_text.append(chunk.get("text", ""))

    reply = "".join(full_text)
    clean_reply = clean_assistant_text(reply)
    summary = clean_reply.splitlines()[0] if clean_reply else "Summary"

    return jsonify({
        "title": title,
        "ocr_snippet": ocr_text[:1000],
        "assistant": clean_reply,
        "summary": summary[:150]
    })

if __name__ == "__main__":
    print(f"[*] Lens Observer daemon starting on 127.0.0.1:{APP_PORT}")
    app.run(host="127.0.0.1", port=APP_PORT, threaded=True)
