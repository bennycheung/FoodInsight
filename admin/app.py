"""Flask admin portal for FoodInsight edge device.

Provides local dashboard with live video feed and status display.
Proxies configuration and admin operations to the local FastAPI backend.
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import httpx
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

# Configuration - use local path for development, /opt for production
_project_root = Path(__file__).parent.parent
if (_project_root / "run_dev.py").exists():
    # Development mode - use local config
    CONFIG_PATH = _project_root / "dev_config.json"
else:
    # Production mode - use system path
    CONFIG_PATH = Path("/opt/foodinsight/config.json")

API_BASE_URL = "http://localhost:8000"  # Local FastAPI backend


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

    # ----- Status Card Partial Endpoints -----

    @app.route("/status-cards/detection")
    def detection_card():
        """HTMX partial for detection status card."""
        fps = _status_data.get("fps", 0.0)
        status = _status_data.get("status", "unknown")
        frame_count = _status_data.get("frame_count", 0)

        badge_class = "success" if status == "running" else "error"
        badge_icon = "✓" if status == "running" else "✕"

        html = f'''
            <div class="status-card__header">
                <div class="status-card__icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--snack-purple);">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                </div>
                <div class="status-card__content">
                    <h3 class="status-card__title">Detection</h3>
                </div>
            </div>
            <div class="status-card__value">{fps:.1f} FPS</div>
            <div class="status-card__meta">
                <div class="status-badge status-badge--{badge_class}">
                    <span class="status-badge__icon">{badge_icon}</span>
                    <span>{status.capitalize()}</span>
                </div>
                <div style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 4px;">
                    {frame_count} frames processed
                </div>
            </div>
        '''
        return html

    @app.route("/status-cards/inventory")
    def inventory_card():
        """HTMX partial for inventory summary card."""
        inventory = _status_data.get("inventory", {})
        total_items = sum(inventory.values())
        in_stock = sum(1 for count in inventory.values() if count > 0)
        empty = len(inventory) - in_stock

        html = f'''
            <div class="status-card__header">
                <div class="status-card__icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--fresh-green);">
                        <path d="M20 7h-4V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v3H4a1 1 0 0 0-1 1v11a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8a1 1 0 0 0-1-1zM10 4h4v3h-4V4zm10 15H4V9h16v10z"></path>
                    </svg>
                </div>
                <div class="status-card__content">
                    <h3 class="status-card__title">Inventory</h3>
                </div>
            </div>
            <div class="status-card__value">{total_items} Items</div>
            <div class="inventory-breakdown">
                <div class="inventory-breakdown__item">
                    <span class="inventory-breakdown__label">In Stock</span>
                    <span class="inventory-breakdown__value inventory-breakdown__value--in-stock">{in_stock}</span>
                </div>
                <div class="inventory-breakdown__item">
                    <span class="inventory-breakdown__label">Empty</span>
                    <span class="inventory-breakdown__value inventory-breakdown__value--empty">{empty}</span>
                </div>
            </div>
        '''
        return html

    @app.route("/status-cards/health")
    def health_card():
        """HTMX partial for system health card."""
        motion_active = _status_data.get("motion_active", False)
        last_detection = _status_data.get("last_detection", "Never")

        motion_dot_class = "health-indicator__dot--warning" if motion_active else ""
        motion_status = "Active" if motion_active else "Idle"

        html = f'''
            <div class="status-card__header">
                <div class="status-card__icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--info-blue);">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                    </svg>
                </div>
                <div class="status-card__content">
                    <h3 class="status-card__title">System Health</h3>
                </div>
            </div>
            <div class="status-card__value">Online</div>
            <div class="health-indicators">
                <div class="health-indicator">
                    <span class="health-indicator__label">Motion</span>
                    <div class="health-indicator__status">
                        <div class="health-indicator__dot {motion_dot_class}"></div>
                        <span class="health-indicator__value">{motion_status}</span>
                    </div>
                </div>
                <div class="health-indicator">
                    <span class="health-indicator__label">Last Detection</span>
                    <span class="health-indicator__value">{last_detection}</span>
                </div>
            </div>
        '''
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

    # ----- Backend API Proxy Routes -----

    @app.route("/api/device-info")
    def device_info():
        """Get device info from backend (HTMX partial)."""
        result = api_get("/info")
        if result:
            # Return HTML partial for HTMX
            html = '<dl class="device-info">'
            html += f'<dt>Device ID</dt><dd>{result.get("device_id", "N/A")}</dd>'
            html += f'<dt>Device Name</dt><dd>{result.get("device_name", "N/A")}</dd>'
            html += f'<dt>Location</dt><dd>{result.get("location", "N/A")}</dd>'
            html += f'<dt>Version</dt><dd>{result.get("version", "N/A")}</dd>'
            html += f'<dt>Environment</dt><dd>{result.get("environment", "N/A")}</dd>'
            html += '</dl>'
            return html
        return '<p class="error">Backend unavailable</p>'

    @app.route("/api/backend-status")
    def backend_status():
        """Get backend health status (HTMX partial)."""
        result = api_get("/ready")
        if result and result.get("status") == "ready":
            return '<div class="status-indicator backend"></div><span>Backend: online</span>'
        return '<div class="status-indicator offline"></div><span>Backend: offline</span>'

    @app.route("/api/inventory-data")
    def inventory_data():
        """Get inventory from backend (HTMX partial)."""
        result = api_get("/inventory")
        if result:
            items = result.get("items", [])
            if not items:
                return '<p>No items in database</p>'
            html = '<div class="inventory">'
            for item in items:
                count = item.get("count", 0)
                name = item.get("display_name", item.get("item_name", "Unknown"))
                status_class = "in-stock" if count > 0 else "out-of-stock"
                html += f'<div class="item {status_class}">'
                html += f'<span class="count">{count}</span>'
                html += f'<span class="name">{name}</span>'
                html += '</div>'
            html += '</div>'
            last_updated = result.get("last_updated", "Never")
            html += f'<p style="font-size: 0.8rem; opacity: 0.6; margin-top: 10px;">Last updated: {last_updated}</p>'
            return html
        # Fall back to in-memory status
        inventory = _status_data.get("inventory", {})
        if not inventory:
            return '<p>No items detected</p>'
        html = '<div class="inventory">'
        for item, count in inventory.items():
            status_class = "in-stock" if count > 0 else "out-of-stock"
            html += f'<div class="item {status_class}">'
            html += f'<span class="count">{count}</span>'
            html += f'<span class="name">{item}</span>'
            html += '</div>'
        html += '</div>'
        return html

    @app.route("/api/events")
    def get_events():
        """Get recent events from backend (HTMX partial)."""
        limit = request.args.get("limit", 50, type=int)
        item_name = request.args.get("item_name")
        event_type = request.args.get("event_type")

        params = f"?limit={limit}"
        if item_name:
            params += f"&item_name={item_name}"
        if event_type:
            params += f"&event_type={event_type}"

        result = api_get(f"/inventory/events{params}")
        if result:
            events = result.get("events", [])
            if not events:
                return '<p>No recent events</p>'
            html = ''
            for event in events:
                event_type = event.get("event_type", "unknown")
                item_name = event.get("item_name", "Unknown")
                count_before = event.get("count_before", 0)
                count_after = event.get("count_after", 0)
                created_at = event.get("created_at", "")

                # Format event type for display
                event_class = "added" if event_type == "item_added" else "taken" if event_type == "item_removed" else ""
                action = "added" if event_type == "item_added" else "removed" if event_type == "item_removed" else event_type

                html += f'<div class="event-item {event_class}">'
                html += f'<strong>{item_name}</strong> {action} ({count_before} → {count_after})'
                html += f'<div class="event-time">{created_at}</div>'
                html += '</div>'
            return html
        return '<p>Unable to load events</p>'

    @app.route("/api/admin/status")
    def admin_status():
        """Get admin status (requires auth header forwarding)."""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            import base64
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = decoded.split(":", 1)
                result = api_get("/admin/status", auth=(username, password))
                if result:
                    return jsonify(result)
            except Exception:
                pass
        return jsonify({"error": "Unauthorized"}), 401

    @app.route("/api/admin/config")
    def admin_config():
        """Get admin config (requires auth header forwarding)."""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            import base64
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = decoded.split(":", 1)
                result = api_get("/admin/config", auth=(username, password))
                if result:
                    return jsonify(result)
            except Exception:
                pass
        return jsonify({"error": "Unauthorized"}), 401

    @app.route("/api/admin/detection/start", methods=["POST"])
    def start_detection():
        """Start detection via backend."""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            import base64
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = decoded.split(":", 1)
                result = api_post("/admin/detection/start", auth=(username, password))
                if result:
                    return jsonify(result)
            except Exception:
                pass
        return jsonify({"error": "Unauthorized"}), 401

    @app.route("/api/admin/detection/stop", methods=["POST"])
    def stop_detection():
        """Stop detection via backend."""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            import base64
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = decoded.split(":", 1)
                result = api_post("/admin/detection/stop", auth=(username, password))
                if result:
                    return jsonify(result)
            except Exception:
                pass
        return jsonify({"error": "Unauthorized"}), 401


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
    """Load configuration from file (legacy) or backend API."""
    # Try backend first
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f"{API_BASE_URL}/admin/config")
            if response.status_code == 401:
                # Need auth - fall back to file
                pass
            elif response.is_success:
                return response.json()
    except Exception as e:
        logger.debug(f"Backend config fetch failed: {e}")

    # Fall back to local file
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


# ----- Backend API Helpers -----


def api_get(path: str, auth: tuple = None) -> Optional[Dict]:
    """Make GET request to backend API."""
    try:
        with httpx.Client(timeout=5.0) as client:
            kwargs = {}
            if auth:
                kwargs["auth"] = auth
            response = client.get(f"{API_BASE_URL}{path}", **kwargs)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"API GET {path} failed: {e}")
        return None


def api_post(path: str, data: dict = None, auth: tuple = None) -> Optional[Dict]:
    """Make POST request to backend API."""
    try:
        with httpx.Client(timeout=5.0) as client:
            kwargs = {"json": data} if data else {}
            if auth:
                kwargs["auth"] = auth
            response = client.post(f"{API_BASE_URL}{path}", **kwargs)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"API POST {path} failed: {e}")
        return None


def api_put(path: str, data: dict, auth: tuple = None) -> Optional[Dict]:
    """Make PUT request to backend API."""
    try:
        with httpx.Client(timeout=5.0) as client:
            kwargs = {"json": data}
            if auth:
                kwargs["auth"] = auth
            response = client.put(f"{API_BASE_URL}{path}", **kwargs)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"API PUT {path} failed: {e}")
        return None
