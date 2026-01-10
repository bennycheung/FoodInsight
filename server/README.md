# FoodInsight Cloud Backend

FastAPI backend for receiving inventory updates from edge devices and serving data to the consumer PWA.

## Features

- **Inventory API**: REST endpoints for inventory CRUD
- **Mock Mode**: Local development without Firestore
- **Bearer Auth**: Token-based authentication for edge devices
- **Health Check**: `/health` endpoint for monitoring
- **CORS**: Configured for PWA cross-origin requests

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI 0.115+ |
| Runtime | Python 3.11+ |
| Database | Firestore (production) / Mock (development) |
| Auth | Bearer Token |
| Package Manager | uv |

## Quick Start

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Environment Variables

Create `.env` file:

```bash
# Environment (development uses mock data)
ENVIRONMENT=development

# Google Cloud Project (production only)
GOOGLE_CLOUD_PROJECT=your-project-id

# CORS origins
ALLOWED_ORIGINS=["http://localhost:5173","https://foodinsight.pages.dev"]
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /health` | GET | None | Health check |
| `GET /inventory/{machine_id}` | GET | None | Get current inventory |
| `POST /inventory/update` | POST | Bearer | Push inventory update (production) |

## Project Structure

```
server/
├── app/
│   ├── __init__.py           # Version
│   ├── main.py               # FastAPI entry point
│   ├── config.py             # Pydantic settings
│   ├── models/
│   │   └── inventory.py      # Pydantic models
│   ├── routers/
│   │   ├── health.py         # Health endpoint
│   │   ├── inventory.py      # Production inventory (Firestore)
│   │   └── mock.py           # Mock inventory (development)
│   ├── services/
│   │   └── firestore.py      # Firestore client
│   └── auth/
│       └── token.py          # Bearer token verification
├── tests/
│   └── test_health.py        # Unit tests
├── scripts/
│   └── generate_token.py     # Generate API tokens
├── pyproject.toml            # Dependencies
├── Dockerfile                # Container image
└── .env                      # Environment config
```

## Development vs Production

The server automatically selects the router based on `ENVIRONMENT`:

- **development**: Uses `mock.py` router with hardcoded sample data
- **production**: Uses `inventory.py` router with Firestore

```python
# app/main.py
if settings.environment == "development":
    app.include_router(mock.router)
else:
    app.include_router(inventory.router)
```

## Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app
```

## Mock Data

In development mode, the API returns this sample inventory:

```json
{
  "machine_id": "breakroom-1",
  "location": "Break Room",
  "items": {
    "chips_bag": {"count": 5, "confidence": 0.92},
    "candy_bar": {"count": 3, "confidence": 0.88},
    "soda_can": {"count": 8, "confidence": 0.95},
    "granola_bar": {"count": 0, "confidence": 1.0},
    "water_bottle": {"count": 12, "confidence": 0.91},
    "cookies_pack": {"count": 2, "confidence": 0.87}
  }
}
```

## Deployment

Deploy to Google Cloud Run:

```bash
gcloud run deploy foodinsight-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=your-project"
```

## Token Generation

Generate bearer tokens for edge devices:

```bash
python scripts/generate_token.py
```

Tokens are SHA-256 hashed before storage in Firestore.

## Related

- [FoodInsight PWA](../app/README.md) - Consumer frontend
- [FoodInsight Edge](../README.md) - Edge detection device
