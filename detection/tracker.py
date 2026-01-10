"""ByteTrack object tracking integration."""

import logging
from pathlib import Path
from typing import List, Optional

import numpy as np

from .models import TrackedDetection

logger = logging.getLogger(__name__)

# Default ByteTrack configuration
DEFAULT_TRACKER_CONFIG = """
tracker_type: bytetrack
track_high_thresh: 0.5
track_low_thresh: 0.1
new_track_thresh: 0.6
track_buffer: 30
match_thresh: 0.8
fuse_score: true
"""


class TrackedDetector:
    """YOLO detector with ByteTrack object tracking.

    Maintains persistent object IDs across frames for tracking
    individual snack items.
    """

    def __init__(
        self,
        model_path: str,
        confidence: float = 0.4,
        input_size: int = 640,
        tracker_config: Optional[str] = None,
    ):
        """Initialize tracked detector.

        Args:
            model_path: Path to YOLO11n NCNN model directory
            confidence: Minimum confidence threshold
            input_size: Input image size for inference
            tracker_config: Path to ByteTrack YAML config (or None for default)
        """
        self.model_path = model_path
        self.confidence = confidence
        self.input_size = input_size
        self.tracker_config = tracker_config or self._create_default_config()
        self.model = None
        self._load_model()

    def _create_default_config(self) -> str:
        """Create default ByteTrack config file."""
        config_dir = Path("/tmp/foodinsight")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "bytetrack.yaml"

        if not config_path.exists():
            config_path.write_text(DEFAULT_TRACKER_CONFIG)

        return str(config_path)

    def _load_model(self) -> None:
        """Load the YOLO model."""
        try:
            from ultralytics import YOLO

            logger.info(f"Loading YOLO model from {self.model_path}")
            self.model = YOLO(self.model_path, task="detect")
            logger.info(f"YOLO model loaded successfully - {len(self.model.names)} classes")
        except ImportError:
            logger.warning(
                "ultralytics not installed. Running in mock mode for development."
            )
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def detect_and_track(self, frame: np.ndarray) -> List[TrackedDetection]:
        """Run detection with tracking on a single frame.

        Args:
            frame: BGR image as numpy array

        Returns:
            List of TrackedDetection objects with persistent IDs
        """
        if self.model is None:
            logger.debug("Model not loaded, using mock detection")
            return self._mock_track(frame)

        try:
            results = self.model.track(
                frame,
                tracker=self.tracker_config,
                persist=True,  # Maintain track IDs across calls
                conf=self.confidence,
                verbose=False,
                imgsz=self.input_size,
            )
            detections = self._parse_tracked_results(results[0])
            if detections:
                logger.info(f"Detected {len(detections)} objects: {[d.class_name for d in detections]}")
            return detections
        except Exception as e:
            logger.error(f"Tracking failed: {e}")
            return []

    def _parse_tracked_results(self, result) -> List[TrackedDetection]:
        """Parse YOLO tracking results into TrackedDetection objects."""
        detections = []

        if result.boxes is None or result.boxes.id is None:
            return detections

        for i, box in enumerate(result.boxes):
            track_id = int(result.boxes.id[i])
            detections.append(
                TrackedDetection(
                    track_id=track_id,
                    class_id=int(box.cls),
                    class_name=result.names[int(box.cls)],
                    confidence=float(box.conf),
                    bbox=box.xyxy[0].tolist(),
                )
            )

        return detections

    def _mock_track(self, frame: np.ndarray) -> List[TrackedDetection]:
        """Mock tracking for development without model."""
        return []

    def reset_tracking(self) -> None:
        """Reset tracking state (clear all track IDs)."""
        if self.model is not None:
            try:
                # Reinitialize model to reset tracker state
                from ultralytics import YOLO

                self.model = YOLO(self.model_path)
            except Exception as e:
                logger.warning(f"Failed to reset tracking: {e}")

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None
