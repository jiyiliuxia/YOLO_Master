"""
inference_engine.py — ONNX 推理引擎
仅支持 .onnx 格式（ONNX Runtime with DirectML/CPU）。
如需使用 .pt 模型，请先用 ultralytics 将其转换为 .onnx：
    yolo export model=your_model.pt format=onnx
"""

import logging
import os
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# 单例引擎实例，供 router 使用
_engine: Optional["InferenceEngine"] = None


def get_engine() -> Optional["InferenceEngine"]:
    return _engine


def set_engine(engine: "InferenceEngine"):
    global _engine
    _engine = engine


class InferenceEngine:
    """
    ONNX Runtime 推理引擎：
      .onnx → ONNX Runtime (DirectML GPU 优先，自动回退到 CPU)

    注意：不再支持 .pt 格式。请使用以下命令转换：
        pip install ultralytics
        yolo export model=your_model.pt format=onnx
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.ext = Path(model_path).suffix.lower()
        self.model = None
        self.class_names: list[str] = []
        self.input_size: tuple[int, int] = (640, 640)  # (w, h)
        self._loaded = False
        self._backend = ""

        self._load()

    def _load(self):
        """加载模型，仅支持 .onnx 格式"""
        if self.ext == ".pt":
            raise ValueError(
                "不支持 .pt 格式直接推理（打包版本已移除 PyTorch 依赖）。\n"
                "请先将模型转换为 ONNX 格式：\n"
                "  pip install ultralytics\n"
                "  yolo export model=your_model.pt format=onnx"
            )
        elif self.ext == ".onnx":
            self._load_onnx()
        else:
            raise ValueError(f"不支持的模型格式：{self.ext}，请使用 .onnx 格式。")

        self._loaded = True
        logger.info("[InferenceEngine] 模型加载完成 backend=%s path=%s", self._backend, self.model_path)

    # ── .onnx 后端 ─────────────────────────────────────────────
    def _load_onnx(self):
        try:
            import onnxruntime as ort
        except ImportError as e:
            raise ImportError("未安装 onnxruntime-directml，请执行 pip install onnxruntime-directml") from e

        # 优先使用 DirectML（集显/独显），失败则回退到 CPU
        providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
        try:
            self.model = ort.InferenceSession(self.model_path, providers=providers)
            logger.info("[InferenceEngine] ONNX 使用 DirectML provider")
        except Exception as e:
            logger.warning("[InferenceEngine] DirectML 不可用（%s），回退到 CPU", e)
            self.model = ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])

        # 读取输入形状
        inp = self.model.get_inputs()[0]
        _, _, h, w = inp.shape
        if isinstance(h, int) and isinstance(w, int):
            self.input_size = (w, h)

        # 尝试从元数据读取类别名
        meta = self.model.get_modelmeta().custom_metadata_map
        if "names" in meta:
            import ast
            raw = meta["names"]
            names_dict = ast.literal_eval(raw)
            self.class_names = [names_dict[i] for i in sorted(names_dict)]

        self._backend = "onnxruntime"

    # ── 统一推理接口 ────────────────────────────────────────────
    def predict(
        self,
        image_bgr: np.ndarray,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ) -> dict:
        """
        推理单张 BGR 图像。
        返回：
          {
            "backend": "onnxruntime",
            "inference_ms": float,
            "image_size": [w, h],
            "boxes": [
              {"x1": int, "y1": int, "x2": int, "y2": int,
               "conf": float, "cls": int, "label": str}
            ]
          }
        """
        if not self._loaded:
            raise RuntimeError("模型尚未加载")

        h_orig, w_orig = image_bgr.shape[:2]
        t0 = time.perf_counter()

        boxes = self._predict_onnx(image_bgr, conf_threshold, iou_threshold)

        elapsed_ms = (time.perf_counter() - t0) * 1000

        return {
            "backend": self._backend,
            "inference_ms": round(elapsed_ms, 1),
            "image_size": [w_orig, h_orig],
            "boxes": boxes,
        }

    def _predict_onnx(self, image_bgr: np.ndarray, conf: float, iou: float) -> list[dict]:
        inp_w, inp_h = self.input_size
        orig_h, orig_w = image_bgr.shape[:2]

        # ── Letterbox 预处理（与 YOLO 训练时保持一致）────────────
        img_lb, scale, (pad_x, pad_y) = _letterbox(image_bgr, (inp_w, inp_h))
        img_lb = cv2.cvtColor(img_lb, cv2.COLOR_BGR2RGB)
        img_lb = img_lb.astype(np.float32) / 255.0
        img_lb = np.transpose(img_lb, (2, 0, 1))[np.newaxis]   # → NCHW

        input_name = self.model.get_inputs()[0].name
        outputs = self.model.run(None, {input_name: img_lb})

        pred = outputs[0]
        if pred.ndim == 3:
            pred = pred[0]              # 去掉 batch 维 → (C, N) 或 (N, C)

        # ── 维度规整：统一为 (num_anchors, 4+num_cls) ──────────
        # YOLOv8 ONNX 标准导出为 (4+num_cls, 8400)，需转置
        if pred.ndim == 2 and pred.shape[0] < pred.shape[1]:
            pred = pred.T               # → (8400, 4+num_cls)

        if pred.ndim != 2 or pred.shape[1] < 5:
            logger.warning("[ONNX] 输出格式异常，shape=%s，跳过", pred.shape)
            return []

        boxes = []
        for det in pred:
            cls_scores = det[4:]        # (num_cls,)
            if len(cls_scores) == 0:
                continue

            cls_idx = int(np.argmax(cls_scores))
            cls_conf = float(cls_scores[cls_idx])

            # ── 自动处理未激活 logit ────────────────────────────
            if cls_conf > 1.0 or cls_conf < 0.0:
                sig = 1.0 / (1.0 + np.exp(-np.clip(cls_scores, -500, 500)))
                cls_idx = int(np.argmax(sig))
                cls_conf = float(sig[cls_idx])

            if cls_conf < conf:
                continue

            # ── 坐标还原：letterbox 空间 → 原图空间 ──────────
            cx, cy, bw, bh = float(det[0]), float(det[1]), float(det[2]), float(det[3])
            x1 = int(np.clip((cx - bw / 2 - pad_x) / scale, 0, orig_w))
            y1 = int(np.clip((cy - bh / 2 - pad_y) / scale, 0, orig_h))
            x2 = int(np.clip((cx + bw / 2 - pad_x) / scale, 0, orig_w))
            y2 = int(np.clip((cy + bh / 2 - pad_y) / scale, 0, orig_h))

            if x2 <= x1 or y2 <= y1:
                continue

            label = (self.class_names[cls_idx]
                     if cls_idx < len(self.class_names)
                     else str(cls_idx))
            boxes.append({
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "conf": round(cls_conf, 4),
                "cls": cls_idx,
                "label": label,
            })

        return _nms(boxes, iou_threshold=iou)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def info(self) -> dict:
        return {
            "loaded": self._loaded,
            "backend": self._backend,
            "model_path": self.model_path,
            "class_names": self.class_names,
            "num_classes": len(self.class_names),
            "input_size": list(self.input_size),
        }


# ── Letterbox 预处理（保持宽高比 + 灰边填充）─────────────────────
def _letterbox(
    img: np.ndarray,
    new_shape: tuple = (640, 640),
    color: tuple = (114, 114, 114),
):
    """
    YOLO 标准 letterbox 缩放：保持宽高比，用灰边填充至目标尺寸。
    返回：(处理后图像, 缩放比例 scale, (pad_left, pad_top))
    坐标还原：orig_coord = (letterbox_coord - pad) / scale
    """
    h, w = img.shape[:2]
    new_w, new_h = new_shape
    scale = min(new_w / w, new_h / h)
    unpad_w = int(round(w * scale))
    unpad_h = int(round(h * scale))
    img = cv2.resize(img, (unpad_w, unpad_h), interpolation=cv2.INTER_LINEAR)
    # 计算对称填充量（偶数对称，奇数差1）
    pad_x = (new_w - unpad_w) / 2
    pad_y = (new_h - unpad_h) / 2
    left   = int(round(pad_x - 0.1))
    right  = int(round(pad_x + 0.1))
    top    = int(round(pad_y - 0.1))
    bottom = int(round(pad_y + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right,
                             cv2.BORDER_CONSTANT, value=color)
    return img, scale, (left, top)


# ── 辅助函数：IoU 计算 + NMS ───────────────────────────────────
def _iou(a: dict, b: dict) -> float:
    ix1 = max(a["x1"], b["x1"])
    iy1 = max(a["y1"], b["y1"])
    ix2 = min(a["x2"], b["x2"])
    iy2 = min(a["y2"], b["y2"])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = (a["x2"] - a["x1"]) * (a["y2"] - a["y1"])
    area_b = (b["x2"] - b["x1"]) * (b["y2"] - b["y1"])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _nms(boxes: list, iou_threshold: float = 0.45) -> list:
    """按类别分组做 NMS"""
    if not boxes:
        return []
    from collections import defaultdict
    by_cls = defaultdict(list)
    for b in boxes:
        by_cls[b["cls"]].append(b)

    kept = []
    for cls_boxes in by_cls.values():
        cls_boxes.sort(key=lambda x: x["conf"], reverse=True)
        while cls_boxes:
            best = cls_boxes.pop(0)
            kept.append(best)
            cls_boxes = [b for b in cls_boxes if _iou(best, b) < iou_threshold]
    return kept
