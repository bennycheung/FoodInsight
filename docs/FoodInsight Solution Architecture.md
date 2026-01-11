# FoodInsight Solution Architecture

**Author:** Winston (Architect) via BMAD
**Date:** 2026-01-11
**Version:** 2.0
**Status:** IMPLEMENTED (Local-First)
**PRD Reference:** [[FoodInsight PRD]]
**Implementation:** `/Users/bcheung/dev/FoodInsight/`

---

## Executive Summary

FoodInsight is a smart snack inventory monitoring system using edge AI and local backend. This solution architecture defines the technical implementation for a Level 2 Internal Tool Prototype targeting office break room deployment.

**Architecture Pattern:** Local-First (Embedded + Local Backend + PWA)

**Key Design Decisions:**
- **Local-first processing** - All detection and storage runs locally on device (no cloud required)
- **Multi-platform support** - RPi 4 ($55) for budget, RPi 5 ($80) for performance, macOS for development
- **CPU-only prototype** - No Hailo accelerator for MVP (RPi 5 can upgrade later)
- **Privacy-by-design** - ROI masking, no images transmitted, all data stays local
- **SQLite database** - Simple, reliable, zero-config local storage
- **Real-time consumer view** - PWA with polling (WebSocket deferred to Phase 2)

---

## Technology Stack

### Edge Device (Raspberry Pi 4 / 5)

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **OS** | Raspberry Pi OS | 64-bit Bookworm | Official, well-supported |
| **Runtime** | Python | 3.11+ | Ultralytics compatibility |
| **Detection** | YOLO11n | Latest | Smallest model, CPU-optimized |
| **Model Format** | NCNN | - | ARM CPU optimization |
| **Tracking** | ByteTrack | Built-in | Ultralytics integration |
| **Web Framework** | Flask + HTMX | 3.x + 2.x | Lightweight admin portal |
| **HTTP Client** | httpx | 0.27+ | Async API calls |
| **Camera** | picamera2 | Latest | RPi Camera Module 3 |
| **Process Manager** | systemd | - | Service management |

### Supported Hardware Platforms

| Platform | CPU | RAM | Expected FPS | Cost | Hailo Upgrade |
|----------|-----|-----|--------------|------|---------------|
| **Raspberry Pi 4** | Cortex-A72 4x 1.8GHz | 4-8GB | 1-3 FPS | $55 | No (no PCIe) |
| **Raspberry Pi 5** | Cortex-A76 4x 2.4GHz | 4-8GB | 4-6 FPS | $80 | Yes (PCIe 2.0) |

**Platform Selection Guide:**
- **Choose RPi 4** if: Budget constrained, already own one, low-traffic location
- **Choose RPi 5** if: Buying new, want Hailo upgrade path, higher traffic location

### Platform-Specific Configuration

The edge detection service auto-detects the platform and applies optimized settings:

```python
# config/platform.py
import subprocess
from dataclasses import dataclass

@dataclass
class PlatformConfig:
    """Platform-specific detection parameters."""
    input_size: int           # YOLO input resolution
    process_every_n_frames: int  # Frame skipping
    motion_threshold: float   # Motion sensitivity
    batch_timeout: float      # API batch interval

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

PLATFORM_CONFIGS = {
    "rpi5": PlatformConfig(
        input_size=640,           # Full resolution
        process_every_n_frames=1, # Every frame
        motion_threshold=0.008,   # High sensitivity for item detection
        batch_timeout=1.0         # 1 second batching
    ),
    "rpi4": PlatformConfig(
        input_size=320,           # Reduced for performance
        process_every_n_frames=3, # Every 3rd frame
        motion_threshold=0.006,   # Higher sensitivity (compensate for skipping)
        batch_timeout=2.0         # Longer batch window
    ),
    "desktop": PlatformConfig(
        input_size=640,           # Full resolution
        process_every_n_frames=1, # Every frame
        motion_threshold=0.008,   # High sensitivity for item detection
        batch_timeout=1.0         # 1 second batching
    ),
    "unknown": PlatformConfig(
        input_size=320,           # Conservative default
        process_every_n_frames=2,
        motion_threshold=0.008,   # High sensitivity for item detection
        batch_timeout=1.5
    )
}

def get_config() -> PlatformConfig:
    """Get configuration for detected platform."""
    platform = detect_platform()
    return PLATFORM_CONFIGS[platform]
```

**Performance Impact by Platform:**

