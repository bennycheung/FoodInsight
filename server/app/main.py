"""FoodInsight API - FastAPI entry point."""

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, JSONResponse

from app import __version__
from app.config import settings
from app.database import init_db, SessionLocal
from app.routers import admin, health, inventory
from app.services.sqlite import SQLiteService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Initializing database...")
    init_db()

    # Initialize default data if needed
    db = SessionLocal()
    try:
        service = SQLiteService(db)
        service.init_default_config()
        service.init_default_admin()
        logger.info("Database initialized successfully")
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="FoodInsight API",
    description="Smart snack inventory monitoring API - Local SQLite Edition",
    version=__version__,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(inventory.router)
app.include_router(admin.router)


def custom_openapi():
    """Generate custom OpenAPI schema with enhanced metadata."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="FoodInsight API",
        version=__version__,
        description="""
## Smart Snack Inventory Monitoring API

Local-first API for managing snack inventory on FoodInsight edge devices.

### Architecture

- **Local SQLite Database**: All data stored locally, no cloud dependencies
- **Role-Based Access**: Public inventory endpoints, authenticated admin endpoints
- **Real-Time Detection**: Receives inventory updates from edge detection pipeline

### Authentication

Admin endpoints require HTTP Basic authentication:
- `viewer`: Read-only access to status and configuration
- `operator`: Can start/stop detection pipeline
- `admin`: Full access including user management

### Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin | admin |

**Important**: Change default credentials after first login.
        """,
        routes=app.routes,
        tags=[
            {"name": "health", "description": "Health check and readiness endpoints"},
            {"name": "inventory", "description": "Inventory management endpoints (public)"},
            {"name": "admin", "description": "Administration endpoints (authenticated)"},
        ],
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    openapi_schema["info"]["contact"] = {
        "name": "FoodInsight Support",
        "email": "support@foodinsight.local"
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    """Export OpenAPI schema as JSON."""
    return JSONResponse(content=app.openapi())


@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    """Export OpenAPI schema as YAML."""
    try:
        import yaml
        from fastapi.responses import Response
        schema = app.openapi()
        yaml_content = yaml.dump(schema, default_flow_style=False, sort_keys=False, allow_unicode=True)
        return Response(content=yaml_content, media_type="application/x-yaml")
    except ImportError:
        # Fallback to JSON if PyYAML not installed
        return JSONResponse(
            content=app.openapi(),
            media_type="application/json"
        )


@app.post("/openapi/export", include_in_schema=False)
async def export_openapi_schema():
    """Export OpenAPI schema to file in the server directory."""
    schema = app.openapi()
    output_path = Path(__file__).parent.parent / "openapi.json"
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    return {"message": f"Schema exported to {output_path}", "path": str(output_path)}
