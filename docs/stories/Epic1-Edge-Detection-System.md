# Epic 1: Edge Detection System - User Stories

**Epic Goal:** Camera captures snacks, YOLO11 detects them, inventory state managed locally

**PRD Reference:** [[FoodInsight PRD]]
**Architecture Reference:** [[FoodInsight Solution Architecture]]

**Epic Acceptance Criteria:**
- [ ] Detection runs at 4-6 FPS on RPi 5 CPU
- [ ] Admin can configure ROI via local web interface
- [ ] System detects when items taken/added within 5 seconds
- [ ] Privacy: only ROI area processed

---

## E1-S1: Set Up RPi 5 with Camera and Base OS

### User Story

**As a** developer setting up the FoodInsight edge device,
**I want** a properly configured Raspberry Pi 5 with camera and Python environment,
**So that** I have a stable foundation for running the detection pipeline.

### Acceptance Criteria

```gherkin
Feature: RPi 5 Base Setup

Scenario: Operating system is properly configured
  Given a Raspberry Pi 5 8GB with 64GB microSD
  When the setup script completes
  Then Raspberry Pi OS 64-bit Bookworm is installed
  And the system boots successfully
  And SSH access is enabled
  And the hostname is set to "foodinsight-edge"

Scenario: Python environment is ready
  Given the base OS is configured
  When I check the Python installation
  Then Python 3.11+ is available
  And a virtual environment exists at /opt/foodinsight/.venv
  And pip is updated to latest version

Scenario: Camera is functional
  Given the RPi Camera Module 3 is connected
  When I run the camera test script
  Then the camera captures a test image successfully
  And the image is saved to /tmp/camera_test.jpg
  And the image resolution is at least 1280x720

Scenario: System services are configured
  Given the base setup is complete
  When I check systemd configuration
  Then a foodinsight.service unit file exists
  And the service is set to start on boot
```

### Technical Notes

**Hardware:**
- Raspberry Pi 5 8GB
- RPi Camera Module 3 (or USB camera alternative)
- 64GB microSD Class A2
- 27W USB-C power supply

**Software Stack:**
- Raspberry Pi OS 64-bit (Bookworm)
- Python 3.11+
- picamera2 library for camera access

**Setup Commands:**
```bash
# Flash SD card with Raspberry Pi Imager
# Enable SSH, set hostname, configure WiFi in imager

# On first boot
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11-venv python3-picamera2 git

# Create application directory
sudo mkdir -p /opt/foodinsight
sudo chown $USER:$USER /opt/foodinsight

# Create virtual environment
python3 -m venv /opt/foodinsight/.venv
source /opt/foodinsight/.venv/bin/activate
pip install --upgrade pip
```

### Definition of Done

- [ ] RPi 5 boots with Bookworm 64-bit
- [ ] SSH access works with key authentication
- [ ] Camera test captures image successfully
- [ ] Python 3.11+ virtual environment created
- [ ] systemd service unit file in place
- [ ] Documentation updated with setup steps

### Dependencies

- **Hardware:** RPi 5, Camera Module 3, SD card, power supply
- **Blocked by:** Hardware procurement

### Complexity

**Points:** 2 (Small)
**Risk:** Low - standard Raspberry Pi setup

---

## E1-S2: Implement YOLO11n Inference with NCNN

### User Story

**As a** detection service,
**I want** to run YOLO11n inference on camera frames using CPU-optimized NCNN format,
**So that** I can detect snack items at 4-6 FPS without hardware acceleration.

### Acceptance Criteria

