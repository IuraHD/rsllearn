@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "FRONTEND_DIR=%ROOT_DIR%frontend"
set "REQUIRED_PYTHON=3.10"
set "VENV_DIR=%ROOT_DIR%.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "REBUILD_VENV=0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher ^(py^) was not found.
    echo Install Python %REQUIRED_PYTHON%.x and make sure the launcher is available.
    exit /b 1
)

py -%REQUIRED_PYTHON% -c "import sys" >nul 2>nul
if errorlevel 1 (
    echo Python %REQUIRED_PYTHON%.x is not available through the Windows launcher.
    echo Install Python %REQUIRED_PYTHON%.x first.
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    echo Node.js was not found.
    echo Install Node.js and npm first.
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo npm was not found.
    echo Install Node.js and npm first.
    exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
    echo Frontend package.json not found at "%FRONTEND_DIR%\package.json".
    exit /b 1
)

if not exist "%VENV_PY%" (
    set "REBUILD_VENV=1"
)

if exist "%VENV_PY%" (
    if not exist "%VENV_DIR%\pyvenv.cfg" (
        set "REBUILD_VENV=1"
    ) else (
        findstr /b /c:"version = %REQUIRED_PYTHON%." "%VENV_DIR%\pyvenv.cfg" >nul 2>nul
        if errorlevel 1 (
            set "REBUILD_VENV=1"
        )
    )
)

if "%REBUILD_VENV%"=="1" (
    if exist "%VENV_DIR%" (
        echo Rebuilding shared virtual environment with Python %REQUIRED_PYTHON%...
        rmdir /s /q "%VENV_DIR%"
    ) else (
        echo Creating shared virtual environment with Python %REQUIRED_PYTHON%...
    )
    py -%REQUIRED_PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create the shared virtual environment.
        exit /b 1
    )
) else (
    echo Shared virtual environment already uses Python %REQUIRED_PYTHON%.
)

call "%VENV_DIR%\Scripts\activate"
if errorlevel 1 (
    echo Failed to activate the shared virtual environment.
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo Installing shared Python dependencies...
python -m pip install -r "%ROOT_DIR%requirements.txt"
if errorlevel 1 exit /b 1

echo Installing frontend dependencies...
pushd "%FRONTEND_DIR%"
npm install
if errorlevel 1 (
    popd
    exit /b 1
)
popd

echo Shared project environment is ready.
echo Python venv: "%VENV_DIR%"
echo Frontend dependencies: "%FRONTEND_DIR%\node_modules"
