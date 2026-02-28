#!/usr/bin/env bash
# BroCoDDE Startup Script
# Runs both the backend and frontend in the background using nohup.
# Logs are persisted to readable files in their respective folders.

cd "$(dirname "$0")" || exit

echo "🚀 Starting BroCoDDE..."

# Start Backend
cd backend
mkdir -p logs
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 >> logs/brocodde.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started on port 8000 (PID: $BACKEND_PID)"
echo "   ↳ Logs tail: tail -f backend/logs/brocodde.log"

# Start Frontend
cd ../frontend
mkdir -p logs
nohup npm run dev >> logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started on port 3000 (PID: $FRONTEND_PID)"
echo "   ↳ Logs tail: tail -f frontend/logs/frontend.log"

echo ""
echo "BroCoDDE is running in the background!"
echo "To stop the servers later, you can run:"
echo "kill $BACKEND_PID $FRONTEND_PID"
