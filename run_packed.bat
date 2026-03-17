@echo off
chcp 65001 >nul
REM run_packed.bat — 打包版本测试运行脚本
REM 用于在打包后直接测试，不依赖 Python 虚拟环境

echo ===========================================
echo   YOLO_Master 打包版本启动（仅用于测试）
echo ===========================================

set ROOT=%~dp0
set BACKEND_EXE=%ROOT%dist\backend\backend.exe

if not exist "%BACKEND_EXE%" (
    echo [错误] 未找到打包后端：%BACKEND_EXE%
    echo        请先运行打包脚本：.\build_backend.ps1
    pause
    exit /b 1
)

echo [1/1] 启动打包后端 dist\backend\backend.exe ...
start "YOLOStudio-Backend-Packed" "%BACKEND_EXE%"

echo.
echo 后端已启动，端口 8765
echo 请直接打开 Tauri 安装包或运行前端进行测试
echo 关闭命令窗口即可停止后端
pause
