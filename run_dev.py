#!/usr/bin/env python3
"""Development runner for testing FoodInsight on Mac/Linux desktop.

This script adjusts paths and settings for local development testing.
"""

import asyncio
import logging
import os
import sys
import threading
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Override config paths for development
os.environ["FOODINSIGHT_CONFIG_PATH"] = str(PROJECT_ROOT / "dev_config.json")
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


def patch_config_paths():
    """Patch config module to use dev paths."""
    from config import settings

    # Override paths
    settings.CONFIG_PATH = PROJECT_ROOT / "dev_config.json"
    settings.DEFAULT_MODEL_PATH = str(PROJECT_ROOT / "models" / "yolo11n_ncnn_model")


def main():
    """Run FoodInsight in development mode."""
    logger.info("=" * 60)
    logger.info("FoodInsight Development Mode")
    logger.info("=" * 60)

    patch_config_paths()

    from admin import create_app, update_frame, update_status
    from api import CloudAPIClient
    from config import Settings
    from detection import DetectionService

    # Create dev settings
    # Camera index: 0 = first camera (often iPhone), 1 = second (often built-in webcam)
    # Change this to switch cameras on Mac
    camera_index = int(os.environ.get("CAMERA_INDEX", "1"))  # Default to built-in webcam

    settings = Settings(
        machine_id="breakroom-1",  # Match mock data machine_id
        model_path=str(PROJECT_ROOT / "models" / "yolo11n_ncnn_model"),
        input_size=640,
        process_every_n_frames=1,
        motion_threshold=0.02,
        admin_port=8080,  # Use non-privileged port
        api_url="http://localhost:8000",  # Local backend for testing
        api_key="dev-token",  # Dummy token for dev (mock backend doesn't validate)
        camera_index=camera_index,  # 0=iPhone, 1=built-in webcam (typically)
        # Filter to only report these classes (empty list = all classes)
        # Default food-related COCO classes for snack detection
        allowed_classes=[
            "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl",
            "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
            "hot dog", "pizza", "donut", "cake",
        ],
    )

    # Save dev config
    import json
    config_path = PROJECT_ROOT / "dev_config.json"
    config_path.write_text(json.dumps({
        "machine_id": settings.machine_id,
        "model_path": settings.model_path,
        "input_size": settings.input_size,
        "admin_port": settings.admin_port,
        "camera_index": settings.camera_index,
        "allowed_classes": settings.allowed_classes,
    }, indent=2))

    logger.info(f"Platform: macOS development mode")
    logger.info(f"Config: {config_path}")
    logger.info(f"Camera index: {camera_index} (set CAMERA_INDEX=0 for iPhone, =1 for built-in)")
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
    api_client = CloudAPIClient(
        base_url=settings.api_url,
        api_key=settings.api_key,
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