```gherkin
Feature: YOLO11n Detection

Scenario: Model loads successfully
  Given the YOLO11n NCNN model is in /opt/foodinsight/models/
  When the detection service starts
  Then the model loads without errors
  And memory usage is under 500MB
  And startup time is under 10 seconds

Scenario: Detection produces valid results
  Given the model is loaded
  When I process a test image with snacks
  Then bounding boxes are returned for detected objects
  And each detection includes class_id, confidence, and bbox coordinates
  And confidence scores are between 0.0 and 1.0

Scenario: Inference meets performance target
  Given the model is loaded
  And the camera is streaming at 640x480
  When I run continuous detection for 60 seconds
  Then average FPS is at least 4
  And no frame takes longer than 500ms to process
  And CPU usage stays under 80%

Scenario: Detection filters by confidence threshold
  Given the model is loaded
  And confidence threshold is set to 0.4
  When I process an image with low-confidence detections
  Then only detections above 0.4 confidence are returned

Scenario: Detection filters by allowed classes
  Given the model is loaded
  And allowed_classes is set to ["bottle", "cup", "banana", "apple"]
  When I process an image with a person and a bottle
  Then only the bottle detection is returned
  And the person detection is filtered out
```

### Technical Notes

**Model Export:**
```bash
# Export YOLO11n to NCNN format (on dev machine)
pip install ultralytics
yolo export model=yolo11n.pt format=ncnn

# Copy to RPi
scp -r yolo11n_ncnn_model/ pi@foodinsight-edge:/opt/foodinsight/models/
```

**Key Implementation:**
```python
# detection/model.py
from ultralytics import YOLO
import numpy as np

class SnackDetector:
    def __init__(self, model_path: str, confidence: float = 0.4):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame: np.ndarray) -> list[Detection]:
        results = self.model.predict(
            frame,
            conf=self.confidence,
            verbose=False,
            imgsz=640
        )
        return self._parse_results(results[0])

    def _parse_results(self, result) -> list[Detection]:
        detections = []
        for box in result.boxes:
            detections.append(Detection(
                class_id=int(box.cls),
                class_name=result.names[int(box.cls)],
                confidence=float(box.conf),
                bbox=box.xyxy[0].tolist()
            ))
        return detections
```

**Performance Tuning:**
- Use `imgsz=640` for balance of speed/accuracy
- Consider `imgsz=320` if FPS is too low
- Set `verbose=False` to reduce logging overhead

### Definition of Done

- [ ] YOLO11n NCNN model deployed to RPi
- [ ] Detection wrapper class implemented
- [ ] Unit tests pass for detection functionality
- [ ] Performance benchmark shows ≥4 FPS
- [ ] Memory usage documented
- [ ] Class filtering via `allowed_classes` config working

### Dependencies

- **Requires:** E1-S1 (RPi 5 Setup)
- **Blocked by:** None after E1-S1

### Complexity

**Points:** 3 (Medium)
**Risk:** Medium - NCNN performance on ARM needs validation

---

## E1-S3: Add Motion-Triggered Detection

### User Story

**As a** detection service running on CPU,
**I want** to only run expensive YOLO inference when motion is detected,
**So that** I conserve CPU resources and reduce power consumption.

### Acceptance Criteria

```gherkin
Feature: Motion-Triggered Detection

Scenario: Motion is detected when items move
  Given the camera is capturing frames
  And the motion detector is initialized
  When a hand enters the frame and takes an item
  Then motion_detected returns True
  And YOLO inference is triggered

Scenario: No detection when scene is static
  Given the camera is capturing a static scene
  When 10 seconds pass with no movement
  Then motion_detected returns False for each frame
  And YOLO inference is NOT triggered
  And CPU usage drops below 20%

Scenario: Motion threshold is configurable
  Given motion threshold is set to 0.02 (2% pixel change)
  When minor lighting fluctuation occurs (< 2% change)
  Then motion_detected returns False
  When significant movement occurs (> 2% change)
  Then motion_detected returns True

Scenario: Detection resumes after motion stops
  Given motion was detected and YOLO ran
  When motion stops for 5 seconds
  Then system returns to motion-watching mode
  And YOLO inference pauses
```

### Technical Notes

**Implementation:**
```python
# detection/motion.py
import cv2
import numpy as np

class MotionDetector:
    def __init__(self, threshold: float = 0.02, blur_size: int = 21):
        self.threshold = threshold
        self.blur_size = blur_size
        self.prev_frame = None

    def detect(self, frame: np.ndarray) -> bool:
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)

        if self.prev_frame is None:
            self.prev_frame = gray
            return True  # First frame, run detection

        # Calculate frame difference
        diff = cv2.absdiff(self.prev_frame, gray)
        motion_score = np.mean(diff) / 255.0

        self.prev_frame = gray
        return motion_score > self.threshold

    def reset(self):
        self.prev_frame = None
```

