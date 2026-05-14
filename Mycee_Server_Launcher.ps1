# Mycee Server PowerShell Launcher
# Run this script from anywhere to start the Mycee server

param(
    [switch]$Production,
    [int]$Port = 5000
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Mycee Accessories Stock Control System" -ForegroundColor Yellow
Write-Host "PowerShell Server Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Server location: $ScriptDir" -ForegroundColor Green
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check server.py
$serverPath = Join-Path $ScriptDir "server.py"
if (-not (Test-Path $serverPath)) {
    Write-Host "ERROR: server.py not found in $ScriptDir" -ForegroundColor Red
    Write-Host "Please ensure all server files are in the same directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check database
$dbPath = Join-Path $ScriptDir "instance\mycee_stock.db"
if (-not (Test-Path $dbPath)) {
    Write-Host "WARNING: Database file not found at $dbPath" -ForegroundColor Yellow
    Write-Host "The server may not work properly without the database." -ForegroundColor Yellow
    Write-Host ""
}

# Set environment
if ($Production) {
    $env:FLASK_ENV = "production"
    Write-Host "Starting in PRODUCTION mode..." -ForegroundColor Magenta
} else {
    $env:FLASK_ENV = "development"
    Write-Host "Starting in DEVELOPMENT mode..." -ForegroundColor Magenta
}

$env:PORT = $Port

Write-Host "Port: $Port" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Change to script directory and run server
Set-Location $ScriptDir
try {
    python server.py
} catch {
    Write-Host "Error starting server: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "Server stopped." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}