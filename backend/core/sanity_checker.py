"""
sanity_checker.py — 数据集一致性体检（纯 Python，生成器）
"""
import os
from typing import Iterator

from backend.core.dataset_manager import DatasetInfo, parse_yolo_labels, IMG_EXTS


def check_dataset(info: DatasetInfo) -> Iterator[dict]:
    """
    生成器：体检数据集，yield 进度 + 最终结果列表。
    """
    if not info.is_valid:
        yield {"type": "error", "error": "数据集目录无效"}
        return

    img_stems = {}
    if info.images_dir:
        for f in os.listdir(info.images_dir):
            if os.path.splitext(f)[1].lower() in IMG_EXTS:
                stem = os.path.splitext(f)[0]
                img_stems[stem] = os.path.join(info.images_dir, f)

    lbl_stems = {}
    if info.labels_dir and os.path.isdir(info.labels_dir):
        for f in os.listdir(info.labels_dir):
            if f.endswith(".txt"):
                stem = os.path.splitext(f)[0]
                lbl_stems[stem] = os.path.join(info.labels_dir, f)

    total = len(img_stems) + len(lbl_stems)
    done = 0
    issues = []
    num_classes = len(info.classes)

    # 1. 有图无标注
    for stem, img_path in img_stems.items():
        done += 1
        yield {"type": "progress", "done": done, "total": total,
               "percent": round(done / total * 100, 1) if total else 100,
               "desc": f"检查图片: {os.path.basename(img_path)}"}
        if stem not in lbl_stems:
            issues.append({
                "category": "有图无标注",
                "path": img_path.replace("\\", "/"),
                "filename": os.path.basename(img_path),
                "detail": "images/ 中无对应 .txt 标注文件",
            })

    # 2. 有标注无图 / 空标注 / 类别越界
    for stem, lbl_path in lbl_stems.items():
        done += 1
        yield {"type": "progress", "done": done, "total": total,
               "percent": round(done / total * 100, 1) if total else 100,
               "desc": f"检查标注: {os.path.basename(lbl_path)}"}

        if stem not in img_stems:
            issues.append({
                "category": "有标注无图",
                "path": lbl_path.replace("\\", "/"),
                "filename": os.path.basename(lbl_path),
                "detail": "labels/ 中无对应图片",
            })
            continue

        labels = parse_yolo_labels(lbl_path)
        if not labels:
            issues.append({
                "category": "空标注",
                "path": lbl_path.replace("\\", "/"),
                "filename": os.path.basename(lbl_path),
                "detail": "标注文件内容为空",
            })
            continue

        if num_classes > 0:
            bad = [lb["class_id"] for lb in labels
                   if lb["class_id"] < 0 or lb["class_id"] >= num_classes]
            if bad:
                issues.append({
                    "category": "类别越界",
                    "path": lbl_path.replace("\\", "/"),
                    "filename": os.path.basename(lbl_path),
                    "detail": f"无效类别 ID: {bad}（共 {num_classes} 类）",
                })

    yield {"type": "done", "issues": issues, "total_issues": len(issues)}


def remove_orphan_labels(issues: list) -> dict:
    """删除 '有标注无图' 和 '空标注' 类型的标注文件（不删图片）。"""
    to_delete = [i["path"] for i in issues
                 if i["category"] in ("有标注无图", "空标注")]
    success, failed = 0, []
    for p in to_delete:
        try:
            os.remove(p)
            success += 1
        except Exception:
            failed.append(p)
    return {"success": success, "failed": failed, "deleted_count": success}