| Setting | RPi 5 Value | RPi 4 Value | Desktop Value | Impact |
|---------|-------------|-------------|---------------|--------|
| Input size | 640×640 | 320×320 | 640×640 | 4× fewer pixels on RPi 4, ~2× faster inference |
| Frame skip | 1 (none) | 3 | 1 (none) | 3× less CPU load on RPi 4, 3× latency |
| Motion threshold | 0.008 | 0.006 | 0.008 | High sensitivity for item detection |
| Expected FPS | 4-6 | 1-3 | 10+ | Sufficient for break room traffic |

### Local Backend

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Framework** | FastAPI | 0.115+ | Async, auto-docs, Pydantic |
| **Runtime** | Python | 3.11+ | Performance, typing |
| **Database** | SQLite + SQLAlchemy | 2.0+ | Local-first, zero-config, reliable |
| **Auth** | Basic Auth | - | Admin API protection |
| **Hosting** | Local (same device) | - | No cloud dependency |
| **Package Manager** | uv | Latest | Fast Python dependency management |

### Client App (PWA)

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Framework** | Vue 3 | 3.5+ | Composition API, lightweight |
| **Build Tool** | Vite | 6.x | Fast builds, native ESM |
| **State** | Pinia | 2.x | Vue-native state management |
| **PWA** | vite-plugin-pwa | Latest | Service worker generation |
| **Styling** | Tailwind CSS | 3.x | Utility-first, responsive |
| **Hosting** | Cloudflare Pages | - | Free tier, global CDN |
| **Package Manager** | bun | Latest | Fast JS runtime |

---

## Architecture Overview

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FoodInsight Device (Local-First)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      EDGE DEVICE LAYER                       │    │
│  │                                                              │    │
│  │  ┌───────────┐    ┌───────────┐    ┌───────────────────┐   │    │
│  │  │ Camera    │───►│ Detection │───►│ Inventory Tracker │   │    │
│  │  │ Input     │    │ Pipeline  │    │                   │   │    │
│  │  └───────────┘    │ YOLO11n   │    └─────────┬─────────┘   │    │
│  │                   │ ByteTrack │              │              │    │
│  │                   └───────────┘              │              │    │
│  │                                              ▼              │    │
│  │  ┌───────────┐    ┌───────────┐    ┌───────────────────┐   │    │
│  │  │ Admin     │◄──►│ FastAPI   │◄──►│ SQLite Database   │   │    │
│  │  │ Portal    │    │ Backend   │    │ (foodinsight.db)  │   │    │
│  │  │ (Flask)   │    │ Port 8000 │    └───────────────────┘   │    │
│  │  │ Port 8080 │    └─────┬─────┘                             │    │
│  │  └───────────┘          │                                   │    │
│  │   LAN Only              │                                   │    │
│  └─────────────────────────┼───────────────────────────────────┘    │
│                            │                                         │
│                            │ REST API                                │
│                            ▼                                         │
│                   ┌─────────────────┐                                │
│                   │   Consumer PWA  │                                │
│                   │   (Vue 3)       │                                │
│                   │   Phone/Browser │                                │
│                   └─────────────────┘                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Camera (30 FPS) ──► Motion Check ──► YOLO11n (4-6 FPS) ──► ByteTrack
                         │                                      │
                         │ No motion                            │
                         ▼                                      ▼
                    Skip frame                          Inventory State
                                                              │
                                                              │ Delta detected
                                                              ▼
                                                   ┌──────────────────┐
                                                   │ REST API Push    │
                                                   │ (max 1/second)   │
                                                   └────────┬─────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │ SQLite Database  │
                                                   │ (local storage)  │
                                                   └────────┬─────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │ PWA Polls        │
                                                   │ (every 30s)      │
                                                   └──────────────────┘
```

---

## Component Design

### Component 1: Edge Detection Service

**Epic Mapping:** Epic 1 (E1-S1 through E1-S8)

**Responsibilities:**
- Camera frame capture and preprocessing
- YOLO11n inference (NCNN format for CPU)
- ByteTrack object tracking
- **Class filtering** - Only detect and report configured allowed classes
- Inventory state management
- Delta update generation
- Cloud API synchronization

**Key Classes:**

```python
# detection/service.py
class DetectionService:
    """Main detection orchestrator."""

    def __init__(self, config: DetectionConfig):
        self.model = YOLO("yolo11n.ncnn")
        self.tracker = ByteTrack()
        self.inventory = InventoryStateManager()
        self.motion_detector = MotionDetector(threshold=0.02)
        self.api_client = CloudAPIClient(config.server_url, config.api_key)
        self.allowed_classes = config.allowed_classes  # Class filter

    async def process_frame(self, frame: np.ndarray) -> None:
        """Process single frame through detection pipeline."""
        # After detection, filter to allowed classes only
        detections = self.tracker.detect_and_track(frame)
        if self.allowed_classes:
            detections = [d for d in detections if d.class_name in self.allowed_classes]
        # ... continue processing

    async def run(self) -> None:
        """Main detection loop."""
        pass
