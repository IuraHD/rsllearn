@echo off
setlocal
set "PYTHON=%~dp0..\.venv\Scripts\python.exe"

if not exist "%~dp0..\setup_python_env.bat" (
    echo Missing shared environment setup script: "%~dp0..\setup_python_env.bat"
    exit /b 1
)

if not exist "%PYTHON%" (
    call "%~dp0..\setup_python_env.bat"
    if errorlevel 1 exit /b 1
)

findstr /b /c:"version = 3.10." "%~dp0..\.venv\pyvenv.cfg" >nul 2>nul
if errorlevel 1 (
    call "%~dp0..\setup_python_env.bat"
    if errorlevel 1 exit /b 1
)

"%PYTHON%" "%~dp0rsl_testare_live.py" %*
