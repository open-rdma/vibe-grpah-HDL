#!/usr/bin/env bash
set -e

echo "============================================"
echo "  RTL Blueprint — Server Startup"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ---- Backend ----
echo "[1/4] Installing backend dependencies..."
cd backend
python -m pip install -r requirements.txt -q 2>/dev/null || {
    echo "ERROR: Failed to install backend dependencies."
    exit 1
}

echo "[2/4] Starting backend server (port 5000)..."
python app.py &
BACKEND_PID=$!
cd ..

# ---- Frontend ----
echo "[3/4] Installing frontend dependencies..."
cd frontend
npm install --silent 2>/dev/null || {
    echo "ERROR: Failed to install frontend dependencies."
    kill "$BACKEND_PID" 2>/dev/null
    exit 1
}

echo "[4/4] Starting frontend dev server (port 5173)..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo "  Both servers are running!"
echo ""
echo "  Backend:  http://localhost:5000"
echo "  Frontend: http://localhost:5173"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop both servers."

# Cleanup on exit
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT TERM
wait