```

```python
# detection/inventory.py
class InventoryStateManager:
    """Track inventory changes and generate deltas."""

    def __init__(self, debounce_frames: int = 10):
        self.current_state: dict[str, int] = {}
        self.pending_changes: list[InventoryEvent] = []

    def update(self, detections: list[Detection]) -> list[InventoryEvent]:
        """Update state and return change events."""
        pass

    def get_delta(self) -> InventoryDelta | None:
        """Get pending changes for API push."""
        pass
```

**NFR Compliance:**
- NFR1 (Detection latency <500ms): NCNN + motion-trigger = 170-250ms
- NFR5 (Power <15W): RPi 5 idle ~3W, detection ~8W

### Component 2: Edge Admin Portal

**Epic Mapping:** Epic 1 (E1-S6, E1-S7)

**Responsibilities:**
- Camera preview stream (MJPEG)
- ROI configuration UI
- Detection status display
- Local-only access (LAN)

**Routes:**

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Dashboard with status |
| `/preview` | GET | MJPEG camera stream |
| `/roi` | GET/POST | ROI configuration |
| `/status` | GET | JSON status endpoint |

**Key Implementation:**

```python
# admin/app.py
from flask import Flask, Response, render_template
import cv2

app = Flask(__name__)

@app.route("/preview")
def video_feed():
    """MJPEG stream for camera preview."""
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/roi", methods=["POST"])
def set_roi():
    """Update ROI from UI drag selection."""
    data = request.json
    config.update_roi(data["x1"], data["y1"], data["x2"], data["y2"])
    return {"status": "ok"}
```

### Component 3: Local Backend (FastAPI + SQLite)

**Epic Mapping:** Epic 2 (E2-S1 through E2-S4)

**Responsibilities:**
- Receive inventory updates from edge detection service
- Store data in SQLite (local database)
- Serve inventory API for PWA
- Admin API with Basic authentication

**API Endpoints:**

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `POST /inventory/update` | POST | None | Edge device pushes delta |
| `POST /inventory/event` | POST | None | Log detection event |
| `GET /inventory` | GET | None | Get current inventory |
| `GET /inventory/events` | GET | None | Get recent events |
| `GET /health` | GET | None | Health check |
| `GET /ready` | GET | None | Readiness check (DB status) |
| `GET /admin/status` | GET | Basic | Device status |
| `GET /admin/config` | GET/PUT | Basic | Configuration |
| `GET /admin/users` | GET/POST/DELETE | Basic | User management |

**Data Models:**

```python
# models/inventory.py
from pydantic import BaseModel, Field
from datetime import datetime

class InventoryItem(BaseModel):
    item_name: str
    display_name: str | None = None
    count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    last_updated: datetime | None = None

class InventoryUpdate(BaseModel):
    items: dict[str, int]  # item_name -> count
    confidences: dict[str, float] | None = None

class InventoryResponse(BaseModel):
    device_id: str
    location: str
    items: list[InventoryItem]
    last_updated: datetime | None
```

**NFR Compliance:**
- NFR2 (API response <200ms): FastAPI async + SQLite
- NFR6 (Cloud cost $0/mo): Local SQLite, no cloud dependency

### Component 4: Consumer PWA

**Epic Mapping:** Epic 2 (E2-S5 through E2-S8)

**Responsibilities:**
- Display current inventory
- Show stock status (available/out of stock)
- Auto-refresh via polling
- Installable PWA

**View Structure:**

```
src/
├── App.vue                 # Root component
├── views/
│   └── InventoryView.vue   # Main consumer view
├── components/
│   ├── SnackGrid.vue       # Grid of snack cards
│   ├── SnackCard.vue       # Individual item display
│   └── LastUpdated.vue     # Timestamp display
├── stores/
│   └── inventory.ts        # Pinia store
├── composables/
│   └── useInventory.ts     # API fetching logic
└── main.ts
```

**Key Implementation:**

```typescript
// stores/inventory.ts
import { defineStore } from 'pinia'

interface SnackItem {
  name: string
  count: number
  inStock: boolean
}

