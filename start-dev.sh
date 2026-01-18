#!/bin/bash

# Start Backend and Frontend for development

echo "🚀 Starting Procuro Development Environment..."

# Start Backend
echo "Starting FastAPI Backend on http://localhost:8000..."
cd backend
PYTHONPATH=.. uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "Starting React Frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services running:"
echo "   Backend:  http://localhost:8000 (API Docs: http://localhost:8000/docs)"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
