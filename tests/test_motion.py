"""Tests for motion detection."""

import numpy as np
import pytest

from detection.motion import MotionDetector


class TestMotionDetector:
    """Test motion detector."""

    def test_init(self):
        """Test initialization."""
        detector = MotionDetector(threshold=0.05, blur_size=21)
        assert detector.threshold == 0.05
        assert detector.blur_size == 21
        assert detector.prev_frame is None

    def test_first_frame_returns_true(self):
        """Test that first frame always triggers detection."""
        detector = MotionDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = detector.detect(frame)
        assert result is True

    def test_static_scene_returns_false(self):
        """Test that identical frames return False."""
        detector = MotionDetector(threshold=0.02, cooldown_frames=0)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # First frame
        detector.detect(frame)

        # Same frame again - should return False (no motion)
        result = detector.detect(frame.copy())
        assert result is False

    def test_motion_detected(self):
        """Test that significant motion is detected."""
        detector = MotionDetector(threshold=0.02, cooldown_frames=0)

        # First frame - mostly black
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        detector.detect(frame1)

        # Second frame - add white region (significant change)
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2[100:200, 100:200] = 255  # White rectangle

        result = detector.detect(frame2)
        assert result is True
        assert detector.last_motion_score > 0.02

    def test_cooldown(self):
        """Test cooldown period after motion."""
        detector = MotionDetector(threshold=0.02, cooldown_frames=5)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector.detect(frame)

        # Trigger motion
        motion_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        motion_frame[100:300, 100:300] = 255
        detector.detect(motion_frame)

        # Static frames during cooldown should still return True
        static_frame = frame.copy()
        for i in range(5):
            result = detector.detect(static_frame)
            assert result is True, f"Failed on cooldown frame {i}"

        # After cooldown, should return False
        result = detector.detect(static_frame)
        assert result is False

    def test_reset(self):
        """Test reset clears state."""
        detector = MotionDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector.detect(frame)

        assert detector.prev_frame is not None

        detector.reset()

        assert detector.prev_frame is None
        assert detector.motion_cooldown == 0
        assert detector.last_motion_score == 0.0

    def test_is_active_property(self):
        """Test is_active property."""
        detector = MotionDetector(threshold=0.02, cooldown_frames=3)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector.detect(frame)

        assert detector.is_active is False

        # Trigger motion
        motion_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        motion_frame[:, :] = 255
        detector.detect(motion_frame)

        assert detector.is_active is True
