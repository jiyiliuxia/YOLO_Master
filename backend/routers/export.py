"""
export.py — 模型转换与导出模块 FastAPI 路由
提供：
  POST /api/export/scan-weights  → 扫描项目目录下所有 .pt 权重文件
  POST /api/export/export        → SSE 流式推送，执行 ONNX 导出
"""

import asyncio
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/export", tags=["模型导出"])


# ── Pydantic 模型 ────────────────────────────────────────────────────

class ScanWeightsRequest(BaseModel):
    """扫描项目目录中的权重文件"""
    project_dir: str


class ExportRequest(BaseModel):
    """ONNX 导出请求"""
    model_path: str          # 源 .pt 文件绝对路径
    output_dir: str          # 输出目录
    opset: int = 12          # ONNX Opset 版本
    imgsz: int = 640         # 推理图像尺寸
    half: bool = False       # FP16 半精度
    simplify: bool = True    # onnxsim 图优化


# ── 工具函数 ─────────────────────────────────────────────────────────

def _scan_pt_files(project_dir: str) -> list[dict]:
    """
    递归扫描项目目录，收集所有 .pt 文件信息。
    优先返回 runs/train/*/weights 下的文件，best.pt 排在 last.pt 前面。
    """
    root = Path(project_dir)
    if not root.exists():
        return []

    # 先收集 runs/train/*/weights 下的权重（优先展示）
    priority: list[Path] = []
    others: list[Path] = []

    for pt in root.rglob("*.pt"):
        parts = pt.parts
        # 检查路径是否包含 runs/train/.../weights
        if "runs" in parts and "weights" in parts:
            priority.append(pt)
        else:
            others.append(pt)

    # 排序：best.pt > last.pt > 其他（按文件名）
    def sort_key(p: Path):
        name = p.stem.lower()
        if name == "best":
            return (0, str(p))
        if name == "last":
            return (1, str(p))
        return (2, str(p))

    priority.sort(key=sort_key)
    others.sort(key=sort_key)

    result = []
    for pt in priority + others:
        try:
            stat = pt.stat()
            size_mb = round(stat.st_size / 1024 / 1024, 2)
            mtime = stat.st_mtime
        except OSError:
            size_mb = 0
            mtime = 0

        result.append({
            "path": str(pt),
            "name": pt.name,
            "relative": str(pt.relative_to(root)),
            "size_mb": size_mb,
            "mtime": mtime,
            "is_priority": pt in priority,
        })
    return result


def _get_python_exe() -> str:
    """
    解析当前应用使用的 Python 解释器路径。

    - 开发模式（直接跑 python main.py）：sys.executable 就是 python.exe，直接返回。
    - 打包模式（PyInstaller exe）：sys.executable 是 backend.exe 本身，
      不能用于运行 Python 脚本。此时从系统 PATH 查找真实的 python.exe。
    """
    if getattr(sys, 'frozen', False):
        # 打包后：sys.executable → backend.exe，需要找系统 Python
        python = shutil.which('python') or shutil.which('python3')
        if not python:
            raise RuntimeError(
                "未在系统 PATH 中找到 Python 解释器。\n"
                "导出功能需要在系统中安装 Python + ultralytics，"
                "请确认已将 Python 加入 PATH 后重试。"
            )
        return python
    # 开发模式：直接使用当前 Python
    return sys.executable


async def _run_export_stream(req: ExportRequest) -> AsyncGenerator[str, None]:
    """
    在子进程中执行 ultralytics YOLO 导出，并将 stdout/stderr 以 SSE 格式逐行推送。
    完成后推送 done 事件（含输出文件路径和体积信息）。
    """
    model_path = Path(req.model_path)
    output_dir = Path(req.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 构建 Python 子进程命令，避免阻塞 FastAPI 事件循环
    script = (
        f"from ultralytics import YOLO\n"
        f"m = YOLO(r'{model_path}')\n"
        f"m.export(\n"
        f"    format='onnx',\n"
        f"    opset={req.opset},\n"
        f"    imgsz={req.imgsz},\n"
        f"    half={req.half},\n"
        f"    simplify={req.simplify},\n"
        f"    project=r'{output_dir}',\n"
        f"    name='export_result',\n"
        f"    exist_ok=True,\n"
        f")\n"
    )

    def _sse(event_type: str, **kwargs) -> str:
        payload = json.dumps({"type": event_type, **kwargs}, ensure_ascii=False)
        return f"data: {payload}\n\n"

    # 解析正确的 Python 路径（打包后不能用 sys.executable）
    try:
        python_exe = _get_python_exe()
    except RuntimeError as e:
        yield _sse("error", error=str(e))
        return

    yield _sse("start", message=f"开始导出：{model_path.name} (Python: {python_exe})")

    try:
        proc = await asyncio.create_subprocess_exec(
            python_exe, "-c", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # stderr 合并到 stdout
            cwd=str(output_dir),
        )

        # 逐行读取子进程输出
        async for line_bytes in proc.stdout:
            line = line_bytes.decode("utf-8", errors="replace").rstrip()
            if line:
                logger.debug("[export] %s", line)
                yield _sse("log", message=line)

        await proc.wait()

        if proc.returncode != 0:
            yield _sse("error", error=f"导出进程异常退出（code={proc.returncode}）")
            return

        # 尝试定位生成的 .onnx 文件
        onnx_candidates = list(output_dir.rglob("*.onnx"))
        # 也检查与源模型同目录（ultralytics 默认行为）
        default_onnx = model_path.with_suffix(".onnx")
        if default_onnx.exists() and default_onnx not in onnx_candidates:
            onnx_candidates.insert(0, default_onnx)

        if onnx_candidates:
            out_path = max(onnx_candidates, key=lambda p: p.stat().st_mtime)
            size_mb = round(out_path.stat().st_size / 1024 / 1024, 2)
            yield _sse(
                "done",
                output_path=str(out_path),
                size_mb=size_mb,
                message=f"导出完成：{out_path.name}（{size_mb} MB）",
            )
        else:
            yield _sse("error", error="导出完成但未找到 .onnx 文件，请检查输出目录")

    except Exception as e:
        logger.error("[export] 导出异常：%s", e, exc_info=True)
        yield _sse("error", error=f"导出异常：{e}")


# ── 路由 ─────────────────────────────────────────────────────────────

@router.post("/scan-weights")
async def scan_weights(req: ScanWeightsRequest):
    """
    扫描指定项目目录下所有 .pt 权重文件，
    优先列出 runs/train/*/weights 下的 best.pt / last.pt。
    """
    if not Path(req.project_dir).exists():
        return {"weights": [], "error": "目录不存在"}
    weights = _scan_pt_files(req.project_dir)
    return {"weights": weights}


@router.post("/export")
async def export_model(req: ExportRequest):
    """
    执行模型导出，以 SSE 流式推送进度日志。
    前端通过 fetch + ReadableStream 消费事件流。
    """
    return StreamingResponse(
        _run_export_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
