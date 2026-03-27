@echo off
REM PM2 Setup for AI Employee - Silver Tier
REM This script sets up PM2 to run AI Employee processes in the background

echo ========================================
echo AI Employee - PM2 Setup
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js found: 
node --version
echo.

REM Check if PM2 is installed
where pm2 >nul 2>nul
if %errorlevel% neq 0 (
    echo PM2 not found. Installing PM2 globally...
    npm install -g pm2
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install PM2
        pause
        exit /b 1
    )
    echo PM2 installed successfully
) else (
    echo PM2 already installed
    pm2 --version
)
echo.

REM Get the project root directory
set PROJECT_ROOT=%~dp0
set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%

echo Project Root: %PROJECT_ROOT%
echo.

REM Create logs directory if it doesn't exist
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

REM ========================================
REM Start processes with PM2
REM ========================================
echo Starting AI Employee processes with PM2...
echo.

cd /d "%PROJECT_ROOT%"

REM Stop any existing processes
echo Stopping any existing PM2 processes...
pm2 stop all 2>nul
pm2 delete all 2>nul
echo.

REM Start processes from ecosystem file
echo Starting processes from ecosystem.config.cjs...
pm2 start ecosystem.config.cjs
echo.

REM Wait for processes to start
timeout /t 3 /nobreak >nul

REM Show status
echo ========================================
echo PM2 Process Status
echo ========================================
pm2 status
echo.

REM Show logs command
echo ========================================
echo To view logs:
echo   pm2 logs
echo.
echo To view specific process logs:
echo   pm2 logs gmail-watcher
echo   pm2 logs linkedin-watcher
echo   pm2 logs orchestrator
echo.
echo To restart all processes:
echo   pm2 restart all
echo.
echo To stop all processes:
echo   pm2 stop all
echo.
echo To start all processes:
echo   pm2 start all
echo.
echo ========================================
echo.

REM Save process list for auto-restart
echo Saving PM2 process list...
pm2 save
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Processes are now running in the background.
echo They will automatically restart if they crash.
echo.
echo NOTE: On Windows, PM2 won't auto-start on boot.
echo For auto-start on boot, use:
echo   1. Windows Task Scheduler: scripts\setup-tasks.bat
echo   2. Or install pm2-startup: npm install -g pm2-startup
echo.
pause
