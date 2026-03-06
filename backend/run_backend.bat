@echo off
REM RSLlingo Backend Startup Script (Windows)
REM Run from the backend directory

if not exist ..\.venv\Scripts\python.exe (
    echo Creating shared virtual environment at ..\.venv ...
    python -m venv ..\.venv
)
call ..\.venv\Scripts\activate
echo Installing dependencies...
pip install -r requirements.txt
echo Starting server...
python -m uvicorn app.main:app --reload --port 3001
