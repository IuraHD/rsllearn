@echo off
REM RSLlingo Backend Startup Script (Windows)
REM Run from the backend directory

if not exist ..\setup_python_env.bat (
    echo Missing shared environment setup script: ..\setup_python_env.bat
    exit /b 1
)

if not exist ..\.venv\Scripts\python.exe (
    call ..\setup_python_env.bat
    if errorlevel 1 exit /b 1
)

findstr /b /c:"version = 3.10." ..\.venv\pyvenv.cfg >nul 2>nul
if errorlevel 1 (
    call ..\setup_python_env.bat
    if errorlevel 1 exit /b 1
)

call ..\.venv\Scripts\activate
echo Starting server...
python -m uvicorn app.main:app --reload --port 3001
