"""
data_prep.py — 数据准备模块 FastAPI 路由
包含：视频信息、SSE 抽帧、图像扫描、删除、重命名预览/执行
"""
import json
import asyncio
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

from backend.core import frame_extractor, image_cleaner, batch_renamer

router = APIRouter(prefix="/api/data-prep", tags=["data-prep"])


# ── 模型定义 ─────────────────────────────────────────────
class VideoInfoRequest(BaseModel):
    video_path: str


class ExtractParams(BaseModel):
    video_path: str
    output_dir: str
    mode: str = "time"          # "time" | "frame"
    interval: float = 1.0
    prefix: str = "frame"


class ScanRequest(BaseModel):
    folder_path: str
    min_width: int = 0
    min_height: int = 0
    min_size_kb: int = 0


class DeleteRequest(BaseModel):
    paths: List[str]


class RenamePreviewRequest(BaseModel):
    source_folder: str
    output_folder: str
    prefix: str = "image"
    ext: str = ".jpg"
    start_seq: int = -1
    zero_pad: int = 6


class RenameExecuteRequest(BaseModel):
    entries: List[dict]


# ── 端点 ─────────────────────────────────────────────────
@router.post("/video-info")
async def get_video_info(req: VideoInfoRequest):
    info = frame_extractor.get_video_info(req.video_path)
    if not info:
        return {"success": False, "error": "无法读取视频信息"}
    return {"success": True, "data": info}


@router.post("/extract-frames")
async def extract_frames_sse(req: ExtractParams):
    """SSE 流式推送抽帧进度。"""
    def generate():
        for event in frame_extractor.extract_frames(
            req.video_path, req.output_dir,
            req.mode, req.interval, req.prefix
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/scan-images")
async def scan_images_sse(req: ScanRequest):
    """SSE 流式推送扫描进度。"""
    def generate():
        for event in image_cleaner.scan_images(
            req.folder_path, req.min_width, req.min_height, req.min_size_kb
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/delete-images")
async def delete_images(req: DeleteRequest):
    result = image_cleaner.delete_files(req.paths)
    return {"success": True, "data": result}


@router.post("/rename-preview")
async def rename_preview(req: RenamePreviewRequest):
    entries = batch_renamer.preview_rename(
        req.source_folder, req.output_folder,
        req.prefix, req.ext, req.start_seq, req.zero_pad
    )
    return {"success": True, "data": entries, "count": len(entries)}


@router.post("/rename-execute")
async def rename_execute(req: RenameExecuteRequest):
    result = batch_renamer.execute_rename(req.entries)
    return {"success": True, "data": result}
