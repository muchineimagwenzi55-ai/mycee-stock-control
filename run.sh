#!/bin/bash

# Mycee Accessories Stock Control System - Linux/Mac Startup Script

echo ""
echo "========================================"
echo "Mycee Accessories Stock Control System"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo ""
echo "Starting Mycee Accessories Stock Control System..."
echo ""
echo "Access the system at: http://localhost:5000"
echo ""

# Run the Flask server entrypoint
python3 server.py
