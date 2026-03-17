"""
inference.py — 推理测试模块 FastAPI 路由
提供模型加载、文件上传加载、图像推理、状态查询四个接口。
"""

import base64
import logging
import tempfile
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from core.inference_engine import InferenceEngine, get_engine, set_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inference", tags=["推理测试"])

# 临时模型存储目录（本次会话内复用，避免重复上传）
_TEMP_DIR = Path(tempfile.gettempdir()) / "yolo_studio_models"
_TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ── Pydantic 模型 ───────────────────────────────────────────────

class LoadRequest(BaseModel):
    """加载模型请求，传入模型在服务器上的绝对路径（Tauri/桌面端使用）"""
    model_path: str


class InferImageRequest(BaseModel):
    """图像推理请求"""
    image_b64: str         # base64 编码的 JPEG/PNG 图像
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45


# ── 路由 ────────────────────────────────────────────────────────

@router.get("/status")
async def get_status():
    """获取当前引擎加载状态与模型信息"""
    engine = get_engine()
    if engine is None or not engine.is_loaded:
        return {"loaded": False}
    return {"loaded": True, **engine.info}


@router.post("/load")
async def load_model(req: LoadRequest):
    """
    通过服务器本地绝对路径加载模型（适用于 Tauri 桌面端）。
    - .pt  → Ultralytics YOLO
    - .onnx → ONNX Runtime (DirectML / CPU)
    """
    path = Path(req.model_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在：{req.model_path}")
    if path.suffix.lower() not in {".pt", ".onnx"}:
        raise HTTPException(status_code=422, detail="仅支持 .pt 或 .onnx 模型")

    try:
        engine = InferenceEngine(str(path))
        set_engine(engine)
        return {"ok": True, **engine.info}
    except Exception as e:
        logger.error("[inference/load] 加载失败：%s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"模型加载失败：{e}")


@router.post("/upload")
async def upload_and_load(file: UploadFile = File(...)):
    """
    通过文件上传加载模型（适用于浏览器 Web 端）。
    浏览器无法提供本地绝对路径，通过 multipart 上传文件内容，
    后端保存至临时目录后自动加载。
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pt", ".onnx"}:
        raise HTTPException(status_code=422, detail="仅支持 .pt 或 .onnx 模型")

    # 保存到临时目录
    save_path = _TEMP_DIR / (file.filename or f"model{suffix}")
    try:
        content = await file.read()
        save_path.write_bytes(content)
        logger.info("[inference/upload] 文件已保存：%s (%d bytes)", save_path, len(content))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败：{e}")
    finally:
        await file.close()

    # 加载引擎
    try:
        engine = InferenceEngine(str(save_path))
        set_engine(engine)
        return {"ok": True, **engine.info}
    except Exception as e:
        logger.error("[inference/upload] 加载失败：%s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"模型加载失败：{e}")


@router.post("/image")
async def infer_image(req: InferImageRequest):
    """
    对单张图像进行目标检测推理。
    - 输入：base64 编码的图像（含或不含 data URI 头）
    - 输出：标准化 boxes 列表（原图坐标）
    """
    engine = get_engine()
    if engine is None or not engine.is_loaded:
        raise HTTPException(status_code=409, detail="请先加载模型（POST /inference/load 或 /inference/upload）")

    # 解码 base64 图像
    try:
        b64_data = req.image_b64
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
        img_bytes = base64.b64decode(b64_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        image_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError("cv2.imdecode 返回 None")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"图像解码失败：{e}")

    # 推理
    try:
        result = engine.predict(
            image_bgr=image_bgr,
            conf_threshold=req.conf_threshold,
            iou_threshold=req.iou_threshold,
        )
        return result
    except Exception as e:
        logger.error("[inference/image] 推理失败：%s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"推理失败：{e}")
