"""Platform detection and configuration for RPi 4/5 support."""

from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class PlatformConfig:
    """Platform-specific detection parameters."""

    platform: str
    input_size: int  # YOLO input resolution
    process_every_n_frames: int  # Frame skipping
    motion_threshold: float  # Motion sensitivity
    batch_timeout: float  # API batch interval (seconds)


PLATFORM_CONFIGS = {
    "rpi5": PlatformConfig(
        platform="rpi5",
        input_size=640,  # Full resolution
        process_every_n_frames=1,  # Every frame
        motion_threshold=0.02,  # Standard sensitivity
        batch_timeout=1.0,  # 1 second batching
    ),
    "rpi4": PlatformConfig(
        platform="rpi4",
        input_size=320,  # Reduced for performance
        process_every_n_frames=3,  # Every 3rd frame
        motion_threshold=0.015,  # More sensitive (compensate for skipping)
        batch_timeout=2.0,  # Longer batch window
    ),
    "unknown": PlatformConfig(
        platform="unknown",
        input_size=320,  # Conservative default
        process_every_n_frames=2,
        motion_threshold=0.02,
        batch_timeout=1.5,
    ),
}


def detect_platform() -> str:
    """Detect RPi model from /proc/device-tree/model."""
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read().lower()
            if "raspberry pi 5" in model:
                return "rpi5"
            elif "raspberry pi 4" in model:
                return "rpi4"
    except FileNotFoundError:
        pass
    return "unknown"


@lru_cache(maxsize=1)
def get_platform_config() -> PlatformConfig:
    """Get configuration for detected platform (cached)."""
    platform = detect_platform()
    return PLATFORM_CONFIGS[platform]
