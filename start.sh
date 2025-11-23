#!/bin/bash

# Start script for Code to Audio System (Unified Application)

echo "Starting Code to Audio System..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp backend/.env.example .env
    echo "Please edit .env with your Hugging Face API token"
fi

# Start the unified application
echo "Starting application on http://localhost:8000..."
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
PID=$!

echo "Application PID: $PID"
echo ""
echo "Application starting..."
echo "Web Interface: http://localhost:8000"
echo "API Endpoint: http://localhost:8000/synthesize"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the application"

# Wait for Ctrl+C
trap "kill $PID; exit" INT
wait