export const useInventoryStore = defineStore('inventory', {
  state: () => ({
    items: [] as SnackItem[],
    lastUpdated: null as Date | null,
    loading: false,
    error: null as string | null
  }),

  actions: {
    async fetchInventory() {
      this.loading = true
      try {
        const response = await fetch('/api/inventory/breakroom-1')
        const data = await response.json()
        this.items = data.items.map(item => ({
          ...item,
          inStock: item.count > 0
        }))
        this.lastUpdated = new Date(data.last_updated)
      } catch (e) {
        this.error = 'Failed to load inventory'
      } finally {
        this.loading = false
      }
    }
  }
})
```

**NFR Compliance:**
- NFR3 (PWA load <2s): Vite + Cloudflare CDN
- FR4.7 (Auto-refresh): 30-second polling interval

---

## Data Architecture

### SQLite Schema

The local SQLite database (`data/foodinsight.db`) uses the following schema:

```sql
-- Device configuration and status
CREATE TABLE config (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Singleton row
    device_id TEXT NOT NULL DEFAULT 'breakroom-001',
    location TEXT NOT NULL DEFAULT 'Break Room',
    status TEXT NOT NULL DEFAULT 'online',
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    roi_x1 REAL, roi_y1 REAL, roi_x2 REAL, roi_y2 REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Current inventory state
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL UNIQUE,
    display_name TEXT,
    count INTEGER NOT NULL DEFAULT 0,
    confidence REAL DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Detection events log
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,  -- 'SNACK_TAKEN' | 'SNACK_ADDED'
    item_name TEXT NOT NULL,
    count_before INTEGER NOT NULL,
    count_after INTEGER NOT NULL,
    confidence REAL DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_name) REFERENCES inventory(item_name)
);

-- Admin users for Basic auth
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alert rules (Phase 2)
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT,  -- NULL for all items
    threshold INTEGER NOT NULL,
    alert_type TEXT NOT NULL,  -- 'low_stock' | 'out_of_stock'
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log for admin actions
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_item ON events(item_name);
CREATE INDEX idx_inventory_item ON inventory(item_name);
```

### Data Retention

- **Inventory**: Current state only, updated in place
- **Events**: 30-day retention (cleanup job in Phase 2)
- **Audit Log**: 90-day retention

---

## Architecture Decision Records (ADRs)

### ADR-001: CPU-Only Detection for Prototype

**Status:** Accepted

**Context:** The PRD specifies $80 hardware budget (Basic tier). Hailo-8L adds $70.

**Decision:** Use YOLO11n with NCNN format for CPU-only inference on RPi 5.

**Consequences:**
- (+) Meets budget constraint ($80 vs $150)
- (+) Simpler deployment, no accelerator drivers
- (-) Lower frame rate (4-6 FPS vs 15-25 FPS)
- (-) Requires motion-triggered detection

**Mitigation:** Motion detection reduces CPU load; 4-6 FPS sufficient for low-traffic break room.

### ADR-002: Polling vs WebSocket for PWA

**Status:** Accepted

**Context:** FR4.4 requires auto-refresh. WebSocket provides instant updates but adds complexity.

**Decision:** Use 30-second polling for MVP. Defer WebSocket to Phase 2.

**Consequences:**
- (+) Simpler implementation, no WebSocket infrastructure
- (+) Works well with CDN caching
- (-) Up to 30-second delay for inventory updates

**Mitigation:** 30-second delay acceptable for checking snack availability.

### ADR-003: Flask for Edge Admin vs FastAPI

**Status:** Accepted

**Context:** FastAPI is the cloud backend choice. Should edge admin also use FastAPI?

**Decision:** Use Flask + HTMX for edge admin portal.

**Consequences:**
- (+) Lighter footprint on resource-constrained edge device
- (+) HTMX provides dynamic UI without heavy JS
- (+) Simpler MJPEG streaming with Flask
- (-) Different framework from cloud backend

**Mitigation:** Edge admin is isolated component; framework difference acceptable.

### ADR-004: SQLite for Local-First Architecture

**Status:** Accepted (Revised)

**Context:** Prototype originally considered cloud Firestore, but local-first design provides better reliability and zero cloud cost.

**Decision:** Use SQLite for all data storage.

**Consequences:**
- (+) Zero cloud dependency - works completely offline
- (+) Zero infrastructure cost ($0/month)
- (+) Simple deployment - single file database
- (+) Full data ownership - no third-party data storage
- (+) Faster development - no cloud configuration needed
- (-) Multi-device sync requires additional work (Phase 2+)
- (-) No built-in real-time capabilities

**Mitigation:** Single-device prototype doesn't need multi-device sync; PWA polling provides adequate refresh rate for break room use case.

### ADR-005: Raspberry Pi 4 Support

**Status:** Accepted

**Context:** The original architecture specified RPi 5 only ($80). Users may have existing RPi 4 hardware or prefer the lower cost ($55).

**Decision:** Support both Raspberry Pi 4 and Raspberry Pi 5 with platform-specific configurations.

**Technical Approach:**
- Auto-detect platform at runtime via `/proc/device-tree/model`
- Apply optimized settings per platform (input size, frame skipping, thresholds)
- RPi 4: 320×320 input, process every 3rd frame, 1-3 FPS expected
- RPi 5: 640×640 input, process every frame, 4-6 FPS expected

**Consequences:**
- (+) Reuses existing RPi 4 hardware, reduces barrier to entry
- (+) Budget tier reduces cost from $139 to $110
- (+) Same codebase, no platform-specific branches
- (-) Lower detection frequency on RPi 4 (1-3 FPS vs 4-6 FPS)
- (-) RPi 4 cannot upgrade to Hailo-8L (no PCIe)
- (-) May require INT8 quantization for acceptable RPi 4 performance

**Mitigation:**
- Motion-triggered detection reduces need for continuous high FPS
- Low-traffic break rooms don't require real-time detection
- Document performance expectations clearly in deployment guide

---

## Security Considerations

### Authentication Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ Admin User  │         │  FastAPI    │         │   SQLite    │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │  GET /admin/status    │                       │
       │  Auth: Basic base64   │                       │
       │──────────────────────►│                       │
       │                       │                       │
       │                       │  Verify credentials   │
       │                       │──────────────────────►│
       │                       │                       │
       │                       │◄──────────────────────│
       │                       │  User record          │
       │                       │                       │
       │  200 OK / 401 Unauth  │                       │
       │◄──────────────────────│                       │
       │                       │                       │

Public endpoints (no auth):
- GET /inventory - Consumer PWA reads inventory
- POST /inventory/update - Edge detection pushes updates
- GET /health, /ready, /info - Health checks
```

