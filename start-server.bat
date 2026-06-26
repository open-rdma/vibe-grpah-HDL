@echo off
chcp 65001 >nul
echo ============================================
echo   RTL Blueprint -- Server Startup
echo ============================================
echo.

cd /d "%~dp0"

:: ---- Backend ----
echo [1/3] Installing backend dependencies...
cd backend
python -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo ERROR: Failed to install backend dependencies.
    pause
    exit /b 1
)
cd ..

:: ---- Frontend build ----
echo [2/3] Installing frontend dependencies and building...
cd frontend
call npm install --silent
if %errorlevel% neq 0 (
    echo ERROR: Failed to install frontend dependencies.
    pause
    exit /b 1
)
call npx vite build
if %errorlevel% neq 0 (
    echo ERROR: Frontend build failed.
    pause
    exit /b 1
)
cd ..

:: ---- Start backend only ----
echo [3/3] Starting backend server (port 5000)...
echo.
echo ============================================
echo   Backend serving at http://localhost:5000
echo   Frontend built to frontend/dist/
echo ============================================
echo.
cd backend
python app.py
pause
