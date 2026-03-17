# -*- mode: python ; coding: utf-8 -*-
# backend.spec — PyInstaller 打包配置
# 生成目标：dist/backend/ 目录（onedir 模式，启动速度更快）

import sys
from pathlib import Path

# 定位 onnxruntime 的 capi DLL 目录（DirectML 需要）
try:
    import onnxruntime
    ORT_DIR = Path(onnxruntime.__file__).parent / "capi"
except ImportError:
    ORT_DIR = None

# 收集 onnxruntime capi DLL（DirectML.dll 等关键文件）
ort_binaries = []
if ORT_DIR and ORT_DIR.exists():
    for dll in ORT_DIR.glob("*.dll"):
        ort_binaries.append((str(dll), "onnxruntime/capi"))

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=ort_binaries,
    datas=[],
    hiddenimports=[
        # onnxruntime 核心
        "onnxruntime",
        "onnxruntime.capi",
        "onnxruntime.capi.onnxruntime_pybind11_state",
        # fastapi / starlette
        "fastapi",
        "starlette",
        "starlette.middleware",
        "starlette.middleware.cors",
        "starlette.routing",
        # uvicorn
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        # 图像处理
        "cv2",
        "PIL",
        "PIL.Image",
        "numpy",
        # 其他
        "yaml",
        "multipart",
        "anyio",
        "anyio.abc",
        "httptools",
        "websockets",
        "ast",
        "collections",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 明确排除，进一步减小体积
        "ultralytics",
        "torch",
        "torchvision",
        "torchaudio",
        "matplotlib",
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "IPython",
        "jupyter",
        "notebook",
        "pandas",
        "scipy",
        "sklearn",
        "tensorflow",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,            # 保留控制台，方便现场调试日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="backend",
)
