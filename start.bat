@echo off
REM Start script for Code to Audio System (Unified Application)

echo Starting Code to Audio System...

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from example...
    copy backend\.env.example .env
    echo Please edit .env with your Hugging Face API token
)

REM Start the unified application
echo Starting application on http://localhost:8000...
start "Code to Audio System" cmd /c "python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Application starting...
echo Web Interface: http://localhost:8000
echo API Endpoint: http://localhost:8000/synthesize
echo Health Check: http://localhost:8000/health
echo.
echo Close this window to stop the application
pause
