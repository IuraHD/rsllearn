@echo off
setlocal
set "PYTHON=%~dp0venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Local venv Python not found: "%PYTHON%"
    echo Create or restore the venv in "%~dp0venv" first.
    exit /b 1
)

"%PYTHON%" "%~dp0rsl_model_trainer.py" %*
