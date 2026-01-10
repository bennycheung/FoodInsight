"""Application settings management."""

import json
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .platform import get_platform_config


CONFIG_PATH = Path("/opt/foodinsight/config.json")
DEFAULT_MODEL_PATH = "/opt/foodinsight/models/yolo11n_ncnn_model"


@dataclass
class ROI:
    """Region of Interest coordinates."""

    x1: int
    y1: int
    x2: int
    y2: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ROI":
        return cls(**data)


@dataclass
class Settings:
    """Application settings with platform-aware defaults."""

    # Machine identification
    machine_id: str = "foodinsight-edge-001"

    # Model settings
    model_path: str = DEFAULT_MODEL_PATH
    confidence_threshold: float = 0.4

    # Detection settings (platform-specific defaults)
    input_size: int = field(default_factory=lambda: get_platform_config().input_size)
    process_every_n_frames: int = field(
        default_factory=lambda: get_platform_config().process_every_n_frames
    )
    motion_threshold: float = field(
        default_factory=lambda: get_platform_config().motion_threshold
    )

    # Inventory settings
    debounce_frames: int = 10
    batch_timeout: float = field(
        default_factory=lambda: get_platform_config().batch_timeout
    )

    # Detection filtering - only report these classes (empty list = all classes)
    # Default includes food-related COCO classes
    allowed_classes: list = field(default_factory=lambda: [
        "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl",
        "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
        "hot dog", "pizza", "donut", "cake",
    ])

    # Privacy settings
    blur_intensity: int = 51
    roi: Optional[ROI] = None

    # Cloud API settings
    api_url: str = "https://foodinsight-api.run.app"
    api_key: str = ""

    # Admin portal settings
    admin_port: int = 80
    admin_host: str = "0.0.0.0"

    # Camera settings (OpenCV only, ignored on RPi with picamera2)
    # 0 = first camera (often iPhone via Continuity Camera on Mac)
    # 1 = second camera (often built-in FaceTime camera on Mac)
    camera_index: int = 0

    def save(self, path: Path = CONFIG_PATH) -> None:
        """Save settings to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        if self.roi:
            data["roi"] = self.roi.to_dict()
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Settings":
        """Load settings from JSON file."""
        if not path.exists():
            return cls()

        with open(path, "r") as f:
            data = json.load(f)

        roi_data = data.pop("roi", None)
        settings = cls(**data)
        if roi_data:
            settings.roi = ROI.from_dict(roi_data)
        return settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings.load()


def reload_settings() -> Settings:
    """Reload settings from disk, clearing cache."""
    get_settings.cache_clear()
    return get_settings()
