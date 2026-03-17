"""
batch_renamer.py — 批量重命名核心逻辑（纯 Python）
"""
import os
import re
from dataclasses import dataclass
from typing import List

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}


@dataclass
class RenameEntry:
    old_path: str
    new_path: str
    old_name: str
    new_name: str

    def to_dict(self) -> dict:
        return {
            "old_name": self.old_name,
            "new_name": self.new_name,
            "old_path": self.old_path.replace("\\", "/"),
            "new_path": self.new_path.replace("\\", "/"),
        }


def detect_max_sequence(folder: str, prefix: str, ext: str) -> int:
    """扫描目标目录，找出已有最大序列号（防冲突）。返回 -1 表示无已有文件。"""
    pattern = re.compile(
        rf"^{re.escape(prefix)}_(\d+){re.escape(ext)}$", re.IGNORECASE
    )
    max_seq = -1
    if not os.path.isdir(folder):
        return max_seq
    for fname in os.listdir(folder):
        m = pattern.match(fname)
        if m:
            max_seq = max(max_seq, int(m.group(1)))
    return max_seq


def preview_rename(
    source_folder: str,
    output_folder: str,
    prefix: str,
    ext: str = ".jpg",
    start_seq: int = -1,
    zero_pad: int = 6,
) -> List[dict]:
    """生成重命名预览列表（不执行）。"""
    if not os.path.isdir(source_folder):
        return []

    source_files = sorted([
        f for f in os.listdir(source_folder)
        if os.path.splitext(f)[1].lower() in IMG_EXTS
    ])
    if not source_files:
        return []

    if start_seq < 0:
        max_seq = detect_max_sequence(output_folder, prefix, ext)
        current_seq = max_seq + 1
    else:
        current_seq = start_seq

    entries = []
    for fname in source_files:
        old_path = os.path.join(source_folder, fname)
        new_name = f"{prefix}_{current_seq:0{zero_pad}d}{ext}"
        new_path = os.path.join(output_folder, new_name)
        entries.append(RenameEntry(
            old_path=old_path, new_path=new_path,
            old_name=fname, new_name=new_name,
        ))
        current_seq += 1

    return [e.to_dict() for e in entries]


def execute_rename(entries: List[dict]) -> dict:
    """执行预览列表中的重命名操作。"""
    dirs = {os.path.dirname(e["new_path"]) for e in entries}
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    success, failed = 0, []
    for e in entries:
        try:
            os.rename(e["old_path"], e["new_path"])
            success += 1
        except Exception:
            failed.append(e["old_path"])
    return {"success": success, "failed": failed}
