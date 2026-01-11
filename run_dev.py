#!/usr/bin/env python3
"""Development runner for testing FoodInsight on Mac/Linux desktop.

This script adjusts paths and settings for local development testing.

Usage:
    python run_dev.py                        # Uses dev_config.json (default)
    python run_dev.py --config custom.json   # Uses custom config file
    python run_dev.py -c prod_config.json    # Short form
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import threading
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run FoodInsight in development mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_dev.py                        # Uses dev_config.json
    python run_dev.py --config custom.json   # Uses custom config file
    python run_dev.py -c prod_config.json    # Short form
        """,
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="dev_config.json",
        help="Path to configuration file (default: dev_config.json)",
    )
    return parser.parse_args()


def load_config(config_path: Path) -> dict:
    """Load configuration from JSON file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        return json.load(f)


# Parse args early to get config path
args = parse_args()
config_path = PROJECT_ROOT / args.config if not Path(args.config).is_absolute() else Path(args.config)

# Override config paths for development
os.environ["FOODINSIGHT_CONFIG_PATH"] = str(config_path)
os.environ["FOODINSIGHT_LOG_DIR"] = str(PROJECT_ROOT / "logs")

# Create logs directory
(PROJECT_ROOT / "logs").mkdir(exist_ok=True)

# Configure logging to console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "logs" / "dev.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


def patch_config_paths(config_file: Path):
    """Patch config module to use dev paths."""
    from config import settings

    # Override paths
    settings.CONFIG_PATH = config_file
    settings.DEFAULT_MODEL_PATH = str(PROJECT_ROOT / "models" / "yolo11n_ncnn_model")


def main():
    """Run FoodInsight in development mode."""
    logger.info("=" * 60)
    logger.info("FoodInsight Development Mode")
    logger.info("=" * 60)

    patch_config_paths(config_path)

    from admin import create_app, update_frame, update_status
    from api import LocalAPIClient
    from config import Settings
    from detection import DetectionService

    # Load configuration from file
    logger.info(f"Loading config from: {config_path}")
    config = load_config(config_path)

    # Camera index: env var overrides config file
    # 0 = first camera (often iPhone), 1 = second (often built-in webcam)
    camera_index = int(os.environ.get("CAMERA_INDEX", config.get("camera_index", 1)))

    # Create settings from config file
    settings = Settings(
        machine_id=config.get("machine_id", "breakroom-1"),
        model_path=config.get("model_path", str(PROJECT_ROOT / "models" / "yolo11n_ncnn_model")),
        input_size=config.get("input_size", 640),
        process_every_n_frames=config.get("process_every_n_frames", 1),
        motion_threshold=config.get("motion_threshold", 0.008),
        admin_port=config.get("admin_port", 8080),
        api_url=config.get("api_url", "http://localhost:8000"),
        camera_index=camera_index,
        allowed_classes=config.get("allowed_classes", []),
    )

    logger.info(f"Platform: macOS development mode")
    logger.info(f"Config: {config_path}")
    logger.info(f"Camera index: {camera_index} (set CAMERA_INDEX=0 for iPhone, =1 for built-in)")
    logger.info(f"Allowed classes: {len(settings.allowed_classes)} classes configured")
    logger.info(f"Admin portal: http://localhost:{settings.admin_port}")

    # Check for model
    model_path = Path(settings.model_path)
    if not model_path.exists():
        logger.warning(f"Model not found at {model_path}")
        logger.warning("Detection will run in mock mode (no actual detections)")
        logger.info("")
        logger.info("To enable real detection, export the model:")
        logger.info("  pip install ultralytics")
        logger.info("  yolo export model=yolo11n.pt format=ncnn")
        logger.info(f"  mv yolo11n_ncnn_model {model_path}")
        logger.info("")

    # Check for camera
    import cv2
    cap = cv2.VideoCapture(camera_index)
    if cap.isOpened():
        logger.info(f"Camera: Found at index {camera_index} (OpenCV VideoCapture)")
        cap.release()
    else:
        logger.warning(f"Camera: Not found at index {camera_index}")
        logger.warning("Try CAMERA_INDEX=0 or CAMERA_INDEX=1 to switch cameras")
        logger.warning("Grant camera permission in System Preferences > Privacy & Security > Camera")

    # Create Flask app
    flask_app = create_app()

    # Create API client for pushing to backend
    api_client = LocalAPIClient(
        base_url=settings.api_url,
    )

    async def push_delta(delta):
        """Push inventory delta to backend."""
        logger.info(f"Delta: {len(delta.events)} events, pushing to backend...")
        success = await api_client.push_delta(delta)
        if success:
            logger.info("Delta pushed successfully")
        else:
            logger.warning("Failed to push delta")

    # Create detection service
    detection_service = DetectionService(
        settings=settings,
        on_frame=update_frame,
        on_status=update_status,
        on_delta=lambda d: asyncio.create_task(push_delta(d)),
    )

    # Start Flask in background thread
    def run_flask():
        import logging as flask_logging
        flask_logging.getLogger("werkzeug").setLevel(flask_logging.WARNING)
        flask_app.run(
            host="127.0.0.1",
            port=settings.admin_port,
            threaded=True,
            use_reloader=False,
        )

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Admin portal running at: http://localhost:{settings.admin_port}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    logger.info("")

    # Run detection service
    try:
        asyncio.run(detection_service.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Error: {e}")


if __name__ == "__main__":
    main()
