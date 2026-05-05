#!/bin/bash

# Production startup script for Mycee Accessories Stock Control System

export FLASK_ENV=production

echo "Starting Mycee Accessories Stock Control System in PRODUCTION mode..."
echo "Access the system at: http://localhost:5000"
echo ""

# Run with gunicorn for production-like setup
gunicorn --bind 0.0.0.0:5000 server:app