#!/usr/bin/env python3
"""FoodInsight Edge Device - Main Entry Point.

This module orchestrates the detection service and admin portal,
running them concurrently with shared state.
"""

import asyncio
import logging
import signal
import sys
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from admin import create_app, update_frame, update_status
from api import LocalAPIClient
from config import get_settings
from detection import DetectionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/foodinsight/edge.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


class FoodInsightEdge:
    """Main application orchestrator."""

    def __init__(self):
        self.settings = get_settings()
        self.detection_service: DetectionService = None
        self.api_client: LocalAPIClient = None
        self.flask_app = None
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start all services."""
        logger.info("Starting FoodInsight Edge...")
        logger.info(f"Machine ID: {self.settings.machine_id}")
        logger.info(f"Platform config: input_size={self.settings.input_size}, "
                   f"skip_frames={self.settings.process_every_n_frames}")

        # Initialize local API client (connects to FastAPI backend on same device)
        self.api_client = LocalAPIClient(
            base_url=self.settings.api_url,
        )

        # Initialize detection service with callbacks
        self.detection_service = DetectionService(
            settings=self.settings,
            on_frame=update_frame,
            on_status=update_status,
            on_delta=self._handle_delta,
        )

        # Create Flask app
        self.flask_app = create_app()

        # Start Flask in a separate thread
        flask_thread = threading.Thread(
            target=self._run_flask,
            daemon=True,
        )
        flask_thread.start()
        logger.info(f"Admin portal started on http://0.0.0.0:{self.settings.admin_port}")

        # Run detection service
        try:
            await self.detection_service.start()
        except asyncio.CancelledError:
            logger.info("Detection service cancelled")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop all services."""
        logger.info("Stopping FoodInsight Edge...")

        if self.detection_service:
            await self.detection_service.stop()

        if self.api_client:
            await self.api_client.close()

        logger.info("FoodInsight Edge stopped")

    def _run_flask(self) -> None:
        """Run Flask app in a thread."""
        # Suppress Flask's default logging
        import logging as flask_logging
        flask_logging.getLogger("werkzeug").setLevel(flask_logging.WARNING)

        self.flask_app.run(
            host=self.settings.admin_host,
            port=self.settings.admin_port,
            threaded=True,
            use_reloader=False,
        )

    def _handle_delta(self, delta) -> None:
        """Handle inventory delta (push to cloud)."""
        # Run async push in event loop
        asyncio.create_task(self._push_delta(delta))

    async def _push_delta(self, delta) -> None:
        """Push delta to cloud API."""
        if self.api_client:
            await self.api_client.push_delta(delta)


def setup_signal_handlers(app: FoodInsightEdge, loop: asyncio.AbstractEventLoop) -> None:
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(sig):
        logger.info(f"Received signal {sig}")
        loop.create_task(app.stop())
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))


def main() -> None:
    """Main entry point."""
    # Ensure log directory exists
    log_dir = Path("/var/log/foodinsight")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create application
    app = FoodInsightEdge()

    # Run
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Set up signal handlers
        setup_signal_handlers(app, loop)

        # Run the application
        loop.run_until_complete(app.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
