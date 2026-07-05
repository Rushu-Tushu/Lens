# Troubleshooting

## Electron starts but nothing happens

Verify that the Observer backend is running before launching the Electron application.

---

## Unauthorized Error

Ensure both `.env` files use the same value for:

```text
ASSISTANT_TOKEN
```

Restart both applications after changing the environment variables.

---

## Observer returns 404

Verify that:

* `app.py` is running.
* All Flask routes are registered.
* The Observer is listening on `127.0.0.1:5050`.

---

## Ollama Connection Failed

Verify that Ollama is running.

```bash
ollama list
```

If necessary, start the model.

```bash
ollama run deepseek-r1:8b
```

---

## OCR Produces Incorrect Results

Possible causes:

* Blurry text
* Small font sizes
* Unsupported fonts
* Low-contrast windows

Ensure Tesseract OCR is correctly installed.

---

## Tesseract Not Found

Verify the installation:

```bash
tesseract --version
```

If necessary, add the Tesseract installation directory to your system PATH.

---

## Python Virtual Environment Issues

Recreate the virtual environment.

```bash
python -m venv venv
```

Activate it.

```bash
venv\Scripts\activate
```

Install the dependencies again.

```bash
pip install -r requirements.txt
```

---

## Electron Cannot Connect to the Observer

Verify that the Observer is running.

```text
http://127.0.0.1:5050
```

Also verify the following value in the Electron `.env` file:

```text
ASSISTANT_OBSERVER=http://127.0.0.1:5050
```
