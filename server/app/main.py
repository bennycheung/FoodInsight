"""FoodInsight API - FastAPI entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.routers import health, inventory, mock


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="FoodInsight API",
    description="Smart snack inventory monitoring API",
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

# Use mock router for local development (no Firestore needed)
if settings.environment == "development":
    app.include_router(mock.router)
else:
    app.include_router(inventory.router)
