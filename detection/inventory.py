"""Inventory state management and delta generation."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

from .models import TrackedDetection

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Inventory event types."""

    SNACK_TAKEN = "SNACK_TAKEN"
    SNACK_ADDED = "SNACK_ADDED"


@dataclass
class InventoryEvent:
    """Single inventory change event."""

    type: EventType
    item: str
    timestamp: datetime
    track_id: int
    count_before: int
    count_after: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "item": self.item,
            "timestamp": self.timestamp.isoformat(),
            "track_id": self.track_id,
            "count_before": self.count_before,
            "count_after": self.count_after,
        }


@dataclass
class InventoryDelta:
    """Batched inventory update for API push."""

    machine_id: str
    timestamp: datetime
    inventory: Dict[str, int]
    events: List[InventoryEvent] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Converts inventory format to match backend InventoryUpdate model:
        - 'inventory' (dict[str, int]) -> 'items' (dict[str, {count, confidence}])
        """
        return {
            "machine_id": self.machine_id,
            "timestamp": self.timestamp.isoformat(),
            "items": {
                item: {"count": count, "confidence": 1.0}
                for item, count in self.inventory.items()
            },
            "events": [e.to_dict() for e in self.events],
        }


class InventoryStateManager:
    """Manage inventory state and detect changes.

    Tracks individual items via their track IDs and generates
    SNACK_TAKEN/SNACK_ADDED events when items appear or disappear.
    """

    def __init__(
        self,
        machine_id: str,
        debounce_frames: int = 10,
    ):
        """Initialize inventory state manager.

        Args:
            machine_id: Unique identifier for this machine
            debounce_frames: Frames before confirming item disappearance
        """
        self.machine_id = machine_id
        self.debounce_frames = debounce_frames

        # Current state
        self.current_counts: Dict[str, int] = defaultdict(int)
        self.active_tracks: Dict[int, str] = {}  # track_id -> class_name
        self.pending_events: List[InventoryEvent] = []

        # Disappearance tracking for debouncing
        self.disappeared_tracks: Dict[int, int] = {}  # track_id -> frames_missing

    def update(self, detections: List[TrackedDetection]) -> List[InventoryEvent]:
        """Update inventory state with new detections.

        Args:
            detections: List of tracked detections from current frame

        Returns:
            List of new inventory events generated
        """
        events: List[InventoryEvent] = []
        current_track_ids: Set[int] = set()

        # Process current detections
        for det in detections:
            current_track_ids.add(det.track_id)

            # Check for new tracks (item added)
            if det.track_id not in self.active_tracks:
                self.active_tracks[det.track_id] = det.class_name
                count_before = self.current_counts[det.class_name]
                self.current_counts[det.class_name] += 1

                event = InventoryEvent(
                    type=EventType.SNACK_ADDED,
                    item=det.class_name,
                    timestamp=datetime.utcnow(),
                    track_id=det.track_id,
                    count_before=count_before,
                    count_after=self.current_counts[det.class_name],
                )
                events.append(event)
                logger.info(
                    f"SNACK_ADDED: {det.class_name} (track_id={det.track_id}, "
                    f"count: {count_before} -> {self.current_counts[det.class_name]})"
                )

            # Track reappeared - reset disappearance counter
            if det.track_id in self.disappeared_tracks:
                del self.disappeared_tracks[det.track_id]

        # Check for disappeared tracks (item taken)
        for track_id, class_name in list(self.active_tracks.items()):
            if track_id not in current_track_ids:
                # Increment disappearance counter
                self.disappeared_tracks[track_id] = (
                    self.disappeared_tracks.get(track_id, 0) + 1
                )

                # Check if debounce threshold reached
                if self.disappeared_tracks[track_id] >= self.debounce_frames:
                    count_before = self.current_counts[class_name]
                    self.current_counts[class_name] = max(0, count_before - 1)

                    event = InventoryEvent(
                        type=EventType.SNACK_TAKEN,
                        item=class_name,
                        timestamp=datetime.utcnow(),
                        track_id=track_id,
                        count_before=count_before,
                        count_after=self.current_counts[class_name],
                    )
                    events.append(event)
                    logger.info(
                        f"SNACK_TAKEN: {class_name} (track_id={track_id}, "
                        f"count: {count_before} -> {self.current_counts[class_name]})"
                    )

                    # Clean up
                    del self.active_tracks[track_id]
                    del self.disappeared_tracks[track_id]

        # Accumulate events for batching
        self.pending_events.extend(events)
        return events

    def get_delta(self) -> Optional[InventoryDelta]:
        """Get pending inventory delta for API push.

        Returns:
            InventoryDelta if there are pending events, None otherwise
        """
        if not self.pending_events:
            return None

        delta = InventoryDelta(
            machine_id=self.machine_id,
            timestamp=datetime.utcnow(),
            inventory=dict(self.current_counts),
            events=self.pending_events.copy(),
        )

        self.pending_events.clear()
        return delta

    def get_current_inventory(self) -> Dict[str, int]:
        """Get current inventory counts."""
        return dict(self.current_counts)

    def reset(self) -> None:
        """Reset all inventory state."""
        self.current_counts.clear()
        self.active_tracks.clear()
        self.pending_events.clear()
        self.disappeared_tracks.clear()
