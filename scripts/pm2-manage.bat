@echo off
REM PM2 Management Commands for AI Employee

if "%1"=="" goto help
if "%1"=="status" goto status
if "%1"=="logs" goto logs
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="delete" goto delete

:help
echo PM2 Management for AI Employee
echo.
echo Usage: pm2-manage.bat ^<command^>
echo.
echo Commands:
echo   status   - Show process status
echo   logs     - View all logs (live)
echo   start    - Start all processes
echo   stop     - Stop all processes
echo   restart  - Restart all processes
echo   delete   - Delete all processes
echo.
goto end

:status
pm2 status
goto end

:logs
pm2 logs
goto end

:start
cd /d "%~dp0.."
pm2 start ecosystem.config.cjs
pm2 status
goto end

:stop
pm2 stop all
pm2 status
goto end

:restart
cd /d "%~dp0.."
pm2 restart all
pm2 status
goto end

:delete
pm2 stop all
pm2 delete all
echo All processes deleted.
goto end

:end
