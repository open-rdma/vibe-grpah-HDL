#!/usr/bin/env bash
set -e

echo "============================================"
echo "  RTL Blueprint — Server Startup"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ---- Backend deps ----
echo "[1/3] Installing backend dependencies..."
cd backend
python -m pip install -r requirements.txt -q 2>/dev/null || {
    echo "ERROR: Failed to install backend dependencies."
    exit 1
}
cd ..

# ---- Frontend build ----
echo "[2/3] Installing frontend dependencies and building..."
cd frontend
npm install --silent 2>/dev/null || {
    echo "ERROR: Failed to install frontend dependencies."
    exit 1
}
npx vite build || {
    echo "ERROR: Frontend build failed."
    exit 1
}
cd ..

# ---- Start backend only ----
echo "[3/3] Starting backend server (port 5000)..."
echo ""
echo "============================================"
echo "  Backend serving at http://localhost:5000"
echo "  Frontend built to frontend/dist/"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop."

cd backend
python app.py
