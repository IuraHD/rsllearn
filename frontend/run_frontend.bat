@echo off
REM RSLlingo Frontend Startup Script (Windows)
REM Run from the frontend directory

if not exist node_modules (
    echo Installing npm dependencies...
    npm install
)
echo Starting frontend...
npm run dev
