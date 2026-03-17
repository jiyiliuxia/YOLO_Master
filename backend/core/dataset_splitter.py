"""
dataset_splitter.py — 数据集拆分与 dataset.yaml 生成（纯 Python，生成器）
"""
import os
import random
import shutil
from typing import Iterator

import yaml

from backend.core.dataset_manager import DatasetInfo, IMG_EXTS


def split_dataset(
    info: DatasetInfo,
    output_dir: str,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
    move: bool = False,
) -> Iterator[dict]:
    """
    生成器：拆分数据集，yield 进度，最后 yield done（含 yaml 路径）。
    """
    if not info.is_valid or not info.images_dir:
        yield {"type": "error", "error": "数据集目录无效"}
        return

    total_r = train_ratio + val_ratio + test_ratio
    if total_r <= 0:
        yield {"type": "error", "error": "比例配置无效"}
        return

    train_r = train_ratio / total_r
    val_r   = val_ratio   / total_r

    all_imgs = sorted([
        f for f in os.listdir(info.images_dir)
        if os.path.splitext(f)[1].lower() in IMG_EXTS
    ])
    random.seed(seed)
    random.shuffle(all_imgs)

    n = len(all_imgs)
    n_train = int(n * train_r)
    n_val   = int(n * val_r)

    splits = {"train": all_imgs[:n_train], "val": all_imgs[n_train:n_train + n_val]}
    if test_ratio > 0:
        splits["test"] = all_imgs[n_train + n_val:]

    for split_name in splits:
        os.makedirs(os.path.join(output_dir, "images", split_name), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "labels", split_name), exist_ok=True)

    total_ops = sum(len(v) for v in splits.values()) * 2
    done = 0
    op = shutil.move if move else shutil.copy2
    counts = {}

    for split_name, file_list in splits.items():
        counts[split_name] = len(file_list)
        for fname in file_list:
            stem = os.path.splitext(fname)[0]
            src_img = os.path.join(info.images_dir, fname)
            dst_img = os.path.join(output_dir, "images", split_name, fname)
            if os.path.isfile(src_img):
                op(src_img, dst_img)
            done += 1
            yield {"type": "progress", "done": done, "total": total_ops,
                   "percent": round(done / total_ops * 100, 1),
                   "desc": f"[{split_name}] {fname}"}

            if info.labels_dir:
                src_lbl = os.path.join(info.labels_dir, stem + ".txt")
                dst_lbl = os.path.join(output_dir, "labels", split_name, stem + ".txt")
                if os.path.isfile(src_lbl):
                    op(src_lbl, dst_lbl)
            done += 1
            yield {"type": "progress", "done": done, "total": total_ops,
                   "percent": round(done / total_ops * 100, 1),
                   "desc": f"[{split_name}] {stem}.txt"}

    # 生成 dataset.yaml
    yaml_path = os.path.join(output_dir, "dataset.yaml")
    yaml_data = {
        "path": os.path.abspath(output_dir).replace("\\", "/"),
        "train": "images/train",
        "val":   "images/val",
    }
    if "test" in splits:
        yaml_data["test"] = "images/test"
    yaml_data["nc"]    = len(info.classes)
    yaml_data["names"] = info.classes or [str(i) for i in range(yaml_data["nc"])]
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_content = f.read()

    yield {
        "type": "done",
        "output_dir": output_dir.replace("\\", "/"),
        "yaml_path": yaml_path.replace("\\", "/"),
        "yaml_content": yaml_content,
        "counts": counts,
    }
