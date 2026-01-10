"""Flask admin portal for FoodInsight edge device."""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
from flask import Flask, Response, jsonify, render_template, request

logger = logging.getLogger(__name__)

# Shared state (thread-safe access via lock)
_frame_lock = threading.Lock()
_camera_frame: Optional[Any] = None
_detections: List[Any] = []
_status_data: Dict[str, Any] = {
    "status": "initializing",
    "fps": 0.0,
    "frame_count": 0,
    "inventory": {},
    "last_detection": None,
    "motion_active": False,
}

# Configuration
CONFIG_PATH = Path("/opt/foodinsight/config.json")


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )

    # Register routes
    register_routes(app)

    return app


def register_routes(app: Flask) -> None:
    """Register all routes on the Flask app."""

    @app.route("/")
    def dashboard():
        """Main dashboard page."""
        return render_template("index.html", status=_status_data)

    @app.route("/preview")
    def video_feed():
        """MJPEG video stream endpoint."""
        return Response(
            generate_frames(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    @app.route("/preview/snapshot")
    def snapshot():
        """Single frame snapshot for ROI configuration."""
        with _frame_lock:
            if _camera_frame is not None:
                # Encode as JPEG without detection overlay
                _, buffer = cv2.imencode(".jpg", _camera_frame)
                return Response(buffer.tobytes(), mimetype="image/jpeg")
        return "", 404

    @app.route("/status")
    def get_status():
        """JSON status endpoint."""
        return jsonify(_status_data)

    @app.route("/inventory")
    def get_inventory():
        """JSON inventory endpoint."""
        return jsonify(_status_data.get("inventory", {}))

    @app.route("/inventory-partial")
    def inventory_partial():
        """HTMX partial for inventory display."""
        inventory = _status_data.get("inventory", {})
        html = ""
        for item, count in inventory.items():
            status_class = "in-stock" if count > 0 else "out-of-stock"
            html += f'<div class="item {status_class}">{item}: {count}</div>'
        if not inventory:
            html = '<div class="item">No items detected</div>'
        return html

    @app.route("/roi")
    def roi_page():
        """ROI configuration page."""
        config = load_config()
        return render_template("roi.html", roi=config.get("roi"))

    @app.route("/roi", methods=["POST"])
    def save_roi():
        """Save ROI configuration."""
        try:
            data = request.json
            config = load_config()
            config["roi"] = {
                "x1": int(data["x1"]),
                "y1": int(data["y1"]),
                "x2": int(data["x2"]),
                "y2": int(data["y2"]),
            }
            save_config(config)

            # Signal detection service to reload
            notify_config_reload()

            return jsonify({"status": "ok", "message": "ROI saved"})
        except Exception as e:
            logger.error(f"Failed to save ROI: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route("/roi/reset", methods=["POST"])
    def reset_roi():
        """Reset ROI to full frame."""
        try:
            config = load_config()
            config["roi"] = None
            save_config(config)
            notify_config_reload()
            return jsonify({"status": "ok", "message": "ROI reset"})
        except Exception as e:
            logger.error(f"Failed to reset ROI: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route("/health")
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


def generate_frames():
    """Generate MJPEG frames for video stream."""
    while True:
        with _frame_lock:
            if _camera_frame is not None:
                frame = _camera_frame.copy()
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
                )

        # Limit frame rate for streaming
        import time
        time.sleep(0.1)  # ~10 FPS max for preview


def update_frame(frame: Any, detections: List[Any]) -> None:
    """Update the current frame (called by detection service)."""
    global _camera_frame, _detections
    with _frame_lock:
        _camera_frame = frame
        _detections = detections


def update_status(status: Any) -> None:
    """Update status data (called by detection service)."""
    global _status_data
    _status_data = {
        "status": status.status,
        "fps": float(status.fps),  # Ensure Python float for JSON
        "frame_count": int(status.frame_count),  # Ensure Python int
        "inventory": {k: int(v) for k, v in status.inventory.items()},  # Convert numpy ints
        "last_detection": status.last_detection_time.isoformat() if status.last_detection_time else None,
        "motion_active": bool(status.motion_active),  # Convert numpy bool to Python bool
    }


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def notify_config_reload() -> None:
    """Notify detection service to reload configuration."""
    # Signal file for config reload
    signal_file = CONFIG_PATH.parent / ".reload"
    signal_file.touch()