**Integration with Detection Service:**
```python
class DetectionService:
    def __init__(self, config):
        self.detector = SnackDetector(config.model_path)
        self.motion = MotionDetector(threshold=config.motion_threshold)
        self.last_detections = []

    def process_frame(self, frame: np.ndarray) -> list[Detection]:
        if self.motion.detect(frame):
            self.last_detections = self.detector.detect(frame)
        return self.last_detections
```

**Tuning Parameters:**
- `threshold=0.02` - 2% pixel change triggers detection
- `blur_size=21` - Gaussian blur to reduce noise
- Adjust threshold based on lighting conditions

### Definition of Done

- [ ] MotionDetector class implemented
- [ ] Integrated with detection service
- [ ] Unit tests for motion detection scenarios
- [ ] Power consumption measured (idle vs active)
- [ ] Threshold tuned for break room lighting

### Dependencies

- **Requires:** E1-S2 (YOLO11n Inference)
- **Blocked by:** None after E1-S2

### Complexity

**Points:** 2 (Small)
**Risk:** Low - well-understood technique

---

## E1-S4: Implement ByteTrack Object Tracking

### User Story

**As a** detection service,
**I want** to maintain persistent object IDs across frames using ByteTrack,
**So that** I can accurately detect when specific items are taken or added.

### Acceptance Criteria

```gherkin
Feature: ByteTrack Object Tracking

Scenario: Objects maintain persistent IDs
  Given tracking is enabled
  When a snack item is detected across 10 consecutive frames
  Then the item maintains the same track_id throughout
  And the track_id is a positive integer

Scenario: New objects get new IDs
  Given existing items are being tracked
  When a new item appears in frame (restocking)
  Then the new item receives a unique track_id
  And existing items keep their original track_ids

Scenario: Disappeared objects are marked
  Given an item with track_id=5 is being tracked
  When the item disappears for 30 frames (taken by someone)
  Then the tracker reports track_id=5 as "lost"
  And the disappeared event is logged

Scenario: Temporary occlusion is handled
  Given an item is being tracked
  When a hand briefly occludes the item (< 10 frames)
  Then the item retains its track_id after occlusion
  And no "lost" event is generated
```

### Technical Notes

**Using Ultralytics Built-in Tracking:**
```python
# detection/tracker.py
from ultralytics import YOLO

class TrackedDetector:
    def __init__(self, model_path: str, tracker_config: str = "bytetrack.yaml"):
        self.model = YOLO(model_path)
        self.tracker_config = tracker_config

    def detect_and_track(self, frame) -> list[TrackedDetection]:
        results = self.model.track(
            frame,
            tracker=self.tracker_config,
            persist=True,  # Keep track IDs across calls
            conf=0.4,
            verbose=False
        )
        return self._parse_tracked_results(results[0])

    def _parse_tracked_results(self, result) -> list[TrackedDetection]:
        detections = []
        if result.boxes.id is not None:
            for i, box in enumerate(result.boxes):
                detections.append(TrackedDetection(
                    track_id=int(result.boxes.id[i]),
                    class_id=int(box.cls),
                    class_name=result.names[int(box.cls)],
                    confidence=float(box.conf),
                    bbox=box.xyxy[0].tolist()
                ))
        return detections
```

**ByteTrack Configuration (bytetrack.yaml):**
```yaml
tracker_type: bytetrack
track_high_thresh: 0.5
track_low_thresh: 0.1
new_track_thresh: 0.6
track_buffer: 30
match_thresh: 0.8
```

**Key Parameters:**
- `track_buffer=30` - frames before marking track as lost
- `persist=True` - maintain IDs across method calls
- `match_thresh=0.8` - IoU threshold for matching

### Definition of Done

- [ ] ByteTrack integrated with YOLO model
- [ ] TrackedDetection dataclass defined
- [ ] Track persistence verified across frames
- [ ] Disappearance detection working
- [ ] Unit tests for tracking scenarios

### Dependencies

