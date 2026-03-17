@echo off
chcp 65001 >nul
REM dev_start.bat — 开发模式启动（后端 + 前端分离）
REM 用于本地开发调试，不需要打包

echo ===========================================
echo   YOLO_Master 开发模式启动
echo ===========================================

REM 启动后端（使用开发虚拟环境）
set BACKEND_DIR=%~dp0backend
set VENV=%~dp0.venv

if not exist "%VENV%\Scripts\python.exe" (
    echo [错误] 找不到开发虚拟环境 .venv，请先执行：
    echo        python -m venv .venv
    echo        .venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

echo [1/2] 启动后端服务 (FastAPI)...
start "YOLOStudio-Backend" cmd /k "%VENV%\Scripts\python.exe %BACKEND_DIR%\main.py"

echo [2/2] 启动前端开发服务 (Vite)...
cd frontend
start "YOLOStudio-Frontend" cmd /k "npm run dev"
cd ..

echo.
echo 后端已在 http://127.0.0.1:8765 启动
echo 前端已在 http://localhost:5173 启动
echo 关闭对应命令窗口即可停止服务
pause
