# assistant-observer/app.py
from flask import Flask, request, jsonify
import mss, io, time, hashlib, os
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

APP_PORT = 5050
ASSISTANT_TOKEN = os.environ.get("ASSISTANT_TOKEN")
OLLAMA_URL = os.environ.get("OLLAMA_URL")

app = Flask(__name__)

# In-memory state and OCR cache
_state = {
    "capture_enabled": True,
    "save_screenshots": False,
    "save_folder": os.path.join(os.getcwd(), "saved_screenshots")
}
_ocr_cache = {}

def clean_assistant_text(s: str) -> str:
    """Clean model output for display: remove internal tokens, decode entities, trim whitespace."""
    if not s:
        return ""
    # decode HTML entities and unicode escapes
    s = html.unescape(s)
    # remove model internal markers like <think> ... </think>
    s = re.sub(r"<\/?think>", "", s, flags=re.IGNORECASE)
    # remove other angle-bracketed tokens (e.g., <...>) that look internal
    s = re.sub(r"<[^>\n]{1,30}>", "", s)
    # normalize whitespace
    s = re.sub(r"\s{2,}", " ", s).strip()
    # remove control chars except common whitespace (tab/newline)
    s = "".join(ch for ch in s if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return s

def get_active_window_info():
    try:
        if gw:
            w = gw.getActiveWindow()
            if w and w.width > 0 and w.height > 0:
                title = w.title or "window"
                bbox = (int(w.left), int(w.top), int(w.width), int(w.height))
                return title, bbox
    except Exception:
        pass
    return "unknown", None

def capture_window(bbox):
    with mss.mss() as sct:
        if bbox:
            left, top, width, height = bbox
            region = {"left": left, "top": top, "width": width, "height": height}
            sshot = sct.grab(region)
        else:
            sshot = sct.grab(sct.monitors[0])
        img = Image.frombytes("RGB", sshot.size, sshot.rgb)
        return img

def image_hash_bytes(img):
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    b = bio.getvalue()
    return hashlib.sha256(b).hexdigest()

def ocr_with_cache(img, max_chars=3000):
    """
    OCR the image with a short cache to avoid repeated OCR of identical frames.
    Uses a Tesseract config tuned for single-column text/code (better for code).
    """
    key = image_hash_bytes(img)
    now = time.time()
    cached = _ocr_cache.get(key)
    if cached and now - cached[0] < 1.0:
        return cached[1]

    # Tesseract config: OEM 3 (default/NN), PSM 6 (assume a block of text)
    custom_config = r'--oem 3 --psm 6'
    try:
        text = pytesseract.image_to_string(img, config=custom_config)
    except Exception:
        # fallback to default if custom config fails
        text = pytesseract.image_to_string(img)
    text = text.strip()
    # trim to max_chars to avoid huge prompts
    text = text[:max_chars]
    _ocr_cache[key] = (now, text)
    if len(_ocr_cache) > 200:
        oldest = sorted(_ocr_cache.items(), key=lambda kv: kv[1][0])[0][0]
        _ocr_cache.pop(oldest, None)
    return text

def call_ollama(prompt, max_tokens=400, temperature=0.1, timeout=180):
    """
    Call Ollama generate endpoint. Handles both single-json and
    newline-delimited JSON streaming responses. Returns the full
    concatenated textual response.
    """
    payload = {
        "model": "deepseek-r1:8b",
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    # Use a streaming-safe request; read the full text then try to parse.
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout, stream=True)
    r.raise_for_status()

    # Read all bytes as text
    raw = r.text

    # First try: the endpoint returned a single JSON object
    try:
        parsed = json.loads(raw)
        # Common Ollama single response keys: "response" or nested choices
        if isinstance(parsed, dict):
            # If it has a top-level 'response' field, return it
            if "response" in parsed and isinstance(parsed["response"], str):
                return parsed["response"]
            # If it has choices similar to openai, try to extract text
            if "choices" in parsed:
                choice = parsed["choices"][0]
                if isinstance(choice, dict):
                    msg = choice.get("message", {})
                    if isinstance(msg, dict) and "content" in msg:
                        return msg["content"]
                    for k in ("text", "response"):
                        if k in choice and isinstance(choice[k], str):
                            return choice[k]
        # fallback: return raw if nothing found
        return raw
    except Exception:
        # Not a single JSON object. Try NDJSON / streaming lines.
        pieces = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                # ignore non-json lines
                continue
            # typical stream chunk contains 'response' string pieces
            if "response" in obj and isinstance(obj["response"], str):
                pieces.append(obj["response"])
            elif "text" in obj and isinstance(obj["text"], str):
                pieces.append(obj["text"])
            elif "choices" in obj and isinstance(obj["choices"], list):
                ch = obj["choices"][0]
                if isinstance(ch, dict):
                    msg = ch.get("message", {})
                    if isinstance(msg, dict) and "content" in msg:
                        pieces.append(msg["content"])
                    elif "text" in ch and isinstance(ch["text"], str):
                        pieces.append(ch["text"])
        combined = "".join(pieces).strip()
        if combined:
            return combined
        return raw

@app.route("/analyze", methods=["POST"])
def analyze():
    token = request.headers.get("x-assistant-token") or request.args.get("token")
    if token != ASSISTANT_TOKEN:
        return jsonify({"error": "unauthorized"}), 401

    if not _state["capture_enabled"]:
        return jsonify({"error": "capture_disabled"}), 403

    title, bbox = get_active_window_info()
    img = capture_window(bbox)

    # downscale if too wide to speed OCR
    max_w = 1600
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((int(img.width*ratio), int(img.height*ratio)), Image.LANCZOS)

    # OCR (cached)
    ocr_text = ocr_with_cache(img, max_chars=3000)

    # build a careful prompt (instruct the model to avoid internal tokens)
    is_code = any(tok in ocr_text for tok in [";", "{", "}", "def ", "int ", "#include", "class ", "=>", "function", "var "])

    if is_code:
        prompt = (
            "You are a concise coding assistant. DO NOT include any internal tokens like <think> or XML/HTML. "
            "Return plain text only. Provide: (1) a 1-line summary, (2) a short line-by-line explanation of the code, "
            "(3) one short actionable improvement. Keep overall output under 500 tokens.\n\n"
            f"Window title: {title}\nVisible code (first 1200 chars):\n```{ocr_text[:1200]}```\n"
        )
    else:
        prompt = (
            "You are a concise assistant. DO NOT include any internal tokens like <think> or XML/HTML. "
            "Return plain text only. Provide: (1) a 30-60 word summary, (2) one useful action the user can take.\n\n"
            f"Window title: {title}\nVisible text (first 1200 chars):\n\"\"\"{ocr_text[:1200]}\"\"\"\n"
        )

    try:
        assistant_reply = call_ollama(prompt)
    except Exception as e:
        return jsonify({"error": "ollama_error", "detail": str(e)}), 500

    # Clean the assistant text for display
    assistant_reply = clean_assistant_text(assistant_reply)

    # derive a short summary to show first in the popup (first non-empty line or truncated)
    first_line = ""
    for ln in assistant_reply.splitlines():
        ln = ln.strip()
        if ln:
            first_line = ln
            break
    if not first_line:
        first_line = (assistant_reply[:160] + "...") if len(assistant_reply) > 160 else assistant_reply
    summary = first_line if len(first_line) <= 160 else (first_line[:157] + "...")

    saved_path = None
    if _state["save_screenshots"]:
        os.makedirs(_state["save_folder"], exist_ok=True)
        ts = int(time.time())
        fname = f"screenshot_{ts}.png"
        path = os.path.join(_state["save_folder"], fname)
        img.save(path)
        saved_path = path

    return jsonify({
        "title": title,
        "ocr_snippet": ocr_text[:1000],
        "assistant": assistant_reply,
        "summary": summary,
        "saved_path": saved_path
    })

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
    body = request.get_json() or {}
    if "save_screenshots" in body:
        _state["save_screenshots"] = bool(body["save_screenshots"])
    if "save_folder" in body:
        _state["save_folder"] = str(body["save_folder"])
    return jsonify({"ok": True, "state": _state})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=APP_PORT)