### Security Checklist

| Concern | Mitigation |
|---------|------------|
| **Admin API auth** | HTTP Basic auth with bcrypt-hashed passwords in SQLite |
| **Admin portal access** | Local network only (not exposed to internet) |
| **Public API** | Read-only inventory intentional (no auth for consumers) |
| **Data privacy** | Only counts stored, never images |
| **ROI config** | Stored locally in config table |
| **Default credentials** | `admin`/`admin` - change after first login |
| **Audit trail** | Admin actions logged to audit_log table |

---

## Implementation Guidance

### Epic 1: Edge Detection System

**Story Sequence:**

1. **E1-S1: RPi 5 Setup** - Base OS, Python 3.11, camera test
2. **E1-S2: YOLO11n Inference** - Load model, run detection, output bboxes
3. **E1-S3: Motion Detection** - Frame differencing, trigger logic
4. **E1-S4: ByteTrack Integration** - Persistent object IDs
5. **E1-S5: Inventory State Manager** - Track counts, generate deltas
6. **E1-S6: Admin Portal** - Flask app, status page
7. **E1-S7: ROI Configuration** - HTMX drag UI, config persistence
8. **E1-S8: Privacy Masking** - Blur outside ROI

**Dependencies:**
```
E1-S1 ──► E1-S2 ──► E1-S4 ──► E1-S5
              │
              └──► E1-S3

E1-S6 ──► E1-S7 ──► E1-S8
```

### Epic 2: Local Backend + Consumer App

**Story Sequence:**

1. **E2-S1: FastAPI Scaffold** - Project setup, health endpoint
2. **E2-S2: SQLite Integration** - SQLAlchemy models, CRUD operations
3. **E2-S3: Basic Auth** - Admin API authentication middleware
4. **E2-S4: Edge API Integration** - Update endpoint, delta processing
5. **E2-S5: Vue PWA Scaffold** - Vite, Vue 3, Pinia, PWA config
6. **E2-S6: Inventory Display** - Grid component, stock indicators
7. **E2-S7: Auto-refresh** - Polling logic, loading states
8. **E2-S8: PWA Features** - Manifest, service worker, icons

**Dependencies:**
```
E2-S1 ──► E2-S2 ──► E2-S3 ──► E2-S4

E2-S5 ──► E2-S6 ──► E2-S7 ──► E2-S8
```

---

## Source Tree

### Edge Device

