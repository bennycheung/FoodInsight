"""Tests for inventory state management."""

import pytest
from datetime import datetime

from detection.models import TrackedDetection
from detection.inventory import (
    InventoryStateManager,
    EventType,
)


class TestInventoryStateManager:
    """Test inventory state manager."""

    def test_init(self):
        """Test initialization."""
        manager = InventoryStateManager(machine_id="test-001")
        assert manager.machine_id == "test-001"
        assert manager.debounce_frames == 10
        assert len(manager.current_counts) == 0
        assert len(manager.active_tracks) == 0

    def test_new_item_generates_added_event(self):
        """Test that new items generate SNACK_ADDED events."""
        manager = InventoryStateManager(machine_id="test-001")

        detections = [
            TrackedDetection(
                track_id=1,
                class_id=0,
                class_name="chips",
                confidence=0.9,
                bbox=[100, 100, 200, 200],
            )
        ]

        events = manager.update(detections)

        assert len(events) == 1
        assert events[0].type == EventType.SNACK_ADDED
        assert events[0].item == "chips"
        assert events[0].count_before == 0
        assert events[0].count_after == 1
        assert manager.current_counts["chips"] == 1

    def test_multiple_items(self):
        """Test tracking multiple items."""
        manager = InventoryStateManager(machine_id="test-001")

        detections = [
            TrackedDetection(
                track_id=1,
                class_id=0,
                class_name="chips",
                confidence=0.9,
                bbox=[100, 100, 200, 200],
            ),
            TrackedDetection(
                track_id=2,
                class_id=1,
                class_name="candy",
                confidence=0.85,
                bbox=[300, 100, 400, 200],
            ),
            TrackedDetection(
                track_id=3,
                class_id=0,
                class_name="chips",
                confidence=0.88,
                bbox=[100, 300, 200, 400],
            ),
        ]

        events = manager.update(detections)

        assert len(events) == 3
        assert manager.current_counts["chips"] == 2
        assert manager.current_counts["candy"] == 1

    def test_item_disappearance_debounce(self):
        """Test that items must disappear for debounce frames before TAKEN event."""
        manager = InventoryStateManager(machine_id="test-001", debounce_frames=5)

        # Add item
        detections = [
            TrackedDetection(
                track_id=1,
                class_id=0,
                class_name="chips",
                confidence=0.9,
                bbox=[100, 100, 200, 200],
            )
        ]
        manager.update(detections)
        assert manager.current_counts["chips"] == 1

        # Item disappears but not long enough
        for i in range(4):
            events = manager.update([])
            assert len(events) == 0
            assert manager.current_counts["chips"] == 1

        # Item still gone - should trigger TAKEN
        events = manager.update([])
        assert len(events) == 1
        assert events[0].type == EventType.SNACK_TAKEN
        assert events[0].item == "chips"
        assert manager.current_counts["chips"] == 0

    def test_item_reappears_cancels_disappearance(self):
        """Test that item reappearing resets disappearance counter."""
        manager = InventoryStateManager(machine_id="test-001", debounce_frames=5)

        detection = TrackedDetection(
            track_id=1,
            class_id=0,
            class_name="chips",
            confidence=0.9,
            bbox=[100, 100, 200, 200],
        )

        # Add item
        manager.update([detection])

        # Item disappears for 3 frames
        for _ in range(3):
            manager.update([])

        # Item reappears
        events = manager.update([detection])
        assert len(events) == 0  # No new event

        # Item disappears again - counter should be reset
        for _ in range(4):
            events = manager.update([])
            assert len(events) == 0

        assert manager.current_counts["chips"] == 1

    def test_get_delta(self):
        """Test delta generation."""
        manager = InventoryStateManager(machine_id="test-001")

        detections = [
            TrackedDetection(
                track_id=1,
                class_id=0,
                class_name="chips",
                confidence=0.9,
                bbox=[100, 100, 200, 200],
            )
        ]
        manager.update(detections)

        delta = manager.get_delta()
        assert delta is not None
        assert delta.machine_id == "test-001"
        assert delta.inventory["chips"] == 1
        assert len(delta.events) == 1

        # Second call should return None (events cleared)
        delta2 = manager.get_delta()
        assert delta2 is None

    def test_get_current_inventory(self):
        """Test getting current inventory."""
        manager = InventoryStateManager(machine_id="test-001")

        manager.update([
            TrackedDetection(
                track_id=1,
                class_id=0,
                class_name="chips",
                confidence=0.9,
                bbox=[100, 100, 200, 200],
            ),
            TrackedDetection(
                track_id=2,
                class_id=1,
                class_name="candy",
                confidence=0.85,
                bbox=[300, 100, 400, 200],
            ),
        ])

        inventory = manager.get_current_inventory()
        assert inventory == {"chips": 1, "candy": 1}

    def test_reset(self):
        """Test reset clears all state."""
        manager = InventoryStateManager(machine_id="test-001")

        manager.update([
            TrackedDetection(
                track_id=1,
                class_id=0,
                class_name="chips",
                confidence=0.9,
                bbox=[100, 100, 200, 200],
            )
        ])

        assert len(manager.current_counts) > 0
        assert len(manager.active_tracks) > 0

        manager.reset()

        assert len(manager.current_counts) == 0
        assert len(manager.active_tracks) == 0
        assert len(manager.pending_events) == 0
