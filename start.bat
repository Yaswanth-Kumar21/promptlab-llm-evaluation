@echo off
title PromptLab Launcher
color 0A

echo.
echo  ==============================================
echo   PromptLab - LLM Prompt Engineering Platform
echo  ==============================================
echo.

REM ── Check .env exists ────────────────────────────────────────────────────
if not exist "%~dp0backend\.env" (
    echo  [SETUP] .env not found. Copying from .env.example...
    copy "%~dp0.env.example" "%~dp0backend\.env" >nul
    echo  [SETUP] Created backend\.env with default settings.
    echo  [INFO]  Edit backend\.env to add LLM API keys ^(optional^).
    echo          The Mock provider works without any keys.
    echo.
)

REM ── Check venv exists ────────────────────────────────────────────────────
if not exist "%~dp0backend\.venv\Scripts\python.exe" (
    echo  [ERROR] Python virtual environment not found.
    echo          Run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM ── Check node_modules exists ────────────────────────────────────────────
if not exist "%~dp0frontend\node_modules" (
    echo  [ERROR] Node modules not found.
    echo          Run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM ── Start Backend ────────────────────────────────────────────────────────
echo  [1/2] Starting Backend  ^(FastAPI on http://localhost:8000^)...
start "PromptLab Backend" cmd /k "cd /d "%~dp0backend" && title PromptLab Backend && color 0B && echo. && echo  PromptLab Backend - FastAPI && echo  Swagger UI: http://localhost:8000/docs && echo  Health:     http://localhost:8000/api/health && echo. && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM ── Wait for backend to start ────────────────────────────────────────────
echo  [INFO] Waiting for backend to start...
timeout /t 4 /nobreak >nul

REM ── Start Frontend ───────────────────────────────────────────────────────
echo  [2/2] Starting Frontend ^(React on http://localhost:5173^)...
start "PromptLab Frontend" cmd /k "cd /d "%~dp0frontend" && title PromptLab Frontend && color 0D && echo. && echo  PromptLab Frontend - React + Vite && echo  App: http://localhost:5173 && echo. && npm run dev"

REM ── Wait then open browser ───────────────────────────────────────────────
echo.
echo  [INFO] Waiting for frontend to start...
timeout /t 5 /nobreak >nul

echo  [INFO] Opening browser...
start "" "http://localhost:5173"

echo.
echo  ==============================================
echo   PromptLab is running!
echo  ==============================================
echo.
echo   Frontend  : http://localhost:5173
echo   Backend   : http://localhost:8000
echo   Swagger   : http://localhost:8000/docs
echo   Health    : http://localhost:8000/api/health
echo.
echo   Two terminal windows have opened:
echo    - Blue  = Backend  ^(FastAPI^)
echo    - Purple = Frontend ^(React^)
echo.
echo   To stop: close those two terminal windows,
echo   or run stop.bat
echo.
echo   Press any key to close this launcher window...
pause >nul