```
foodinsight-edge/
├── detection/
│   ├── __init__.py
│   ├── service.py          # Main detection loop
│   ├── model.py            # YOLO11n wrapper
│   ├── tracker.py          # ByteTrack integration
│   ├── motion.py           # Motion detection
│   └── inventory.py        # State management
├── admin/
│   ├── __init__.py
│   ├── app.py              # Flask application
│   ├── templates/
│   │   ├── index.html      # Dashboard
│   │   └── roi.html        # ROI config
│   └── static/
│       └── htmx.min.js
├── privacy/
│   ├── __init__.py
│   └── pipeline.py         # ROI masking
├── api/
│   ├── __init__.py
│   └── client.py           # Cloud API client
├── config.py               # Configuration
├── main.py                 # Entry point
├── requirements.txt
└── systemd/
    └── foodinsight.service
```

### Local Backend

```
server/
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI entry
│   ├── config.py           # Pydantic settings
│   ├── database.py         # SQLAlchemy engine
│   ├── routers/
│   │   ├── health.py       # /health, /ready, /info
│   │   ├── inventory.py    # /inventory/*
│   │   └── admin.py        # /admin/* (Basic auth)
│   ├── db/
│   │   └── models.py       # SQLAlchemy ORM models
│   └── services/
│       └── sqlite.py       # SQLite service layer
├── tests/
│   └── test_inventory.py
├── pyproject.toml
└── README.md
```

### Consumer PWA

```
foodinsight-app/
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── views/
│   │   └── InventoryView.vue
│   ├── components/
│   │   ├── SnackGrid.vue
│   │   ├── SnackCard.vue
│   │   └── LastUpdated.vue
│   ├── stores/
│   │   └── inventory.ts
│   ├── composables/
│   │   └── useInventory.ts
│   └── assets/
│       └── styles.css
├── public/
│   ├── manifest.json
│   └── icons/
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

---

## Testing Strategy

### Unit Testing

| Component | Framework | Coverage Target |
|-----------|-----------|-----------------|
| Edge Detection | pytest | 70% |
| Cloud Backend | pytest | 80% |
| PWA | Vitest | 70% |

### Integration Testing

| Test | Description |
|------|-------------|
| Edge → Backend | Verify delta updates reach SQLite |
| Backend → PWA | Verify inventory API returns correct data |
| End-to-End | Simulated item removal updates PWA |

### Manual Testing

| Scenario | Steps |
|----------|-------|
| Detection accuracy | Place known items, verify counts |
| ROI configuration | Configure via admin, verify masking |
| PWA installation | Add to home screen on iOS/Android |

---

## Hardware Bill of Materials

### Deployment Tiers

| Tier | Description | Use Case |
|------|-------------|----------|
| **Development** | Mac/Linux desktop | Local testing before deployment |
| **Budget** | RPi 4-based, CPU-only | Existing hardware, low traffic |
| **Standard** | RPi 5-based, CPU-only | New deployment, moderate traffic |
| **Performance** | RPi 5 + Hailo-8L | High traffic, future expansion |

### Development Tier (Mac/Linux Desktop)

For testing before Raspberry Pi deployment:

```bash
python run_dev.py  # Runs on port 8080, uses built-in webcam (index 1)

# To use iPhone via Continuity Camera instead:
CAMERA_INDEX=0 python run_dev.py
```

| Component | Development Mode |
|-----------|------------------|
| Camera | OpenCV VideoCapture (configurable index) |
| Camera Index | `CAMERA_INDEX` env var (0=iPhone, 1=built-in webcam) |
| Admin Port | 8080 (no sudo) |
| Config Path | `./dev_config.json` |
| Log Path | `./logs/` |
| Model | Optional (mock mode if absent) |

### Budget Tier (Raspberry Pi 4)

| Component | Model | Est. Cost | Notes |
|-----------|-------|-----------|-------|
| Single-board computer | Raspberry Pi 4 8GB | $55 | 4GB acceptable for tight budget |
| Camera | Camera Module 3 | $25 | Wide variant optional |
| Storage | 64GB microSD (A2) | $12 | A2 rating for performance |
| Power supply | USB-C 5V/3A | $10 | Official PSU recommended |
| Case | Passive cooling case | $8 | Heatsink case preferred |
| **Total** | | **~$110** | |

### Standard Tier (Raspberry Pi 5)

| Component | Model | Est. Cost | Notes |
|-----------|-------|-----------|-------|
| Single-board computer | Raspberry Pi 5 8GB | $80 | 4GB works but 8GB preferred |
| Camera | Camera Module 3 | $25 | Wide variant optional |
| Storage | 64GB microSD (A2) | $12 | A2 rating for performance |
| Power supply | USB-C 5V/5A | $12 | Higher amperage for RPi 5 |
| Case | Active cooling case | $10 | Fan case for sustained load |
| **Total** | | **~$139** | |

### Performance Tier (RPi 5 + Hailo)

| Component | Model | Est. Cost | Notes |
|-----------|-------|-----------|-------|
| Single-board computer | Raspberry Pi 5 8GB | $80 | 8GB required for Hailo |
| Camera | Camera Module 3 | $25 | Wide variant optional |
| AI Accelerator | Hailo-8L M.2 | $70 | 13 TOPS, PCIe 2.0 |
| HAT | Raspberry Pi AI HAT | $25 | M.2 to PCIe adapter |
| Storage | 64GB microSD (A2) | $12 | A2 rating for performance |
| Power supply | USB-C 5V/5A | $12 | Higher amperage required |
| Case | Custom/3D printed | $15 | Must accommodate HAT |
| **Total** | | **~$239** | |

---

## Deployment

### Edge Device

```bash
# On Raspberry Pi 5
git clone https://github.com/your-org/foodinsight-edge
cd foodinsight-edge

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with API key, server URL

