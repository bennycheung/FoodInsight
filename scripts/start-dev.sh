#!/bin/bash
# Start all FoodInsight development services
# Run from project root: ./scripts/start-dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Starting FoodInsight Development Services..."
echo "============================================="

# Check if services are already running
if lsof -i :8000 -i :5173 -i :8080 2>/dev/null | grep -q LISTEN; then
    echo "Warning: Some services may already be running."
    echo "Run ./scripts/stop-dev.sh first to stop them."
    lsof -i :8000 -i :5173 -i :8080 2>/dev/null | grep LISTEN || true
    exit 1
fi

# Start FastAPI Backend (port 8000)
echo ""
echo "[1/3] Starting FastAPI Backend on port 8000..."
cd "$PROJECT_ROOT/server"
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd "$PROJECT_ROOT"

# Wait for backend to be ready
sleep 2
if ! lsof -i :8000 2>/dev/null | grep -q LISTEN; then
    echo "Error: Backend failed to start"
    exit 1
fi
echo "Backend running (PID: $BACKEND_PID)"

# Start Vue PWA (port 5173)
echo ""
echo "[2/3] Starting Vue PWA on port 5173..."
cd "$PROJECT_ROOT/app"
bun run dev &
VUE_PID=$!
cd "$PROJECT_ROOT"

# Wait for Vue to be ready
sleep 3
if ! lsof -i :5173 2>/dev/null | grep -q LISTEN; then
    echo "Error: Vue PWA failed to start"
    exit 1
fi
echo "Vue PWA running (PID: $VUE_PID)"

# Start Detection Service (port 8080)
echo ""
echo "[3/3] Starting Detection Service on port 8080..."
source .venv/bin/activate
CAMERA_INDEX=${CAMERA_INDEX:-1} python run_dev.py &
DETECTION_PID=$!

# Wait for detection service to be ready
sleep 3
if ! lsof -i :8080 2>/dev/null | grep -q LISTEN; then
    echo "Error: Detection service failed to start"
    exit 1
fi
echo "Detection service running (PID: $DETECTION_PID)"

echo ""
echo "============================================="
echo "All services started successfully!"
echo ""
echo "  FastAPI Backend:  http://localhost:8000"
echo "  OpenAPI Docs:     http://localhost:8000/docs"
echo "  Vue PWA:          http://localhost:5173"
echo "  Admin Portal:     http://localhost:8080"
echo ""
echo "To stop all services: ./scripts/stop-dev.sh"
echo "============================================="

# Keep script running to maintain background processes
wait
