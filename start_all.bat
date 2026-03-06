@echo off
REM RSLlingo - Start All Services (Windows)

echo.
echo  RSLlingo - Starting all services...
echo.

start "RSLlingo Backend" cmd /k "cd backend && call run_backend.bat"
timeout /t 5 /nobreak > nul
start "RSLlingo Frontend" cmd /k "cd frontend && call run_frontend.bat"

echo.
echo  ============================================
echo   RSLlingo is starting!
echo  ============================================
echo.
echo   Backend:  http://localhost:3001
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:3001/docs
echo.
