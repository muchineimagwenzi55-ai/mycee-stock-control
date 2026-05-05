@echo off
title Mycee Accessories Stock Control System
color 0B

echo ============================================
echo   MYCEE ACCESSORIES - Starting Server...
echo ============================================
echo.

:: Go to your project folder
cd /d "C:\Users\muchi\Mycee Accessories Stock Control System"

:: Activate virtual environment if you have one
if exist ".env\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .env\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo Starting Flask server...
echo.
echo >> Open your browser and go to: http://127.0.0.1:5000
echo.
echo [Keep this window open while using the system]
echo [Close this window to stop the server]
echo.
echo ============================================

:: Run app.py
python app.py

echo.
echo Server stopped. Press any key to exit.
pause
