"""
frame_extractor.py — 视频抽帧核心逻辑（纯 Python，无 PyQt6）
使用生成器 yield 进度事件，供 FastAPI SSE 消费。
"""
import os
import cv2
from typing import Iterator, Optional

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def get_video_info(video_path: str) -> dict:
    """读取视频基础信息。"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {}
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return {
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "width": width,
        "height": height,
        "duration_sec": round(total_frames / fps if fps else 0, 2),
    }


def extract_frames(
    video_path: str,
    output_dir: str,
    mode: str = "time",       # "time" | "frame"
    interval: float = 1.0,
    prefix: str = "frame",
    jpeg_quality: int = 95,
) -> Iterator[dict]:
    """
    生成器：逐帧提取，每保存一帧 yield 一条进度事件。
    事件结构: {type, frame_idx, total_frames, saved, thumb_path, error?}
    """
    if not os.path.isfile(video_path):
        yield {"type": "error", "error": f"视频文件不存在: {video_path}"}
        return

    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        yield {"type": "error", "error": f"无法打开视频: {video_path}"}
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, int(fps * interval) if mode == "time" else int(interval))

    saved_count = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            filename = f"{prefix}_{saved_count:06d}.jpg"
            out_path = os.path.join(output_dir, filename)
            cv2.imwrite(out_path, frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            saved_count += 1
            yield {
                "type": "progress",
                "frame_idx": frame_idx,
                "total_frames": total_frames,
                "saved": saved_count,
                "thumb_path": out_path.replace("\\", "/"),
                "percent": round(frame_idx / total_frames * 100, 1) if total_frames else 0,
            }
        frame_idx += 1

    cap.release()
    yield {"type": "done", "saved": saved_count, "output_dir": output_dir.replace("\\", "/")}