- **Requires:** E1-S2 (YOLO11n Inference)
- **Can parallel with:** E1-S3 (Motion Detection)

### Complexity

**Points:** 3 (Medium)
**Risk:** Medium - tracking accuracy depends on detection quality

---

## E1-S5: Create Inventory State Manager

### User Story

**As a** detection service,
**I want** to maintain inventory counts and detect additions/removals,
**So that** I can generate delta updates for the cloud backend.

### Acceptance Criteria

```gherkin
Feature: Inventory State Management

Scenario: Counts are maintained per class
  Given the inventory manager is initialized
  When detections show 5 chips_bag and 3 candy_bar
  Then inventory["chips_bag"] equals 5
  And inventory["candy_bar"] equals 3

Scenario: Item removal generates SNACK_TAKEN event
  Given inventory shows 5 chips_bag
  When tracking reports a chips_bag track_id as lost
  Then a SNACK_TAKEN event is generated
  And event.item equals "chips_bag"
  And inventory["chips_bag"] equals 4

Scenario: Item addition generates SNACK_ADDED event
  Given inventory shows 3 candy_bar
  When a new candy_bar track_id appears
  Then a SNACK_ADDED event is generated
  And event.item equals "candy_bar"
  And inventory["candy_bar"] equals 4

Scenario: Debouncing prevents false events
  Given tracking shows 5 items
  When an item briefly disappears for 3 frames then reappears
  Then no SNACK_TAKEN event is generated
  And inventory count remains unchanged

Scenario: Delta updates are batched
  Given multiple events occur within 1 second
  When get_delta() is called
  Then a single InventoryDelta is returned
  And it contains all pending events
  And events are cleared after retrieval
```

### Technical Notes

**Implementation:**
```python
# detection/inventory.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import defaultdict

class EventType(Enum):
    SNACK_TAKEN = "SNACK_TAKEN"
    SNACK_ADDED = "SNACK_ADDED"

@dataclass
class InventoryEvent:
    type: EventType
    item: str
    timestamp: datetime
    track_id: int
    count_before: int
    count_after: int

@dataclass
class InventoryDelta:
    machine_id: str
    timestamp: datetime
    inventory: dict[str, int]
    events: list[InventoryEvent]

class InventoryStateManager:
    def __init__(self, machine_id: str, debounce_frames: int = 10):
        self.machine_id = machine_id
        self.debounce_frames = debounce_frames
        self.current_counts: dict[str, int] = defaultdict(int)
        self.active_tracks: dict[int, str] = {}  # track_id -> class_name
        self.pending_events: list[InventoryEvent] = []
        self.disappeared_tracks: dict[int, int] = {}  # track_id -> frames_missing

    def update(self, detections: list[TrackedDetection]) -> list[InventoryEvent]:
        events = []
        current_track_ids = set()

        for det in detections:
            current_track_ids.add(det.track_id)

            # New track = new item
            if det.track_id not in self.active_tracks:
                self.active_tracks[det.track_id] = det.class_name
                count_before = self.current_counts[det.class_name]
                self.current_counts[det.class_name] += 1
                events.append(InventoryEvent(
                    type=EventType.SNACK_ADDED,
                    item=det.class_name,
                    timestamp=datetime.utcnow(),
                    track_id=det.track_id,
                    count_before=count_before,
                    count_after=self.current_counts[det.class_name]
                ))

        # Check for disappeared tracks
        for track_id, class_name in list(self.active_tracks.items()):
            if track_id not in current_track_ids:
                self.disappeared_tracks[track_id] = \
                    self.disappeared_tracks.get(track_id, 0) + 1

                if self.disappeared_tracks[track_id] >= self.debounce_frames:
                    count_before = self.current_counts[class_name]
                    self.current_counts[class_name] = max(0, count_before - 1)
                    events.append(InventoryEvent(
                        type=EventType.SNACK_TAKEN,
                        item=class_name,
                        timestamp=datetime.utcnow(),
                        track_id=track_id,
                        count_before=count_before,
                        count_after=self.current_counts[class_name]
                    ))
                    del self.active_tracks[track_id]
                    del self.disappeared_tracks[track_id]
            else:
                # Track reappeared, reset counter
                if track_id in self.disappeared_tracks:
                    del self.disappeared_tracks[track_id]

        self.pending_events.extend(events)
        return events

    def get_delta(self) -> InventoryDelta | None:
        if not self.pending_events:
            return None

        delta = InventoryDelta(
            machine_id=self.machine_id,
            timestamp=datetime.utcnow(),
            inventory=dict(self.current_counts),
            events=self.pending_events.copy()
        )
        self.pending_events.clear()
        return delta
```

