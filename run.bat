@echo off
setlocal enabledelayedexpansion
title Lens Assistant
color 0B

echo =======================================================
echo               Lens - Local Screen AI
echo =======================================================
echo.

:: 1. Verify installation
if not exist "assistant-observer\venv\Scripts\python.exe" (
    echo [!] Environment not found. Running setup first...
    call setup.bat
    if %errorlevel% neq 0 exit /b 1
)

if not exist "assistant-electron\node_modules" (
    echo [!] Electron dependencies missing. Running setup...
    call setup.bat
    if %errorlevel% neq 0 exit /b 1
)

:: 2. Check if Ollama is running
curl -s http://127.0.0.1:11434/api/tags >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Starting Ollama local server in background...
    start /b ollama serve >nul 2>nul
    timeout /t 2 /nobreak >nul
)

:: 3. Launch Lens Desktop App
echo [*] Shortcuts:
echo     - [Alt + L]         Summon Lens HUD
echo     - [Alt + Shift + S] Snip Region
echo     - [Ctrl + Shift + P] Privacy Toggle
echo.
echo [*] Launching Lens overlay...

cd assistant-electron
call npm start
cd ..
