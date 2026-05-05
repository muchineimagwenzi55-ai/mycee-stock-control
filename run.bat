@echo off
REM Mycee Accessories Stock Control System - Windows Startup Script

echo.
echo ========================================
echo Mycee Accessories Stock Control System
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Starting Mycee Accessories Stock Control System...
echo.
echo Access the system at: http://localhost:5000
echo.

REM Run the Flask server entrypoint
python server.py

pause
