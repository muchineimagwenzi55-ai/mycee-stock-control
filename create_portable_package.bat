@echo off
REM Mycee Server Packager - Creates a portable ZIP package

echo.
echo ========================================
echo Mycee Server Packager
echo ========================================
echo.

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "OUTPUT_DIR=%PROJECT_DIR%\Mycee_Server_Portable"
set "ZIP_FILE=%PROJECT_DIR%\Mycee_Server_Portable.zip"

echo Creating portable package...
echo Source: %PROJECT_DIR%
echo Output: %OUTPUT_DIR%
echo ZIP: %ZIP_FILE%
echo.

REM Create output directory
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%"
mkdir "%OUTPUT_DIR%"

REM Copy essential files
echo Copying server files...
copy "%PROJECT_DIR%\server.py" "%OUTPUT_DIR%\" >nul
copy "%PROJECT_DIR%\app.py" "%OUTPUT_DIR%\" >nul
copy "%PROJECT_DIR%\models.py" "%OUTPUT_DIR%\" >nul
copy "%PROJECT_DIR%\config.py" "%OUTPUT_DIR%\" >nul

REM Copy instance directory (database)
if exist "%PROJECT_DIR%\instance" (
    echo Copying database...
    xcopy "%PROJECT_DIR%\instance" "%OUTPUT_DIR%\instance\" /E /I /H /Y >nul
)

REM Copy templates directory
if exist "%PROJECT_DIR%\templates" (
    echo Copying templates...
    xcopy "%PROJECT_DIR%\templates" "%OUTPUT_DIR%\templates\" /E /I /H /Y >nul
)

REM Copy static directory
if exist "%PROJECT_DIR%\static" (
    echo Copying static files...
    xcopy "%PROJECT_DIR%\static" "%OUTPUT_DIR%\static\" /E /I /H /Y >nul
)

REM Copy environment file
if exist "%PROJECT_DIR%\.env" (
    echo Copying environment configuration...
    copy "%PROJECT_DIR%\.env" "%OUTPUT_DIR%\" >nul
)

REM Copy requirements
copy "%PROJECT_DIR%\requirements.txt" "%OUTPUT_DIR%\" >nul

REM Create the launcher batch file
copy "%PROJECT_DIR%\Mycee_Server_Launcher.bat" "%OUTPUT_DIR%\" >nul

REM Create README
echo Mycee Accessories Stock Control System - Portable Version > "%OUTPUT_DIR%\README.txt"
echo. >> "%OUTPUT_DIR%\README.txt"
echo To run the server: >> "%OUTPUT_DIR%\README.txt"
echo 1. Double-click "Mycee_Server_Launcher.bat" >> "%OUTPUT_DIR%\README.txt"
echo 2. Or run: python server.py >> "%OUTPUT_DIR%\README.txt"
echo. >> "%OUTPUT_DIR%\README.txt"
echo Access the system at: http://127.0.0.1:5000 >> "%OUTPUT_DIR%\README.txt"
echo. >> "%OUTPUT_DIR%\README.txt"
echo Login credentials: >> "%OUTPUT_DIR%\README.txt"
echo Manager: bright / Ronaldo#7 >> "%OUTPUT_DIR%\README.txt"
echo Admin: admin / admin123 >> "%OUTPUT_DIR%\README.txt"

echo.
echo Creating ZIP package...
powershell "Compress-Archive -Path '%OUTPUT_DIR%\*' -DestinationPath '%ZIP_FILE%' -Force"

echo.
echo ========================================
echo Package created successfully!
echo ========================================
echo.
echo Portable package location: %ZIP_FILE%
echo.
echo To use:
echo 1. Extract the ZIP file to any location
echo 2. Run "Mycee_Server_Launcher.bat" or "python server.py"
echo 3. Access at http://127.0.0.1:5000
echo.
pause