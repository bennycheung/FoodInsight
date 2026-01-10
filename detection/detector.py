"""YOLO11n snack detector wrapper."""

import logging
from typing import List, Optional

import numpy as np

from .models import Detection

logger = logging.getLogger(__name__)


class SnackDetector:
    """YOLO11n detector for snack items.

    Uses NCNN format for CPU-optimized inference on Raspberry Pi.
    """

    def __init__(
        self,
        model_path: str,
        confidence: float = 0.4,
        input_size: int = 640,
    ):
        """Initialize the snack detector.

        Args:
            model_path: Path to YOLO11n NCNN model directory
            confidence: Minimum confidence threshold for detections
            input_size: Input image size for inference (320 or 640)
        """
        self.model_path = model_path
        self.confidence = confidence
        self.input_size = input_size
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the YOLO model."""
        try:
            from ultralytics import YOLO

            logger.info(f"Loading model from {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info("Model loaded successfully")
        except ImportError:
            logger.warning(
                "ultralytics not installed. Running in mock mode for development."
            )
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Run detection on a single frame.

        Args:
            frame: BGR image as numpy array

        Returns:
            List of Detection objects
        """
        if self.model is None:
            return self._mock_detect(frame)

        try:
            results = self.model.predict(
                frame,
                conf=self.confidence,
                verbose=False,
                imgsz=self.input_size,
            )
            return self._parse_results(results[0])
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []

    def _parse_results(self, result) -> List[Detection]:
        """Parse YOLO results into Detection objects."""
        detections = []
        if result.boxes is None:
            return detections

        for box in result.boxes:
            detections.append(
                Detection(
                    class_id=int(box.cls),
                    class_name=result.names[int(box.cls)],
                    confidence=float(box.conf),
                    bbox=box.xyxy[0].tolist(),
                )
            )
        return detections

    def _mock_detect(self, frame: np.ndarray) -> List[Detection]:
        """Mock detection for development without model."""
        # Return empty list in mock mode
        return []

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None
