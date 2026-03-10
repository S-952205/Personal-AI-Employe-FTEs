@echo off
REM Start all AI Employee watchers and orchestrator
echo ========================================
echo AI Employee - Silver Tier Startup
echo ========================================
echo.

set PROJECT_ROOT=%~dp0
set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%

echo Starting watchers...
echo.

REM Start Gmail Watcher in new window
echo [1/3] Starting Gmail Watcher...
start "Gmail Watcher" python.exe "%PROJECT_ROOT%\scripts\gmail_watcher.py"

REM Wait a bit for Gmail watcher to initialize
timeout /t 3 /nobreak > nul

REM Start LinkedIn Watcher in new window
echo [2/3] Starting LinkedIn Watcher...
start "LinkedIn Watcher" python.exe "%PROJECT_ROOT%\scripts\linkedin_watcher.py"

REM Wait a bit for LinkedIn watcher to initialize
timeout /t 3 /nobreak > nul

REM Start Orchestrator in new window
echo [3/3] Starting Orchestrator...
start "Orchestrator" python.exe "%PROJECT_ROOT%\scripts\orchestrator.py"

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Running services:
echo   - Gmail Watcher (checks every 2 minutes)
echo   - LinkedIn Watcher (checks every 5 minutes)
echo   - Orchestrator (processes every 30 seconds)
echo.
echo Close the terminal windows to stop individual services.
echo.
echo Logs location: %PROJECT_ROOT%\logs\
echo.
