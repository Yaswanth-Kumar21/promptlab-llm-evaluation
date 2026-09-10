@echo off
title PromptLab - Stop
color 0C

echo.
echo  Stopping PromptLab servers...
echo.

REM Kill uvicorn (backend)
echo  [1/2] Stopping backend ^(uvicorn^)...
taskkill /FI "WINDOWTITLE eq PromptLab Backend" /T /F >nul 2>&1
taskkill /FI "IMAGENAME eq uvicorn.exe" /T /F >nul 2>&1

REM Kill node / vite (frontend)
echo  [2/2] Stopping frontend ^(vite/node^)...
taskkill /FI "WINDOWTITLE eq PromptLab Frontend" /T /F >nul 2>&1

REM Also free the ports just in case
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo  All servers stopped.
echo.
pause
