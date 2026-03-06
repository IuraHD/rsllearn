@echo off
REM RSLlingo Backend Debug Script (Windows)
REM Run from the backend directory

if not exist ..\.venv\Scripts\python.exe (
    echo Creating shared virtual environment at ..\.venv ...
    python -m venv ..\.venv
)
call ..\.venv\Scripts\activate
set PORT=3002
echo Starting backend in DEBUG mode on port 3002...
python -m uvicorn app.main:app --reload --port 3002
