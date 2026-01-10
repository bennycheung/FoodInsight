"""Privacy pipeline for ROI masking and blur."""

import logging
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class PrivacyPipeline:
    """Apply privacy masking to camera frames.

    Blurs areas outside the configured ROI to protect privacy
    while still showing the snack shelf area clearly.
    """

    def __init__(self, blur_intensity: int = 51):
        """Initialize privacy pipeline.

        Args:
            blur_intensity: Gaussian blur kernel size (must be odd)
        """
        # Ensure blur intensity is odd
        self.blur_intensity = blur_intensity if blur_intensity % 2 == 1 else blur_intensity + 1
        self.roi: Optional[Dict[str, int]] = None

    def set_roi(self, roi: Optional[Dict[str, int]]) -> None:
        """Set the Region of Interest.

        Args:
            roi: Dictionary with x1, y1, x2, y2 keys, or None for full frame
        """
        self.roi = roi
        if roi:
            logger.info(f"ROI set to: ({roi['x1']}, {roi['y1']}) -> ({roi['x2']}, {roi['y2']})")
        else:
            logger.info("ROI cleared - using full frame")

    def process_for_display(self, frame: np.ndarray) -> np.ndarray:
        """Apply blur outside ROI for admin display.

        Args:
            frame: BGR image as numpy array

        Returns:
            Processed frame with blur outside ROI
        """
        if self.roi is None:
            return frame

        x1, y1, x2, y2 = self._get_roi_coords(frame.shape)

        # Blur entire frame
        blurred = cv2.GaussianBlur(
            frame,
            (self.blur_intensity, self.blur_intensity),
            0
        )

        # Restore ROI region
        result = blurred.copy()
        result[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

        # Draw ROI border
        cv2.rectangle(result, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return result

    def crop_for_detection(self, frame: np.ndarray) -> np.ndarray:
        """Crop frame to ROI for detection processing.

        Args:
            frame: BGR image as numpy array

        Returns:
            Cropped frame containing only ROI region
        """
        if self.roi is None:
            return frame

        x1, y1, x2, y2 = self._get_roi_coords(frame.shape)
        return frame[y1:y2, x1:x2].copy()

    def adjust_detections(
        self,
        detections: List,
        frame_shape: Tuple[int, int, int]
    ) -> List:
        """Adjust detection coordinates from ROI back to full frame.

        Args:
            detections: List of detection objects with bbox attribute
            frame_shape: Original frame shape (height, width, channels)

        Returns:
            Detections with adjusted bbox coordinates
        """
        if self.roi is None:
            return detections

        x1, y1, _, _ = self._get_roi_coords(frame_shape)

        for det in detections:
            if hasattr(det, 'bbox') and len(det.bbox) >= 4:
                det.bbox[0] += x1  # x1
                det.bbox[1] += y1  # y1
                det.bbox[2] += x1  # x2
                det.bbox[3] += y1  # y2

        return detections

    def _get_roi_coords(
        self,
        frame_shape: Tuple[int, ...]
    ) -> Tuple[int, int, int, int]:
        """Get ROI coordinates, clamped to frame bounds.

        Args:
            frame_shape: Frame shape (height, width, ...)

        Returns:
            Tuple of (x1, y1, x2, y2)
        """
        height, width = frame_shape[:2]

        x1 = max(0, min(self.roi["x1"], width - 1))
        y1 = max(0, min(self.roi["y1"], height - 1))
        x2 = max(x1 + 1, min(self.roi["x2"], width))
        y2 = max(y1 + 1, min(self.roi["y2"], height))

        return x1, y1, x2, y2

    @property
    def roi_offset(self) -> Tuple[int, int]:
        """Get ROI offset for coordinate adjustment."""
        if self.roi is None:
            return (0, 0)
        return (self.roi["x1"], self.roi["y1"])

    @property
    def has_roi(self) -> bool:
        """Check if ROI is configured."""
        return self.roi is not None
