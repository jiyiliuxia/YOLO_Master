@echo off
chcp 65001 >nul
REM build.bat — 一键打包入口（调用 PowerShell 脚本）
REM 双击即可开始打包，无需手动输入命令

echo ===========================================
echo   YOLO_Master 一键打包
echo   (ONNX 推理 + DirectML 加速)
echo ===========================================
echo.
echo 此过程大约需要 5~15 分钟，请耐心等待...
echo 首次运行会下载依赖包，请确保网络畅通。
echo.

PowerShell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_backend.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [失败] 打包过程中出现错误，请查看上方日志。
    pause
    exit /b 1
)

echo.
echo [成功] 打包完成！
echo   后端：dist\backend\
echo   安装包：frontend\src-tauri\target\release\bundle\
pause
