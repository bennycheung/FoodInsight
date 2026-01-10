"""Motion detection for CPU efficiency."""

import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class MotionDetector:
    """Detect motion in camera frames using frame differencing.

    Motion detection is used to trigger expensive YOLO inference
    only when there's activity in the frame.
    """

    def __init__(
        self,
        threshold: float = 0.02,
        blur_size: int = 21,
        cooldown_frames: int = 30,
    ):
        """Initialize motion detector.

        Args:
            threshold: Minimum motion score (0-1) to trigger detection.
                      0.02 = 2% of pixels changed
            blur_size: Gaussian blur kernel size (must be odd)
            cooldown_frames: Frames to continue detection after motion stops
        """
        self.threshold = threshold
        self.blur_size = blur_size
        self.cooldown_frames = cooldown_frames
        self.prev_frame: Optional[np.ndarray] = None
        self.motion_cooldown: int = 0
        self.last_motion_score: float = 0.0

    def detect(self, frame: np.ndarray) -> bool:
        """Check if motion is detected in frame.

        Args:
            frame: BGR image as numpy array

        Returns:
            True if motion detected or in cooldown period
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)

        # First frame - always run detection
        if self.prev_frame is None:
            self.prev_frame = gray
            return True

        # Calculate frame difference
        diff = cv2.absdiff(self.prev_frame, gray)
        self.last_motion_score = np.mean(diff) / 255.0

        self.prev_frame = gray

        # Check if motion exceeds threshold
        if self.last_motion_score > self.threshold:
            self.motion_cooldown = self.cooldown_frames
            return True

        # In cooldown period
        if self.motion_cooldown > 0:
            self.motion_cooldown -= 1
            return True

        return False

    def reset(self) -> None:
        """Reset the motion detector state."""
        self.prev_frame = None
        self.motion_cooldown = 0
        self.last_motion_score = 0.0

    @property
    def is_active(self) -> bool:
        """Check if motion detection is currently active."""
        return self.motion_cooldown > 0 or self.last_motion_score > self.threshold
