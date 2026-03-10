@echo off
REM Windows Task Scheduler Setup for AI Employee - Silver Tier
REM Run this script as Administrator to set up scheduled tasks

echo ========================================
echo AI Employee - Task Scheduler Setup
echo ========================================
echo.

REM Get the project root directory
set PROJECT_ROOT=%~dp0
set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%

echo Project Root: %PROJECT_ROOT%
echo.

REM Create log directory if it doesn't exist
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

REM ========================================
REM Task 1: Gmail Watcher
REM ========================================
echo [1/3] Setting up Gmail Watcher task...
schtasks /Create /TN "AI_Employee_Gmail_Watcher" /TR "python.exe '%PROJECT_ROOT%\scripts\gmail_watcher.py'" /SC ONSTART /RU SYSTEM /RL HIGHEST /F
if %errorlevel% equ 0 (
    echo   ✓ Gmail Watcher task created
) else (
    echo   ✗ Failed to create Gmail Watcher task
)
echo.

REM ========================================
REM Task 2: LinkedIn Watcher
REM ========================================
echo [2/3] Setting up LinkedIn Watcher task...
schtasks /Create /TN "AI_Employee_LinkedIn_Watcher" /TR "python.exe '%PROJECT_ROOT%\scripts\linkedin_watcher.py'" /SC ONSTART /RU SYSTEM /RL HIGHEST /F
if %errorlevel% equ 0 (
    echo   ✓ LinkedIn Watcher task created
) else (
    echo   ✗ Failed to create LinkedIn Watcher task
)
echo.

REM ========================================
REM Task 3: Orchestrator
REM ========================================
echo [3/3] Setting up Orchestrator task...
schtasks /Create /TN "AI_Employee_Orchestrator" /TR "python.exe '%PROJECT_ROOT%\scripts\orchestrator.py'" /SC ONSTART /RU SYSTEM /RL HIGHEST /F
if %errorlevel% equ 0 (
    echo   ✓ Orchestrator task created
) else (
    echo   ✗ Failed to create Orchestrator task
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Scheduled tasks created:
echo   - AI_Employee_Gmail_Watcher
echo   - AI_Employee_LinkedIn_Watcher
echo   - AI_Employee_Orchestrator
echo.
echo These tasks will start automatically when Windows boots.
echo.
echo To view tasks: taskschd.msc
echo To run manually: schtasks /Run /TN "AI_Employee_Gmail_Watcher"
echo To delete tasks: schtasks /Delete /TN "AI_Employee_Gmail_Watcher" /F
echo.
pause
