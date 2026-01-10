"""Tests for privacy pipeline."""

import numpy as np
import pytest

from privacy.pipeline import PrivacyPipeline


class TestPrivacyPipeline:
    """Test privacy pipeline."""

    def test_init(self):
        """Test initialization."""
        pipeline = PrivacyPipeline(blur_intensity=51)
        assert pipeline.blur_intensity == 51
        assert pipeline.roi is None

    def test_blur_intensity_must_be_odd(self):
        """Test that blur intensity is made odd."""
        pipeline = PrivacyPipeline(blur_intensity=50)
        assert pipeline.blur_intensity == 51

    def test_set_roi(self):
        """Test setting ROI."""
        pipeline = PrivacyPipeline()
        roi = {"x1": 100, "y1": 100, "x2": 400, "y2": 300}
        pipeline.set_roi(roi)

        assert pipeline.roi == roi
        assert pipeline.has_roi is True

    def test_clear_roi(self):
        """Test clearing ROI."""
        pipeline = PrivacyPipeline()
        pipeline.set_roi({"x1": 100, "y1": 100, "x2": 400, "y2": 300})
        pipeline.set_roi(None)

        assert pipeline.roi is None
        assert pipeline.has_roi is False

    def test_crop_for_detection_no_roi(self):
        """Test cropping with no ROI returns full frame."""
        pipeline = PrivacyPipeline()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = pipeline.crop_for_detection(frame)
        assert result.shape == frame.shape

    def test_crop_for_detection_with_roi(self):
        """Test cropping with ROI returns cropped region."""
        pipeline = PrivacyPipeline()
        pipeline.set_roi({"x1": 100, "y1": 50, "x2": 300, "y2": 200})

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = pipeline.crop_for_detection(frame)

        assert result.shape == (150, 200, 3)  # (200-50, 300-100, 3)

    def test_process_for_display_no_roi(self):
        """Test display processing with no ROI returns original."""
        pipeline = PrivacyPipeline()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:200] = 128

        result = pipeline.process_for_display(frame)
        assert np.array_equal(result, frame)

    def test_process_for_display_with_roi_preserves_region(self):
        """Test that ROI region is preserved in display output."""
        pipeline = PrivacyPipeline(blur_intensity=51)
        pipeline.set_roi({"x1": 100, "y1": 100, "x2": 200, "y2": 200})

        # Create frame with distinct region
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:200] = 255  # White in ROI

        result = pipeline.process_for_display(frame)

        # ROI region should be preserved (white)
        roi_region = result[100:200, 100:200]
        assert np.all(roi_region == 255)

    def test_adjust_detections(self):
        """Test coordinate adjustment for detections."""
        pipeline = PrivacyPipeline()
        pipeline.set_roi({"x1": 100, "y1": 50, "x2": 400, "y2": 300})

        # Mock detection with bbox
        class MockDetection:
            def __init__(self):
                self.bbox = [10, 20, 50, 60]  # Relative to ROI

        detections = [MockDetection()]
        frame_shape = (480, 640, 3)

        result = pipeline.adjust_detections(detections, frame_shape)

        # Coordinates should be adjusted by ROI offset
        assert result[0].bbox == [110, 70, 150, 110]  # +100, +50

    def test_roi_offset_property(self):
        """Test roi_offset property."""
        pipeline = PrivacyPipeline()

        assert pipeline.roi_offset == (0, 0)

        pipeline.set_roi({"x1": 100, "y1": 50, "x2": 400, "y2": 300})
        assert pipeline.roi_offset == (100, 50)

    def test_roi_clamped_to_frame_bounds(self):
        """Test that ROI coordinates are clamped to frame bounds."""
        pipeline = PrivacyPipeline()
        pipeline.set_roi({"x1": -50, "y1": -50, "x2": 800, "y2": 600})

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = pipeline.crop_for_detection(frame)

        # Should be clamped to frame size
        assert result.shape[0] <= 480
        assert result.shape[1] <= 640
