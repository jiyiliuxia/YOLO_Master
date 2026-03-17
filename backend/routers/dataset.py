"""
dataset.py — 数据集管理模块 FastAPI 路由
包含：加载、体检 SSE、删除孤立文件、图片列表、标注解析、分析、拆分 SSE
"""
import json
import base64
import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional

from backend.core import dataset_manager, sanity_checker, dataset_splitter

router = APIRouter(prefix="/api/dataset", tags=["dataset"])

# 全局缓存当前数据集（简单内存缓存，单用户场景足够）
_current_dataset: dataset_manager.DatasetInfo = dataset_manager.DatasetInfo()


class LoadRequest(BaseModel):
    root_dir: str


class SanityCheckRequest(BaseModel):
    root_dir: str


class FixIssuesRequest(BaseModel):
    issues: List[dict]


class AnalyticsRequest(BaseModel):
    root_dir: str


class SplitRequest(BaseModel):
    root_dir: str
    output_dir: str
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    seed: int = 42
    move: bool = False


@router.post("/load")
async def load_dataset(req: LoadRequest):
    global _current_dataset
    info = dataset_manager.load_dataset(req.root_dir)
    _current_dataset = info
    if not info.is_valid:
        return {"success": False, "error": "无效的数据集目录（未找到 images/ 子目录）"}
    return {"success": True, "data": info.to_dict()}


@router.post("/sanity-check")
async def sanity_check_sse(req: SanityCheckRequest):
    """SSE 流式推送体检进度与结果。"""
    info = dataset_manager.load_dataset(req.root_dir)
    def generate():
        for event in sanity_checker.check_dataset(info):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/fix-issues")
async def fix_issues(req: FixIssuesRequest):
    result = sanity_checker.remove_orphan_labels(req.issues)
    return {"success": True, "data": result}


@router.post("/image-list")
async def get_image_list(req: LoadRequest):
    info = dataset_manager.load_dataset(req.root_dir)
    images = dataset_manager.get_image_list(info)
    return {"success": True, "data": images, "count": len(images)}


@router.get("/label")
async def get_label(img_path: str, root_dir: str):
    info = dataset_manager.load_dataset(root_dir)
    lbl_path = dataset_manager.get_label_path(info, img_path)
    labels = dataset_manager.parse_yolo_labels(lbl_path) if lbl_path else []
    return {"success": True, "data": labels, "classes": info.classes}


@router.get("/image")
async def serve_image(path: str):
    """将本地图片文件作为 base64 返回给前端（绕过跨域限制）。"""
    if not os.path.isfile(path):
        return {"success": False, "error": "图片不存在"}
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png",
            "bmp": "bmp", "webp": "webp"}.get(ext, "jpeg")
    return {"success": True, "data": f"data:image/{mime};base64,{data}"}


@router.post("/analyze")
async def analyze(req: AnalyticsRequest):
    info = dataset_manager.load_dataset(req.root_dir)
    if not info.is_valid:
        return {"success": False, "error": "数据集无效"}
    result = dataset_manager.compute_analytics(info)
    return {"success": True, "data": result}


@router.post("/split")
async def split_sse(req: SplitRequest):
    """SSE 流式推送拆分进度。"""
    info = dataset_manager.load_dataset(req.root_dir)
    def generate():
        for event in dataset_splitter.split_dataset(
            info, req.output_dir,
            req.train_ratio, req.val_ratio, req.test_ratio,
            req.seed, req.move
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
