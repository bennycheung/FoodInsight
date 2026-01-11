#!/bin/bash
# Stop all FoodInsight development services
# Run from anywhere: ./scripts/stop-dev.sh

echo "Stopping FoodInsight Development Services..."
echo "============================================="

# Kill processes on each port
for PORT in 8000 5173 8080; do
    PIDS=$(lsof -ti :$PORT 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "Stopping service on port $PORT (PIDs: $PIDS)"
        echo "$PIDS" | xargs kill -9 2>/dev/null || true
    else
        echo "No service running on port $PORT"
    fi
done

# Verify all stopped
sleep 1
if lsof -i :8000 -i :5173 -i :8080 2>/dev/null | grep -q LISTEN; then
    echo ""
    echo "Warning: Some services may still be running:"
    lsof -i :8000 -i :5173 -i :8080 2>/dev/null | grep LISTEN || true
else
    echo ""
    echo "============================================="
    echo "All services stopped."
    echo "============================================="
fi