### Definition of Done

- [ ] InventoryStateManager class implemented
- [ ] Event generation for SNACK_TAKEN/SNACK_ADDED
- [ ] Debouncing logic prevents false positives
- [ ] Delta batching works correctly
- [ ] Unit tests cover all scenarios
- [ ] Integration test with tracker

### Dependencies

- **Requires:** E1-S4 (ByteTrack Integration)
- **Blocked by:** None after E1-S4

### Complexity

**Points:** 5 (Large)
**Risk:** Medium - state management logic is complex

---

## E1-S6: Build Edge Admin Portal with Camera Preview

### User Story

**As an** IT admin,
**I want** a local web interface to view the camera feed and detection status,
**So that** I can verify the system is working correctly during setup.

### Acceptance Criteria

```gherkin
Feature: Edge Admin Portal

Scenario: Dashboard loads successfully
  Given the admin portal is running on port 80
  When I navigate to http://<device-ip>/
  Then the dashboard page loads
  And I see the device status (online/offline)
  And I see current detection FPS
  And I see current inventory counts

Scenario: Camera preview streams
  Given I am on the dashboard
  When I view the camera preview section
  Then I see a live MJPEG stream
  And detection bounding boxes are overlaid
  And the stream updates at least 2 FPS

Scenario: Status endpoint returns JSON
  Given the admin portal is running
  When I GET /status
  Then I receive JSON with:
    | Field | Type |
    | status | string |
    | fps | number |
    | inventory | object |
    | last_detection | string |

Scenario: Portal is only accessible on LAN
  Given the admin portal is running
  When I try to access from external IP
  Then the connection is refused
```

### Technical Notes

**Flask Application:**
```python
# admin/app.py
from flask import Flask, Response, render_template, jsonify
import cv2
import threading

app = Flask(__name__)

# Shared state
camera_frame = None
detection_overlay = None
status_data = {
    "status": "initializing",
    "fps": 0.0,
    "inventory": {},
    "last_detection": None
}
frame_lock = threading.Lock()

@app.route("/")
def dashboard():
    return render_template("index.html", status=status_data)

@app.route("/preview")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

def generate_frames():
    while True:
        with frame_lock:
            if camera_frame is not None:
                frame = camera_frame.copy()
                if detection_overlay is not None:
                    frame = draw_detections(frame, detection_overlay)
                _, buffer = cv2.imencode(".jpg", frame)
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" +
                       buffer.tobytes() + b"\r\n")

@app.route("/status")
def get_status():
    return jsonify(status_data)

def update_frame(frame, detections):
    global camera_frame, detection_overlay
    with frame_lock:
        camera_frame = frame
        detection_overlay = detections

def update_status(fps, inventory):
    status_data["status"] = "running"
    status_data["fps"] = fps
    status_data["inventory"] = inventory
    status_data["last_detection"] = datetime.utcnow().isoformat()
```

