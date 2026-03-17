@echo off
title YOLO-Studio
echo Starting YOLO-Studio backend...
start "YOLO-Backend" /B python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
echo Backend starting on http://127.0.0.1:8765
echo.
echo Open http://localhost:5173 in your browser (or run: cd frontend ^&^& npm run dev)
echo Press Ctrl+C to stop.
pause
