import logging
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO

from config import get_settings

logger = logging.getLogger(__name__)

# Class mapping sesuai spesifikasi model best.pt
CLASS_MAPPING: dict[int, str] = {
    0: "helmet",
    1: "no-helmet",
    2: "no-vest",
    3: "person",
    4: "vest",
}


class DetectorError(Exception):
    """Error saat proses inference."""


def decode_image(raw: bytes) -> np.ndarray | None:
    """Decode bytes gambar menjadi numpy array BGR (format OpenCV)."""
    if not raw:
        return None
    buffer = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    return image


class Detector:
    """Wrapper YOLO. Model di-load sekali, bukan per request."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._model: YOLO | None = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        model_path = Path(self._settings.MODEL_PATH)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file tidak ditemukan di: {model_path.resolve()}. "
                f"Letakkan best.pt di folder ai/ atau ubah MODEL_PATH di .env."
            )
        logger.info("Loading YOLO model from %s", model_path)
        self._model = YOLO(str(model_path))
        logger.info("YOLO model loaded. Classes: %s", self._model.names)

    def predict(self, image: np.ndarray) -> dict[str, Any]:
        if self._model is None:
            raise DetectorError("YOLO model belum di-load.")

        start = time.perf_counter()
        results = self._model.predict(
            source=image,
            conf=self._settings.CONFIDENCE_THRESHOLD,
            iou=self._settings.IOU_THRESHOLD,
            imgsz=self._settings.IMAGE_SIZE,
            verbose=False,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        result = results[0]
        height, width = result.orig_shape[:2]

        detections: list[dict[str, Any]] = []
        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]

            detections.append(
                {
                    "class_id": cls_id,
                    "class_name": CLASS_MAPPING.get(cls_id, f"unknown-{cls_id}"),
                    "confidence": round(confidence, 4),
                    "bbox": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2),
                    },
                }
            )

        return {
            "width": int(width),
            "height": int(height),
            "inference_time_ms": round(elapsed_ms, 2),
            "detections": detections,
        }


# Singleton instance — di-load pada startup aplikasi (lifespan)
detector = Detector()