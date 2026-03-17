@echo off
chcp 65001 >nul
REM build_portable.bat — 组装便携版（无需安装，复制即用）

echo ===================================================
echo   YOLOStudio 便携版组装
echo ===================================================

set ROOT=%~dp0
set EXE=%ROOT%frontend\src-tauri\target\release\yolostudio.exe
set BACKEND=%ROOT%dist\backend
set OUT=%ROOT%release\YOLOStudio_portable

REM 检查 yolostudio.exe
if not exist "%EXE%" (
    echo [错误] 未找到 %EXE%
    echo        请先运行: cd frontend && npm run tauri:build
    pause & exit /b 1
)

REM 检查 backend
if not exist "%BACKEND%\backend.exe" (
    echo [错误] 未找到 %BACKEND%\backend.exe
    echo        请先重新打包后端
    pause & exit /b 1
)

REM 清理旧目录
if exist "%OUT%" rd /s /q "%OUT%"
mkdir "%OUT%"

echo [1/2] 复制主程序...
copy /y "%EXE%" "%OUT%\YOLOStudio.exe" >nul

echo [2/2] 复制后端及依赖...
xcopy /e /i /y "%BACKEND%" "%OUT%\backend" >nul

echo.
echo ✅ 便携版已生成：
echo    %OUT%\
echo.
echo 使用方法：
echo   将 YOLOStudio_portable 文件夹复制到任意位置
echo   双击 YOLOStudio.exe 即可启动
echo.
echo 目录结构：
echo   YOLOStudio_portable\
echo     YOLOStudio.exe     ← 主程序
echo     backend\
echo       backend.exe      ← 自动启动的后端服务
echo       *.dll            ← DirectML / ONNX Runtime 依赖
echo.

REM 是否压缩为 zip（需要 PowerShell 5+）
set /p ZIPNOW="是否同时打包为 .zip？[Y/n] "
if /i "%ZIPNOW%"=="n" goto done
PowerShell -NoProfile -Command "Compress-Archive -Path '%OUT%' -DestinationPath '%ROOT%release\YOLOStudio_portable.zip' -Force"
echo ✅ 压缩包：%ROOT%release\YOLOStudio_portable.zip

:done
pause