# Install service
sudo cp systemd/foodinsight.service /etc/systemd/system/
sudo systemctl enable foodinsight
sudo systemctl start foodinsight
```

### Local Backend

```bash
# On the device (same as edge device or separate)
cd server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Initialize database (auto-creates on first run)
# Default credentials: admin/admin

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Consumer PWA

```bash
# Build for production
cd app
bun run build

# Option 1: Serve from local device (simple)
python -m http.server 3000 -d dist

# Option 2: Deploy to Cloudflare Pages (for remote access)
wrangler pages deploy dist --project-name=foodinsight
```

---

## Monitoring & Operations

### Health Checks

| Component | Endpoint | Interval |
|-----------|----------|----------|
| Cloud API | `GET /health` | 1 minute |
| Edge Device | `GET /status` (local) | On-demand |

### Key Metrics (Phase 2)

- Detection FPS
- API response latency
- Inventory update frequency
- PWA load time

---

## Appendix: Version Matrix

| Dependency | Version | Lock Reason |
|------------|---------|-------------|
| Python | 3.11+ | Ultralytics requirement |
| YOLO11 | Latest | Active development |
| FastAPI | 0.115+ | Stable, Pydantic v2 |
| Vue | 3.5+ | Composition API |
| Vite | 6.x | Latest stable |
| Node.js | 20+ | LTS |
| bun | 1.x | Latest |

---

## Requirements Traceability Matrix

### Functional Requirements Coverage

| Requirement | Description | Component | Status |
|-------------|-------------|-----------|--------|
| **FR1.1** | Detect and classify snack items | Edge Detection Service | ✅ Covered |
| **FR1.2** | YOLO11n model (NCNN format) | Edge Detection Service | ✅ Covered |
| **FR1.3** | Motion-triggered detection | Edge Detection Service | ✅ Covered |
| **FR1.4** | ByteTrack object tracking | Edge Detection Service | ✅ Covered |
| **FR1.5** | Detect items taken/added | Edge Detection Service | ✅ Covered |
| **FR1.6** | Filter detections to allowed classes only | Edge Detection Service | ✅ Covered |
| **FR2.1** | Maintain inventory count per class | Edge Detection Service | ✅ Covered |
| **FR2.2** | Push delta updates to cloud | Edge Detection Service | ✅ Covered |
| **FR2.3** | Include timestamp + confidence | Data Models | ✅ Covered |
| **FR2.4** | Batch updates (max 1/second) | Edge Detection Service | ✅ Covered |
| **FR3.1** | Receive/store inventory updates | Local Backend | ✅ Covered |
| **FR3.2** | REST API for inventory retrieval | Local Backend | ✅ Covered |
| **FR3.3** | SQLite for local-first operation | Data Architecture | ✅ Covered |
| **FR3.4** | Basic authentication for admin | Local Backend | ✅ Covered |
| **FR4.1** | Display current snack inventory | Consumer PWA | ✅ Covered |
| **FR4.2** | Show item name and count | Consumer PWA | ✅ Covered |
| **FR4.3** | Indicate out of stock items | Consumer PWA | ✅ Covered |
| **FR4.4** | Auto-refresh (30 seconds) | Consumer PWA | ✅ Covered |
| **FR4.5** | Mobile and desktop browsers | Consumer PWA | ✅ Covered |
| **FR4.6** | Installable as PWA | Consumer PWA | ✅ Covered |
| **FR5.1** | Process snack shelf ROI only | Edge Detection Service | ✅ Covered |
| **FR5.2** | Blur/mask outside ROI | Privacy Pipeline | ✅ Covered |
| **FR5.3** | No full frames to cloud | Architecture Design | ✅ Covered |
| **FR5.4** | Only transmit metadata | Data Flow | ✅ Covered |
| **FR6.1** | Camera preview on local network | Edge Admin Portal | ✅ Covered |
| **FR6.2** | ROI configuration UI | Edge Admin Portal | ✅ Covered |
| **FR6.3** | Display detection status | Edge Admin Portal | ✅ Covered |
| **FR6.4** | Not accessible from internet | Edge Admin Portal | ✅ Covered |

