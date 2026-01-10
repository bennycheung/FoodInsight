"""Data models for detection results."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Detection:
    """Single detection result from YOLO."""

    class_id: int
    class_name: str
    confidence: float
    bbox: List[float] = field(default_factory=list)  # [x1, y1, x2, y2]

    @property
    def x1(self) -> float:
        return self.bbox[0] if len(self.bbox) >= 1 else 0.0

    @property
    def y1(self) -> float:
        return self.bbox[1] if len(self.bbox) >= 2 else 0.0

    @property
    def x2(self) -> float:
        return self.bbox[2] if len(self.bbox) >= 3 else 0.0

    @property
    def y2(self) -> float:
        return self.bbox[3] if len(self.bbox) >= 4 else 0.0

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class TrackedDetection(Detection):
    """Detection with persistent tracking ID."""

    track_id: int = -1

    @classmethod
    def from_detection(cls, detection: Detection, track_id: int) -> "TrackedDetection":
        return cls(
            class_id=detection.class_id,
            class_name=detection.class_name,
            confidence=detection.confidence,
            bbox=detection.bbox.copy(),
            track_id=track_id,
        )
