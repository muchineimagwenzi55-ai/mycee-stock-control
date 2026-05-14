@echo off
REM Mycee Accessories Stock Control System - Portable Server Launcher
REM This file can be placed anywhere and will run the server

echo.
echo ========================================
echo Mycee Accessories Stock Control System
echo Portable Server Launcher
echo ========================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Navigate to the script directory (remove trailing backslash if present)
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo Server location: %SCRIPT_DIR%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if server.py exists
if not exist "%SCRIPT_DIR%\server.py" (
    echo ERROR: server.py not found in %SCRIPT_DIR%
    echo Please ensure all server files are in the same directory as this batch file
    pause
    exit /b 1
)

REM Check if instance directory and database exist
if not exist "%SCRIPT_DIR%\instance\mycee_stock.db" (
    echo WARNING: Database file not found. The server may not work properly.
    echo Expected location: %SCRIPT_DIR%\instance\mycee_stock.db
    echo.
)

echo Starting Mycee server...
echo Press Ctrl+C to stop the server
echo.

REM Change to the script directory and run the server
cd /d "%SCRIPT_DIR%"
python server.py

echo.
echo Server stopped.
pause