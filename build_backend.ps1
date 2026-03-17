# build_backend.ps1 — YOLO_Master 后端打包脚本
# 用法：在项目根目录执行 .\build_backend.ps1
# 前提：已安装 Python 3.10+，且网络可访问 PyPI

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  YOLO_Master 后端打包脚本 (ONNX-only)" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# ── 路径配置 ────────────────────────────────────────────────────
$ROOT      = $PSScriptRoot                         # 脚本所在目录（项目根）
$BACKEND   = Join-Path $ROOT "backend"
$VENV_DIR  = Join-Path $ROOT ".venv_pack"          # 专用打包虚拟环境（与开发环境隔离）
$DIST_DIR  = Join-Path $ROOT "dist"
$SPEC_FILE = Join-Path $BACKEND "backend.spec"
$REQ_FILE  = Join-Path $BACKEND "requirements_pack.txt"

# ── 步骤 1：创建/激活虚拟环境 ───────────────────────────────────
Write-Host "`n[1/5] 检查打包专用虚拟环境..." -ForegroundColor Yellow

if (-not (Test-Path $VENV_DIR)) {
    Write-Host "      创建虚拟环境 $VENV_DIR" -ForegroundColor Gray
    python -m venv $VENV_DIR
} else {
    Write-Host "      虚拟环境已存在，跳过创建" -ForegroundColor Gray
}

$PIP  = Join-Path $VENV_DIR "Scripts\pip.exe"
$PY   = Join-Path $VENV_DIR "Scripts\python.exe"

# ── 步骤 2：安装精简依赖 ─────────────────────────────────────────
Write-Host "`n[2/5] 安装打包依赖（onnxruntime-directml, 无 torch）..." -ForegroundColor Yellow
& $PIP install --upgrade pip --quiet
& $PIP install -r $REQ_FILE --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "      [错误] 依赖安装失败，请检查网络或 requirements_pack.txt" -ForegroundColor Red
    exit 1
}
Write-Host "      依赖安装完成" -ForegroundColor Green

# ── 步骤 3：运行 PyInstaller ──────────────────────────────────────
Write-Host "`n[3/5] 运行 PyInstaller 打包后端..." -ForegroundColor Yellow
$PyInstaller = Join-Path $VENV_DIR "Scripts\pyinstaller.exe"

Push-Location $BACKEND
try {
    & $PyInstaller $SPEC_FILE --distpath $DIST_DIR --workpath (Join-Path $ROOT "build") --noconfirm
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      [错误] PyInstaller 打包失败" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}
Write-Host "      后端打包完成 → $DIST_DIR\backend\" -ForegroundColor Green

# ── 步骤 4：打包前端（Tauri build）──────────────────────────────
Write-Host "`n[4/5] 构建前端 + Tauri 安装包..." -ForegroundColor Yellow
$FRONTEND = Join-Path $ROOT "frontend"
Push-Location $FRONTEND
try {
    npm install --silent 2>&1 | Out-Null
    npm run tauri:build 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      [错误] Tauri build 失败" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# ── 步骤 5：汇总输出 ─────────────────────────────────────────────
Write-Host "`n[5/5] 打包完成！输出路径：" -ForegroundColor Green
$BACKEND_OUT = Join-Path $DIST_DIR "backend"
$TAURI_OUT   = Join-Path $FRONTEND "src-tauri\target\release\bundle"

if (Test-Path $BACKEND_OUT) {
    $size = (Get-ChildItem $BACKEND_OUT -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "      后端目录：$BACKEND_OUT ($([math]::Round($size, 1)) MB)" -ForegroundColor Cyan
}
if (Test-Path $TAURI_OUT) {
    Write-Host "      Tauri 安装包：$TAURI_OUT" -ForegroundColor Cyan
}

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  完成！模型文件无需打包，运行时通过界面选择 .onnx 文件" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
