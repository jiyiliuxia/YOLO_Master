"""
dataset_manager.py — 数据集目录结构加载与解析（纯 Python）
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}


@dataclass
class DatasetInfo:
    root_dir: str = ""
    images_dir: str = ""
    labels_dir: str = ""
    classes_file: str = ""
    classes: List[str] = field(default_factory=list)
    total_images: int = 0
    labeled_images: int = 0
    unlabeled_images: int = 0
    total_instances: int = 0
    is_valid: bool = False

    def to_dict(self) -> dict:
        return {
            "root_dir": self.root_dir.replace("\\", "/"),
            "images_dir": self.images_dir.replace("\\", "/"),
            "labels_dir": self.labels_dir.replace("\\", "/"),
            "classes_file": self.classes_file.replace("\\", "/"),
            "classes": self.classes,
            "total_images": self.total_images,
            "labeled_images": self.labeled_images,
            "unlabeled_images": self.unlabeled_images,
            "total_instances": self.total_instances,
            "is_valid": self.is_valid,
        }


def load_dataset(root_dir: str) -> DatasetInfo:
    """加载数据集目录，返回 DatasetInfo。"""
    info = DatasetInfo(root_dir=root_dir)
    if not os.path.isdir(root_dir):
        return info

    for name in ("images", "image", "imgs", "img"):
        c = os.path.join(root_dir, name)
        if os.path.isdir(c): info.images_dir = c; break

    for name in ("labels", "label", "annotations"):
        c = os.path.join(root_dir, name)
        if os.path.isdir(c): info.labels_dir = c; break

    for name in ("classes.txt", "obj.names", "labels.txt"):
        c = os.path.join(root_dir, name)
        if os.path.isfile(c): info.classes_file = c; break

    if info.classes_file:
        with open(info.classes_file, "r", encoding="utf-8") as f:
            info.classes = [l.strip() for l in f if l.strip()]

    if info.images_dir:
        stems = [
            os.path.splitext(f)[0]
            for f in os.listdir(info.images_dir)
            if os.path.splitext(f)[1].lower() in IMG_EXTS
        ]
        info.total_images = len(stems)
        labeled = 0
        instances = 0
        for stem in stems:
            txt = os.path.join(info.labels_dir, stem + ".txt") if info.labels_dir else ""
            if txt and os.path.isfile(txt):
                lines = [l.strip() for l in open(txt, encoding="utf-8") if l.strip()]
                if lines:
                    labeled += 1
                    instances += len(lines)
        info.labeled_images = labeled
        info.unlabeled_images = info.total_images - labeled
        info.total_instances = instances

    info.is_valid = bool(info.images_dir)
    return info


def get_image_list(info: DatasetInfo) -> List[str]:
    if not info.images_dir or not os.path.isdir(info.images_dir):
        return []
    return sorted([
        os.path.join(info.images_dir, f).replace("\\", "/")
        for f in os.listdir(info.images_dir)
        if os.path.splitext(f)[1].lower() in IMG_EXTS
    ])


def get_label_path(info: DatasetInfo, img_path: str) -> Optional[str]:
    if not info.labels_dir:
        return None
    stem = os.path.splitext(os.path.basename(img_path))[0]
    return os.path.join(info.labels_dir, stem + ".txt").replace("\\", "/")


def parse_yolo_labels(txt_path: str) -> List[dict]:
    results = []
    if not txt_path or not os.path.isfile(txt_path):
        return results
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 5:
                try:
                    results.append({
                        "class_id": int(parts[0]),
                        "cx": float(parts[1]), "cy": float(parts[2]),
                        "w":  float(parts[3]), "h":  float(parts[4]),
                    })
                except ValueError:
                    pass
    return results


def compute_class_distribution(info: DatasetInfo) -> dict:
    dist = {}
    if not info.labels_dir or not os.path.isdir(info.labels_dir):
        return dist
    for fname in os.listdir(info.labels_dir):
        if not fname.endswith(".txt"):
            continue
        for lbl in parse_yolo_labels(os.path.join(info.labels_dir, fname)):
            cid = lbl["class_id"]
            dist[cid] = dist.get(cid, 0) + 1
    return dist


def compute_analytics(info: DatasetInfo) -> dict:
    """完整分析：类别分布 + 框尺寸统计。"""
    dist = compute_class_distribution(info)
    class_names = info.classes
    bar_data = [
        {"class_id": cid, "name": class_names[cid] if 0 <= cid < len(class_names) else str(cid), "count": cnt}
        for cid, cnt in sorted(dist.items())
    ]

    points, total_inst, sum_w, sum_h = [], 0, 0.0, 0.0
    if info.labels_dir and os.path.isdir(info.labels_dir):
        for fname in os.listdir(info.labels_dir):
            if not fname.endswith(".txt"):
                continue
            for lbl in parse_yolo_labels(os.path.join(info.labels_dir, fname)):
                points.append({"w": lbl["w"], "h": lbl["h"], "class_id": lbl["class_id"]})
                sum_w += lbl["w"]; sum_h += lbl["h"]; total_inst += 1

    # 限制散点数据量
    import random
    if len(points) > 3000:
        points = random.sample(points, 3000)

    max_cnt = max(dist.values()) if dist else 1
    min_cnt = min(dist.values()) if dist else 0
    long_tail = (min_cnt / max_cnt if max_cnt else 1.0) < 0.1 if len(dist) > 1 else False

    return {
        "bar_data": bar_data,
        "scatter_points": points,
        "total_instances": total_inst,
        "avg_width": round(sum_w / total_inst, 4) if total_inst else 0,
        "avg_height": round(sum_h / total_inst, 4) if total_inst else 0,
        "long_tail_warning": long_tail,
        "class_count": len(dist),
    }