**Dashboard Template (templates/index.html):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>FoodInsight Admin</title>
    <script src="/static/htmx.min.js"></script>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        .status { padding: 10px; margin: 10px 0; }
        .online { background: #d4edda; }
        .preview { max-width: 640px; }
        .inventory { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .item { padding: 10px; background: #f8f9fa; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>FoodInsight Edge Admin</h1>

    <div class="status online" hx-get="/status" hx-trigger="every 2s" hx-swap="innerHTML">
        Status: {{ status.status }} | FPS: {{ status.fps }}
    </div>

    <h2>Camera Preview</h2>
    <img class="preview" src="/preview" alt="Camera feed">

    <h2>Current Inventory</h2>
    <div class="inventory" hx-get="/inventory-partial" hx-trigger="every 5s">
        {% for item, count in status.inventory.items() %}
        <div class="item">{{ item }}: {{ count }}</div>
        {% endfor %}
    </div>
</body>
</html>
```

**Network Binding (LAN only):**
```python
# Run on local interface only
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)  # Firewall restricts external access
```

### Definition of Done

- [ ] Flask app with dashboard route
- [ ] MJPEG streaming endpoint
- [ ] Detection overlay on video feed
- [ ] Status JSON endpoint
- [ ] HTMX auto-refresh working
- [ ] Systemd service configured for port 80

### Dependencies

- **Requires:** E1-S2 (Detection working)
- **Can parallel with:** E1-S3, E1-S4, E1-S5

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - standard Flask patterns

---

## E1-S7: Implement ROI Configuration UI

### User Story

**As an** IT admin,
**I want** to draw a rectangle on the camera preview to define the snack shelf region,
**So that** detection only processes the relevant area.

### Acceptance Criteria

```gherkin
Feature: ROI Configuration

Scenario: ROI can be drawn on preview
  Given I am on the ROI configuration page
  When I click and drag on the camera preview
  Then a rectangle is drawn following my mouse
  And the rectangle coordinates are displayed

Scenario: ROI is saved persistently
  Given I have drawn an ROI rectangle
  When I click "Save Configuration"
  Then the ROI is saved to config file
  And a success message is displayed
  And the ROI persists across reboots

Scenario: Detection respects ROI
  Given ROI is configured to x1=100, y1=50, x2=540, y2=400
  When the detection service processes a frame
  Then only objects within the ROI are detected
  And objects outside ROI are ignored

Scenario: ROI can be reset
  Given an ROI is configured
  When I click "Reset to Full Frame"
  Then the ROI is cleared
  And detection processes the entire frame
```

### Technical Notes

**ROI Configuration Page:**
```html
<!-- templates/roi.html -->
<h2>Configure Detection Region</h2>
<p>Click and drag to select the snack shelf area:</p>

<div id="roi-container" style="position: relative; display: inline-block;">
    <img id="preview" src="/preview/snapshot" style="max-width: 100%;">
    <div id="roi-overlay" style="position: absolute; border: 2px dashed #00ff00; display: none;"></div>
</div>

<div id="coordinates">
    ROI: <span id="roi-coords">Not set</span>
</div>

<button id="save-btn" hx-post="/roi" hx-vals="js:{...getRoiCoords()}" hx-swap="none">
    Save Configuration
</button>
<button id="reset-btn" hx-post="/roi/reset" hx-swap="none">
    Reset to Full Frame
</button>

<script>
let startX, startY, isDrawing = false;
const container = document.getElementById('roi-container');
const overlay = document.getElementById('roi-overlay');
const preview = document.getElementById('preview');

preview.addEventListener('mousedown', (e) => {
    const rect = preview.getBoundingClientRect();
    startX = e.clientX - rect.left;
    startY = e.clientY - rect.top;
    isDrawing = true;
    overlay.style.display = 'block';
});

preview.addEventListener('mousemove', (e) => {
    if (!isDrawing) return;
    const rect = preview.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;

    overlay.style.left = Math.min(startX, currentX) + 'px';
    overlay.style.top = Math.min(startY, currentY) + 'px';
    overlay.style.width = Math.abs(currentX - startX) + 'px';
    overlay.style.height = Math.abs(currentY - startY) + 'px';
});

preview.addEventListener('mouseup', (e) => {
    isDrawing = false;
    updateCoordinates();
});

function getRoiCoords() {
    // Scale from display to actual frame coordinates
    const scale = preview.naturalWidth / preview.clientWidth;
    return {
        x1: Math.round(parseInt(overlay.style.left) * scale),
        y1: Math.round(parseInt(overlay.style.top) * scale),
        x2: Math.round((parseInt(overlay.style.left) + parseInt(overlay.style.width)) * scale),
        y2: Math.round((parseInt(overlay.style.top) + parseInt(overlay.style.height)) * scale)
    };
}
</script>
```

**Backend Routes:**
```python
# admin/app.py
import json
from pathlib import Path

CONFIG_PATH = Path("/opt/foodinsight/config.json")

@app.route("/roi", methods=["GET"])
def roi_page():
    config = load_config()
    return render_template("roi.html", roi=config.get("roi"))

@app.route("/roi", methods=["POST"])
def save_roi():
    data = request.json
    config = load_config()
    config["roi"] = {
        "x1": data["x1"],
        "y1": data["y1"],
        "x2": data["x2"],
        "y2": data["y2"]
    }
    save_config(config)
    # Notify detection service to reload config
    reload_detection_config()
    return {"status": "ok", "message": "ROI saved"}

@app.route("/roi/reset", methods=["POST"])
def reset_roi():
    config = load_config()
    config["roi"] = None
    save_config(config)
    reload_detection_config()
    return {"status": "ok", "message": "ROI reset"}

@app.route("/preview/snapshot")
def snapshot():
    # Return single frame for ROI configuration
    with frame_lock:
        if camera_frame is not None:
            _, buffer = cv2.imencode(".jpg", camera_frame)
            return Response(buffer.tobytes(), mimetype="image/jpeg")
    return "", 404
```

### Definition of Done

- [ ] ROI configuration page with drag-to-select
- [ ] Coordinates display and save functionality
- [ ] Config persistence in JSON file
- [ ] Detection service respects ROI setting
- [ ] Reset to full frame works
- [ ] Visual feedback on save

### Dependencies

- **Requires:** E1-S6 (Admin Portal)
- **Blocked by:** None after E1-S6

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - standard web UI patterns

---

## E1-S8: Add Privacy Masking

### User Story

**As a** privacy-conscious deployment,
**I want** areas outside the configured ROI to be blurred,
**So that** the admin preview doesn't show people or other sensitive areas.

### Acceptance Criteria

```gherkin
Feature: Privacy Masking

Scenario: Areas outside ROI are blurred
  Given ROI is set to the snack shelf area
  When viewing the admin camera preview
  Then the snack shelf area is clear
  And everything outside the ROI is blurred

Scenario: Blur intensity is configurable
  Given blur_intensity is set to 51 (kernel size)
  When processing a frame
  Then the blurred area uses 51x51 Gaussian blur
  And the blurred area is unrecognizable

Scenario: No masking when ROI is not set
  Given ROI is not configured (full frame mode)
  When viewing the admin camera preview
  Then the entire frame is displayed without blur

Scenario: Only ROI is processed for detection
  Given ROI is configured
  When the detection service runs
  Then only the ROI region is sent to YOLO
  And detection does not see blurred areas
```

### Technical Notes

**Privacy Pipeline:**
```python
# privacy/pipeline.py
import cv2
import numpy as np

class PrivacyPipeline:
    def __init__(self, blur_intensity: int = 51):
        self.blur_intensity = blur_intensity
        self.roi = None

    def set_roi(self, roi: dict | None):
        """Set ROI from config: {x1, y1, x2, y2}"""
        self.roi = roi

    def process_for_display(self, frame: np.ndarray) -> np.ndarray:
        """Apply blur outside ROI for admin display."""
        if self.roi is None:
            return frame

        x1, y1, x2, y2 = self.roi["x1"], self.roi["y1"], self.roi["x2"], self.roi["y2"]

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
        """Crop frame to ROI for detection processing."""
        if self.roi is None:
            return frame

        x1, y1, x2, y2 = self.roi["x1"], self.roi["y1"], self.roi["x2"], self.roi["y2"]
        return frame[y1:y2, x1:x2]

    def adjust_detections(self, detections: list, offset: tuple = None) -> list:
        """Adjust detection coordinates back to full frame."""
        if self.roi is None or offset is None:
            return detections

        x1, y1 = self.roi["x1"], self.roi["y1"]
        for det in detections:
            det.bbox[0] += x1
            det.bbox[1] += y1
            det.bbox[2] += x1
            det.bbox[3] += y1
        return detections
```

**Integration with Detection Service:**
```python
class DetectionService:
    def __init__(self, config):
        self.detector = TrackedDetector(config.model_path)
        self.motion = MotionDetector()
        self.inventory = InventoryStateManager(config.machine_id)
        self.privacy = PrivacyPipeline(config.blur_intensity)

        # Load ROI from config
        if config.roi:
            self.privacy.set_roi(config.roi)

    def process_frame(self, frame: np.ndarray) -> tuple[list, np.ndarray]:
        # Crop to ROI for detection
        detection_frame = self.privacy.crop_for_detection(frame)

        if self.motion.detect(detection_frame):
            detections = self.detector.detect_and_track(detection_frame)
            # Adjust coordinates back to full frame
            detections = self.privacy.adjust_detections(detections)
            self.inventory.update(detections)

        # Create display frame with privacy masking
        display_frame = self.privacy.process_for_display(frame)

        return detections, display_frame
```

### Definition of Done

- [ ] PrivacyPipeline class implemented
- [ ] Blur outside ROI working
- [ ] Detection crops to ROI before processing
- [ ] Coordinate adjustment working
- [ ] Visual verification in admin preview
- [ ] Unit tests for privacy functions

### Dependencies

- **Requires:** E1-S7 (ROI Configuration)
- **Blocked by:** None after E1-S7

### Complexity

**Points:** 2 (Small)
**Risk:** Low - straightforward image processing

---

## Epic 1 Summary

| Story | Title | Points | Dependencies |
|-------|-------|--------|--------------|
| E1-S1 | RPi 5 Setup | 2 | Hardware |
| E1-S2 | YOLO11n Inference | 3 | E1-S1 |
| E1-S3 | Motion Detection | 2 | E1-S2 |
| E1-S4 | ByteTrack Integration | 3 | E1-S2 |
| E1-S5 | Inventory State Manager | 5 | E1-S4 |
| E1-S6 | Admin Portal | 3 | E1-S2 |
| E1-S7 | ROI Configuration | 3 | E1-S6 |
| E1-S8 | Privacy Masking | 2 | E1-S7 |
| **Total** | | **23** | |

### Dependency Graph

```
E1-S1 (Setup)
    │
    ▼
E1-S2 (YOLO11n) ─────────────────┐
    │                            │
    ├──► E1-S3 (Motion)          │
    │                            │
    └──► E1-S4 (ByteTrack)       │
              │                  │
              ▼                  ▼
         E1-S5 (Inventory)   E1-S6 (Admin)
                                 │
                                 ▼
                            E1-S7 (ROI)
                                 │
                                 ▼
                            E1-S8 (Privacy)
```

### Recommended Implementation Order

1. **Week 1:** E1-S1 → E1-S2 (foundation)
2. **Week 2:** E1-S3, E1-S4 in parallel (detection enhancements)
3. **Week 2-3:** E1-S5 (inventory logic)
4. **Week 3:** E1-S6 → E1-S7 → E1-S8 (admin UI)

---

## Development Testing

The edge detection system can be tested on Mac/Linux desktop before RPi deployment:

```bash
cd /path/to/foodinsight-edge
python3 -m venv .venv && source .venv/bin/activate
pip install ultralytics flask httpx opencv-python numpy
python run_dev.py  # Uses built-in webcam by default

# To use iPhone via Continuity Camera:
CAMERA_INDEX=0 python run_dev.py
```

**Development mode features:**
- Uses OpenCV VideoCapture instead of picamera2
- Configurable camera via `CAMERA_INDEX` env var (0=iPhone, 1=built-in webcam)
- Runs admin portal on port 8080 (no sudo)
- Logs to `./logs/` instead of `/var/log/`
- Config stored in `./dev_config.json`
- Mock detection mode if model not present

**Platform detection:**
| Platform | Auto-detected | Settings |
|----------|---------------|----------|
| RPi 5 | Yes | 640×640, every frame |
| RPi 4 | Yes | 320×320, skip 2 frames |
| macOS/Desktop | Defaults | 640×640, every frame |

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | PAI | Initial stories |
| 1.1 | 2026-01-10 | PAI | Added `allowed_classes` filtering scenario and DoD item |
| 1.2 | 2026-01-10 | PAI | Added `camera_index` for dev camera selection |
