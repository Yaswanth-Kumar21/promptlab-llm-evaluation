@echo off
title PromptLab - First Time Setup
color 0E

echo.
echo  ==============================================
echo   PromptLab - First Time Setup
echo  ==============================================
echo.
echo  This will:
echo    1. Create Python virtual environment
echo    2. Install Python dependencies
echo    3. Install Node.js dependencies
echo    4. Create .env file from template
echo.
echo  Requires: Python 3.11+ and Node.js 18+
echo.
pause

REM ── Check Python ─────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)

REM ── Check Node ───────────────────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found. Install from https://nodejs.org
    pause
    exit /b 1
)

echo.
echo  [1/4] Creating Python virtual environment...
cd /d "%~dp0backend"
if not exist ".venv" (
    python -m venv .venv
    echo  Virtual environment created.
) else (
    echo  Virtual environment already exists. Skipping.
)

echo.
echo  [2/4] Installing Python dependencies...
echo  ^(This may take 2-5 minutes - sentence-transformers is ~300MB^)
echo.
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo  [ERROR] Python dependency installation failed.
    echo  Try running manually: cd backend ^&^& .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
echo  Python dependencies installed.

echo.
echo  [3/4] Installing Node.js dependencies...
cd /d "%~dp0frontend"
call npm install --prefer-offline
if errorlevel 1 (
    echo.
    echo  [ERROR] Node dependency installation failed.
    echo  Try running manually: cd frontend ^&^& npm install
    pause
    exit /b 1
)
echo  Node dependencies installed.

echo.
echo  [4/4] Creating .env file...
cd /d "%~dp0"
if not exist "backend\.env" (
    copy ".env.example" "backend\.env" >nul
    echo  Created backend\.env from template.
    echo.
    echo  ============================================================
    echo   OPTIONAL: Add LLM API keys to backend\.env
    echo  ============================================================
    echo   The app works with the FREE Mock provider out of the box.
    echo   To use real LLMs, edit backend\.env and add:
    echo     OPENAI_API_KEY=sk-...
    echo     ANTHROPIC_API_KEY=sk-ant-...
    echo     GEMINI_API_KEY=...
    echo     MISTRAL_API_KEY=...
    echo  ============================================================
) else (
    echo  backend\.env already exists. Skipping.
)

echo.
echo  ==============================================
echo   Setup complete!
echo  ==============================================
echo.
echo   Now double-click start.bat to launch PromptLab.
echo.
pause
