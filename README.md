# FoodInsight

Smart snack inventory monitoring system using YOLO11 object detection.

## Project Status: MVP COMPLETE

All components implemented and tested locally (2026-01-10).

| Component | Location | Status |
|-----------|----------|--------|
| Edge Detection | `detection/`, `admin/`, `privacy/` | Complete |
| Cloud Backend | `server/` | Complete |
| Consumer PWA | `app/` | Complete |

## Quick Start (Local Development)

```bash
# 1. Start backend (terminal 1)
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --port 8000 --reload

# 2. Start frontend (terminal 2)
cd app
bun install
bun run dev

# 3. Open http://localhost:5173
```

---

## Edge Device

### Features

- **Real-time Detection**: YOLO11n model optimized for ARM CPU (NCNN format)
- **Object Tracking**: ByteTrack for persistent item IDs across frames
- **Motion-Triggered**: Only runs inference when activity detected
- **Inventory Management**: Tracks item additions and removals
- **Privacy-First**: ROI masking, only metadata sent to cloud
- **Admin Portal**: Local web interface for configuration

## Supported Platforms

| Platform | CPU | Expected FPS | Cost | Notes |
|----------|-----|--------------|------|-------|
| Raspberry Pi 4 | Cortex-A72 4x 1.8GHz | 1-3 FPS | $55 | Production (budget) |
| Raspberry Pi 5 | Cortex-A76 4x 2.4GHz | 4-6 FPS | $80 | Production (recommended) |
| macOS / Linux | Any | 10+ FPS | - | Development / testing |

## Quick Start

### Development Testing (Mac/Linux Desktop)

Test the system locally before deploying to Raspberry Pi:

```bash
cd /path/to/foodinsight-edge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install ultralytics flask httpx opencv-python numpy

# Run in development mode (port 8080)
python run_dev.py
```

Open http://localhost:8080 to access the admin portal.

**What works in dev mode:**
- Camera capture via OpenCV (built-in webcam or USB)
- Admin portal with live preview
- ROI configuration UI
- Motion detection
- YOLO inference (if model exported)

**Optional - Enable real detection:**
```bash
# Activate virtual environment first
source .venv/bin/activate

# Export YOLO11n to NCNN format
yolo export model=yolo11n.pt format=ncnn

# Move model to project
mv yolo11n_ncnn_model models/
```

**To stop the server:**
```bash
pkill -f "python run_dev.py"
```

**macOS camera permission:** Grant Terminal/IDE camera access in **System Preferences > Privacy & Security > Camera**.

---

### Raspberry Pi Deployment

#### Prerequisites

- Raspberry Pi 4 or 5 (8GB recommended)
- Camera Module 3 or USB camera
- Python 3.11+

#### Installation

```bash
# Clone repository
git clone https://github.com/your-org/foodinsight-edge.git
cd foodinsight-edge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For Raspberry Pi camera support
pip install picamera2

# Export YOLO11n to NCNN (on dev machine)
yolo export model=yolo11n.pt format=ncnn

# Copy model to device
scp -r yolo11n_ncnn_model/ pi@raspberrypi:/opt/foodinsight/models/
```

### Configuration

```bash
# Copy to deployment location
sudo mkdir -p /opt/foodinsight
sudo cp -r . /opt/foodinsight/
sudo chown -R pi:pi /opt/foodinsight

# Create config file
cat > /opt/foodinsight/config.json << EOF
{
  "machine_id": "breakroom-001",
  "model_path": "/opt/foodinsight/models/yolo11n_ncnn_model",
  "api_url": "https://your-api.run.app",
  "api_key": "your-bearer-token"
}
EOF
```

### Running

```bash
# Direct execution
python main.py

# Or install as service
sudo cp systemd/foodinsight.service /etc/systemd/system/
sudo systemctl enable foodinsight
sudo systemctl start foodinsight
```

### Admin Portal

Access the admin portal at `http://<device-ip>/`

- View live camera feed with detection overlay
- Configure ROI (Region of Interest)
- Monitor inventory counts
- Check detection FPS and status

## Project Structure

```
foodinsight-edge/
├── detection/           # Detection components
│   ├── detector.py      # YOLO11n wrapper
│   ├── tracker.py       # ByteTrack integration
│   ├── motion.py        # Motion detection
│   ├── inventory.py     # State management
│   └── service.py       # Main orchestrator
├── admin/               # Flask admin portal
│   ├── app.py           # Flask application
│   └── templates/       # HTML templates
├── privacy/             # Privacy pipeline
│   └── pipeline.py      # ROI masking
├── api/                 # Cloud API client
│   └── client.py        # HTTP client
├── config/              # Configuration
│   ├── platform.py      # Platform detection
│   └── settings.py      # Settings management
├── tests/               # Unit tests
├── main.py              # Production entry point
├── run_dev.py           # Development runner (Mac/Linux)
└── systemd/             # Service files
```

## Testing

Run the test suite:

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
python -m pytest tests/ -v

# Run with coverage
pip install pytest-cov
python -m pytest tests/ --cov=detection --cov=privacy
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Admin dashboard |
| `/preview` | GET | MJPEG video stream |
| `/status` | GET | JSON status |
| `/roi` | GET/POST | ROI configuration |
| `/health` | GET | Health check |

## Platform Detection

The system auto-detects the platform and applies optimized settings:

| Platform | Input Size | Frame Skip | Motion Threshold |
|----------|------------|------------|------------------|
| RPi 5 | 640×640 | None | 0.02 |
| RPi 4 | 320×320 | Every 3rd | 0.015 |
| Desktop | 640×640 | None | 0.02 |

Platform is detected by reading `/proc/device-tree/model` on Linux. On macOS or unknown platforms, defaults to desktop settings.

---

## Full Project Structure

```
FoodInsight/
├── detection/           # Edge detection components
│   ├── detector.py      # YOLO11n wrapper
│   ├── tracker.py       # ByteTrack integration
│   ├── motion.py        # Motion detection
│   ├── inventory.py     # State management
│   └── service.py       # Main orchestrator
├── admin/               # Flask admin portal
│   ├── app.py           # Flask application
│   └── templates/       # HTML templates
├── privacy/             # Privacy pipeline
│   └── pipeline.py      # ROI masking
├── api/                 # Cloud API client
│   └── client.py        # HTTP client
├── config/              # Configuration
├── server/              # Cloud backend (FastAPI)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   ├── models/
│   │   └── services/
│   └── tests/
├── app/                 # Consumer PWA (Vue 3)
│   ├── src/
│   │   ├── views/
│   │   ├── components/
│   │   ├── stores/
│   │   └── composables/
│   └── vite.config.ts
├── models/              # YOLO model files
├── main.py              # Edge production entry
├── run_dev.py           # Edge development runner
└── README.md
```

## Related Documentation

- [Server README](server/README.md) - FastAPI backend
- [App README](app/README.md) - Vue 3 PWA
- [PRD](../KnowledgeBase/Projects/FoodInsight/FoodInsight%20PRD.md) - Requirements
- [Architecture](../KnowledgeBase/Projects/FoodInsight/FoodInsight%20Solution%20Architecture.md) - Technical design

## Next Steps

1. **Deploy to Cloud** - Cloud Run (backend) + Cloudflare Pages (PWA)
2. **Train Custom Model** - Fine-tune YOLO11n on office snack dataset
3. **Add Firestore** - Replace mock router with real Firestore
4. **Field Testing** - Deploy to actual break room

## License

MIT