### Non-Functional Requirements Coverage

| Requirement | Target | Architecture Solution | Status |
|-------------|--------|----------------------|--------|
| **NFR1** | Detection <500ms | NCNN + motion trigger = 170-250ms | ✅ Met |
| **NFR2** | API response <200ms | FastAPI async + SQLite | ✅ Met |
| **NFR3** | PWA load <2s | Vite + local serve (33KB gzipped) | ✅ Met |
| **NFR4** | 95% uptime | systemd service | ✅ Design supports |
| **NFR5** | Power <15W | RPi 5 ~8W during detection | ✅ Met |
| **NFR6** | Cloud cost $0/mo | Local SQLite, no cloud required | ✅ Met |
| **NFR7** | 30-day retention | SQLite cleanup job (Phase 2) | ⏳ Deferred |
| **NFR8** | Offline mode | Fully local-first design | ✅ Met |

### Goal Alignment

| Goal | Success Metric | Architecture Support |
|------|----------------|---------------------|
| **G1** | ≥85% mAP | YOLO11n + custom training path documented |
| **G2** | Updates <5 seconds | Delta push + polling architecture |
| **G3** | Employee visibility | PWA with zero-friction access |
| **G4** | Hardware <$100 | CPU-only Basic tier ($80) |
| **G5** | Privacy preserved | ROI masking, metadata-only transmission |

### Cohesion Check: PASSED ✅

All 23 functional requirements are mapped to components. All must-have NFRs have solutions.

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | Winston/PAI | Initial architecture |
| 1.1 | 2026-01-10 | Winston/PAI | Added Raspberry Pi 4 support (ADR-005, platform configs, hardware BOM) |
| 1.2 | 2026-01-10 | Winston/PAI | Added Mac/Linux development tier for local testing |
| 1.3 | 2026-01-10 | PAI | **IMPLEMENTED** - All components built and tested locally |
| 1.4 | 2026-01-10 | PAI | Added `allowed_classes` feature for class filtering (FR1.6) |
| 1.5 | 2026-01-10 | PAI | Added `camera_index` setting for dev camera selection |
| 2.0 | 2026-01-11 | PAI | **LOCAL-FIRST MIGRATION** - Replaced Firestore with SQLite, updated all diagrams and ADRs |

---

## Implementation Notes

### Completed Implementation (2026-01-11)

**Edge Detection System:**
- YOLO11n exported to NCNN format successfully
- ByteTrack tracking with `fuse_score: true` configuration
- Motion detection (threshold: 0.008), ROI masking, inventory state management
- **Class filtering** - `allowed_classes` setting restricts detection to food-related COCO classes
- Flask admin portal with MJPEG camera preview
- Achieved ~45 FPS on Mac M4 Pro (development testing)

**Local Backend (SQLite):**
- FastAPI server with Pydantic v2 settings
- SQLAlchemy 2.0 ORM with SQLite database
- Basic authentication for admin API endpoints
- Full CRUD for inventory, events, config, users, alerts
- Audit logging for admin actions
- Health, ready, and info endpoints

**Consumer PWA:**
- Vue 3 + Vite + Pinia + Tailwind CSS v4
- Auto-refresh with 30-second polling
- Responsive snack card grid with stock indicators
- PWA manifest and service worker configured
- Build size: 33KB gzipped

**Key Fixes During Implementation:**
1. ByteTrack required `fuse_score: true` in tracker config
2. Numpy types needed conversion for JSON serialization
3. Pydantic v2 uses `model_config = SettingsConfigDict()` not `class Config`
4. Tailwind CSS v4 requires `@tailwindcss/vite` plugin
5. Vue store updated to match SQLite backend response format (array vs dictionary)

**Development Features:**
- `camera_index` setting to choose between cameras (0=iPhone, 1=built-in webcam on Mac)
- Set via `CAMERA_INDEX` environment variable or in `dev_config.json`
- Dev scripts: `scripts/start-dev.sh` and `scripts/stop-dev.sh` for easy local testing

---

**Related Documents:**
- [[FoodInsight PRD]] — Requirements
- [[FoodInsight Modernized Architecture Proposal]] — Technical foundation
