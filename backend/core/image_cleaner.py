"""
image_cleaner.py — 图像清洗核心逻辑（纯 Python）
"""
import os
from dataclasses import dataclass
from typing import Iterator, List

from PIL import Image, UnidentifiedImageError

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}


@dataclass
class ImageCheckResult:
    path: str
    width: int = 0
    height: int = 0
    size_bytes: int = 0
    is_corrupted: bool = False
    below_resolution: bool = False
    below_filesize: bool = False

    @property
    def should_remove(self) -> bool:
        return self.is_corrupted or self.below_resolution or self.below_filesize

    @property
    def reason(self) -> str:
        r = []
        if self.is_corrupted:     r.append("损坏")
        if self.below_resolution: r.append(f"分辨率不足({self.width}x{self.height})")
        if self.below_filesize:   r.append(f"文件过小({self.size_bytes//1024}KB)")
        return "、".join(r) if r else "正常"

    def to_dict(self) -> dict:
        return {
            "path": self.path.replace("\\", "/"),
            "filename": os.path.basename(self.path),
            "width": self.width,
            "height": self.height,
            "size_kb": round(self.size_bytes / 1024, 1),
            "should_remove": self.should_remove,
            "reason": self.reason,
        }


def scan_images(
    folder_path: str,
    min_width: int = 0,
    min_height: int = 0,
    min_size_kb: int = 0,
) -> Iterator[dict]:
    """
    生成器：扫描文件夹，每处理一张图 yield 进度，
    最后 yield done 事件含完整结果列表。
    """
    if not os.path.isdir(folder_path):
        yield {"type": "error", "error": f"目录不存在: {folder_path}"}
        return

    all_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(folder_path)
        for f in files
        if os.path.splitext(f)[1].lower() in IMG_EXTS
    ]
    total = len(all_files)
    results: List[ImageCheckResult] = []

    for idx, fpath in enumerate(all_files):
        size_bytes = os.path.getsize(fpath)
        result = ImageCheckResult(path=fpath, size_bytes=size_bytes)

        try:
            with Image.open(fpath) as img:
                img.verify()
            with Image.open(fpath) as img:
                result.width, result.height = img.size
        except Exception:
            result.is_corrupted = True

        if not result.is_corrupted:
            if min_width > 0 and min_height > 0:
                if result.width < min_width or result.height < min_height:
                    result.below_resolution = True
            if min_size_kb > 0 and size_bytes < min_size_kb * 1024:
                result.below_filesize = True

        results.append(result)
        yield {
            "type": "progress",
            "done": idx + 1,
            "total": total,
            "percent": round((idx + 1) / total * 100, 1) if total else 100,
            "current_file": os.path.basename(fpath),
        }

    bad = [r for r in results if r.should_remove]
    yield {
        "type": "done",
        "total": total,
        "bad_count": len(bad),
        "results": [r.to_dict() for r in results],
    }


def delete_files(paths: List[str]) -> dict:
    """删除文件列表，返回结果。"""
    success, failed = 0, []
    for p in paths:
        try:
            os.remove(p)
            success += 1
        except Exception:
            failed.append(p)
    return {"success": success, "failed": failed}
