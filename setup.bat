@echo off
setlocal enabledelayedexpansion
title Lens Assistant - Environment Setup
color 0B

echo =======================================================
echo          Lens Assistant - 1-Click Setup
echo =======================================================
echo.

:: 1. Check Python
echo [*] Checking Python installation...
where python >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.10+ from https://python.org and check "Add Python to PATH".
    pause
    exit /b 1
)
python --version

:: 2. Check Node.js
echo.
echo [*] Checking Node.js installation...
where node >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Node.js is not installed or not added to PATH.
    echo Please install Node.js 20+ from https://nodejs.org.
    pause
    exit /b 1
)
node --version

:: 3. Check Ollama
echo.
echo [*] Checking Ollama installation...
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Ollama CLI not found in PATH.
    echo Make sure Ollama is installed and running from https://ollama.com.
) else (
    ollama --version
)

:: 4. Setup Python Observer Backend
echo.
echo [*] Setting up Python Observer daemon...
cd assistant-observer

if not exist ".env" (
    if exist ".env.example" (
        echo [*] Initializing assistant-observer\.env from example...
        copy .env.example .env >nul
    )
)

if not exist "venv\Scripts\python.exe" (
    echo [*] Creating virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to create Python virtual environment.
        pause
        exit /b 1
    )
)

echo [*] Installing Python requirements...
call venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
call deactivate
cd ..

:: 5. Setup Electron Client
echo.
echo [*] Setting up Electron Desktop Client...
cd assistant-electron

if not exist ".env" (
    if exist ".env.example" (
        echo [*] Initializing assistant-electron\.env from example...
        copy .env.example .env >nul
    )
)

echo [*] Installing Node modules...
call npm install
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to install npm dependencies.
    pause
    exit /b 1
)
cd ..

echo.
echo =======================================================
echo          [SUCCESS] Lens is fully configured!
echo =======================================================
echo.
echo Next steps:
echo 1. Ensure Ollama is running and has your preferred model:
echo    ollama pull qwen3-vl:8b
echo 2. Launch Lens anytime by double-clicking: run.bat
echo.
pause
