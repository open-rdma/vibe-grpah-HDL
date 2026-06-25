@echo off
chcp 65001 >nul
echo ============================================
echo   RTL Blueprint — Server Startup
echo ============================================
echo.

cd /d "%~dp0"

:: ---- Backend ----
echo [1/4] Installing backend dependencies...
cd backend
python -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo ERROR: Failed to install backend dependencies.
    pause
    exit /b 1
)

echo [2/4] Starting backend server (port 5000)...
start "RTL Blueprint Backend" cmd /c "python app.py"
cd ..

:: ---- Frontend ----
echo [3/4] Installing frontend dependencies...
cd frontend
call npm install --silent
if %errorlevel% neq 0 (
    echo ERROR: Failed to install frontend dependencies.
    pause
    exit /b 1
)

echo [4/4] Starting frontend dev server (port 5173)...
start "RTL Blueprint Frontend" cmd /c "npm run dev"
cd ..

echo.
echo ============================================
echo   Both servers are starting!
echo.
echo   Backend:  http://localhost:5000
echo   Frontend: http://localhost:5173
echo ============================================
echo.
pause
