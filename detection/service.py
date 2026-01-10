"""Main detection service orchestrator."""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional, Tuple

import cv2
import numpy as np

from config import Settings, get_settings
from privacy import PrivacyPipeline

from .inventory import InventoryDelta, InventoryStateManager
from .models import TrackedDetection
from .motion import MotionDetector
from .tracker import TrackedDetector

logger = logging.getLogger(__name__)


@dataclass
class ServiceStatus:
    """Current service status."""

    status: str  # "initializing", "running", "stopped", "error"
    fps: float
    frame_count: int
    last_detection_time: Optional[datetime]
    motion_active: bool
    inventory: dict


class DetectionService:
    """Main detection service orchestrating all components.

    Coordinates camera capture, motion detection, object tracking,
    inventory management, and privacy masking.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        on_frame: Optional[Callable[[np.ndarray, List[TrackedDetection]], None]] = None,
        on_status: Optional[Callable[[ServiceStatus], None]] = None,
        on_delta: Optional[Callable[[InventoryDelta], None]] = None,
    ):
        """Initialize detection service.

        Args:
            settings: Application settings (uses cached if None)
            on_frame: Callback for processed frames (for admin preview)
            on_status: Callback for status updates
            on_delta: Callback for inventory deltas (for API push)
        """
        self.settings = settings or get_settings()

        # Initialize components
        self.tracker = TrackedDetector(
            model_path=self.settings.model_path,
            confidence=self.settings.confidence_threshold,
            input_size=self.settings.input_size,
        )
        self.motion = MotionDetector(
            threshold=self.settings.motion_threshold,
        )
        self.inventory = InventoryStateManager(
            machine_id=self.settings.machine_id,
            debounce_frames=self.settings.debounce_frames,
        )
        self.privacy = PrivacyPipeline(
            blur_intensity=self.settings.blur_intensity,
        )

        # Load ROI if configured
        if self.settings.roi:
            self.privacy.set_roi(self.settings.roi.to_dict())

        # Callbacks
        self.on_frame = on_frame
        self.on_status = on_status
        self.on_delta = on_delta

        # State
        self._running = False
        self._frame_count = 0
        self._fps = 0.0
        self._last_detection_time: Optional[datetime] = None
        self._last_detections: List[TrackedDetection] = []
        self._last_delta_time = time.time()

        # Camera
        self._camera = None
        self._current_frame: Optional[np.ndarray] = None

    async def start(self) -> None:
        """Start the detection service."""
        logger.info("Starting detection service...")
        logger.info(f"YOLO model loaded: {self.tracker.is_loaded}")
        logger.info(f"Model path: {self.settings.model_path}")
        self._running = True
        await self._init_camera()
        await self._run_loop()

    async def stop(self) -> None:
        """Stop the detection service."""
        logger.info("Stopping detection service...")
        self._running = False
        self._release_camera()

    async def _init_camera(self) -> None:
        """Initialize camera."""
        try:
            # Try picamera2 first (Raspberry Pi)
            try:
                from picamera2 import Picamera2

                self._camera = Picamera2()
                config = self._camera.create_still_configuration(
                    main={"size": (1280, 720), "format": "RGB888"}
                )
                self._camera.configure(config)
                self._camera.start()
                logger.info("Using picamera2")
                return
            except ImportError:
                pass

            # Fall back to OpenCV
            camera_index = self.settings.camera_index
            self._camera = cv2.VideoCapture(camera_index)
            if not self._camera.isOpened():
                raise RuntimeError(f"Failed to open camera at index {camera_index}")
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            logger.info(f"Using OpenCV VideoCapture (camera_index={camera_index})")

        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self._camera = None

    def _release_camera(self) -> None:
        """Release camera resources."""
        if self._camera is not None:
            try:
                if hasattr(self._camera, "stop"):
                    self._camera.stop()
                elif hasattr(self._camera, "release"):
                    self._camera.release()
            except Exception as e:
                logger.warning(f"Error releasing camera: {e}")
            self._camera = None

    def _capture_frame(self) -> Optional[np.ndarray]:
        """Capture a frame from camera."""
        if self._camera is None:
            return None

        try:
            if hasattr(self._camera, "capture_array"):
                # picamera2
                frame = self._camera.capture_array()
                # Convert RGB to BGR for OpenCV
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                # OpenCV
                ret, frame = self._camera.read()
                return frame if ret else None
        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")
            return None

    async def _run_loop(self) -> None:
        """Main detection loop."""
        frame_times = []
        frame_skip_counter = 0

        while self._running:
            loop_start = time.time()

            # Capture frame
            frame = self._capture_frame()
            if frame is None:
                await asyncio.sleep(0.1)
                continue

            self._current_frame = frame
            self._frame_count += 1

            # Frame skipping for lower-powered platforms
            frame_skip_counter += 1
            if frame_skip_counter < self.settings.process_every_n_frames:
                # Still update display with last detections
                if self.on_frame:
                    display_frame = self._create_display_frame(frame)
                    self.on_frame(display_frame, self._last_detections)
                await asyncio.sleep(0.01)
                continue
            frame_skip_counter = 0

            # Crop to ROI for detection
            detection_frame = self.privacy.crop_for_detection(frame)

            # Check for motion
            motion_detected = self.motion.detect(detection_frame)
            if motion_detected:
                # Run detection and tracking
                detections = self.tracker.detect_and_track(detection_frame)

                # Filter to allowed classes (if configured)
                if self.settings.allowed_classes:
                    detections = [
                        d for d in detections
                        if d.class_name in self.settings.allowed_classes
                    ]

                # Adjust coordinates back to full frame
                detections = self.privacy.adjust_detections(detections, frame.shape)

                # Update inventory
                self.inventory.update(detections)

                self._last_detections = detections
                self._last_detection_time = datetime.utcnow()

            # Create display frame
            display_frame = self._create_display_frame(frame)

            # Invoke frame callback
            if self.on_frame:
                self.on_frame(display_frame, self._last_detections)

            # Check for delta push
            await self._check_delta_push()

            # Calculate FPS
            frame_time = time.time() - loop_start
            frame_times.append(frame_time)
            if len(frame_times) > 30:
                frame_times.pop(0)
            self._fps = 1.0 / (sum(frame_times) / len(frame_times)) if frame_times else 0

            # Invoke status callback
            if self.on_status:
                self.on_status(self.get_status())

            # Small delay to prevent CPU overload
            await asyncio.sleep(0.01)

    def _create_display_frame(self, frame: np.ndarray) -> np.ndarray:
        """Create display frame with privacy masking and detection overlay."""
        # Apply privacy blur
        display_frame = self.privacy.process_for_display(frame)

        # Draw detection boxes
        for det in self._last_detections:
            x1, y1, x2, y2 = [int(v) for v in det.bbox]
            color = (0, 255, 0)  # Green

            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)

            # Draw label
            label = f"{det.class_name} ({det.confidence:.2f})"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(
                display_frame,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                color,
                -1,
            )
            cv2.putText(
                display_frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                2,
            )

        return display_frame

    async def _check_delta_push(self) -> None:
        """Check if it's time to push inventory delta."""
        now = time.time()
        if now - self._last_delta_time >= self.settings.batch_timeout:
            delta = self.inventory.get_delta()
            if delta and self.on_delta:
                self.on_delta(delta)
            self._last_delta_time = now

    def get_status(self) -> ServiceStatus:
        """Get current service status."""
        return ServiceStatus(
            status="running" if self._running else "stopped",
            fps=round(self._fps, 1),
            frame_count=self._frame_count,
            last_detection_time=self._last_detection_time,
            motion_active=self.motion.is_active,
            inventory=self.inventory.get_current_inventory(),
        )

    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame."""
        return self._current_frame

    def get_current_detections(self) -> List[TrackedDetection]:
        """Get the most recent detections."""
        return self._last_detections

    def reload_config(self) -> None:
        """Reload configuration from disk."""
        from config import reload_settings

        self.settings = reload_settings()

        # Update ROI
        if self.settings.roi:
            self.privacy.set_roi(self.settings.roi.to_dict())
        else:
            self.privacy.set_roi(None)

        logger.info("Configuration reloaded")
