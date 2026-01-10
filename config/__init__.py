"""FoodInsight Edge Configuration Module."""

from .settings import Settings, get_settings
from .platform import PlatformConfig, detect_platform, get_platform_config

__all__ = [
    "Settings",
    "get_settings",
    "PlatformConfig",
    "detect_platform",
    "get_platform_config",
]
