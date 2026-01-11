# FoodInsight Local Backend

FastAPI backend with SQLite for local inventory storage and device administration.

## Features

- **SQLite Storage**: All data persisted locally, no cloud dependencies
- **Inventory API**: REST endpoints for inventory CRUD
- **Admin API**: Device configuration, user management, audit logs
- **HTTP Basic Auth**: Role-based access control for admin endpoints
- **Health Checks**: `/health` and `/ready` endpoints for monitoring

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI 0.115+ |
| Runtime | Python 3.11+ |
| Database | SQLite + SQLAlchemy 2.0 |
| Auth | HTTP Basic (admin endpoints only) |
| Package Manager | uv (recommended) or pip |

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

The database is automatically initialized on first startup with:
- Default configuration values
- Default admin user (`admin` / `admin`)

## Environment Variables

Create `.env` file (optional - defaults work for local development):

```bash
# Environment
ENVIRONMENT=development

# Database path (default: ./data/foodinsight.db)
DATABASE_PATH=./data/foodinsight.db

# Device identification
DEVICE_ID=foodinsight-001
DEVICE_NAME=FoodInsight Device

# CORS origins (for PWA)
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:8080"]
```

## API Endpoints

### Public Endpoints (No Auth Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /health` | GET | Basic health check |
| `GET /ready` | GET | Readiness check (includes DB status) |
| `GET /info` | GET | Device information |
| `GET /inventory` | GET | Current inventory state |
| `GET /inventory/item/{name}` | GET | Single item by name |
| `GET /inventory/events` | GET | Recent detection events |
| `POST /inventory/update` | POST | Push inventory update (from detection) |
| `POST /inventory/event` | POST | Log detection event |

### Admin Endpoints (HTTP Basic Auth Required)

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `GET /admin/status` | GET | viewer+ | Device status |
| `GET /admin/config` | GET | viewer+ | All configuration |
| `PUT /admin/config` | PUT | admin | Update configuration |
| `GET /admin/detection/status` | GET | viewer+ | Detection pipeline status |
| `POST /admin/detection/start` | POST | operator+ | Start detection |
| `POST /admin/detection/stop` | POST | operator+ | Stop detection |
| `GET /admin/users` | GET | admin | List users |
| `POST /admin/users` | POST | admin | Create user |
| `DELETE /admin/users/{id}` | DELETE | admin | Delete user |
| `GET /admin/alerts` | GET | viewer+ | List alert rules |
| `POST /admin/alerts` | POST | admin | Create alert rule |
| `GET /admin/events` | GET | viewer+ | Detection events |
| `GET /admin/audit` | GET | admin | Audit logs |
| `POST /admin/system/reboot` | POST | admin | Schedule reboot |
| `POST /admin/system/shutdown` | POST | admin | Schedule shutdown |

### Role Hierarchy

| Role | Permissions |
|------|-------------|
| `viewer` | Read-only access to status and inventory |
| `operator` | Viewer + start/stop detection |
| `admin` | Full access including user management |

## API Documentation (OpenAPI)

The API includes built-in OpenAPI documentation with multiple access methods:

### Interactive Documentation

| URL | Description |
|-----|-------------|
| `/docs` | Swagger UI - Interactive API explorer |
| `/redoc` | ReDoc - Alternative documentation viewer |

### Schema Export

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /openapi.json` | GET | Download OpenAPI 3.0 schema as JSON |
| `GET /openapi.yaml` | GET | Download OpenAPI 3.0 schema as YAML |
| `POST /openapi/export` | POST | Export schema to `server/openapi.json` file |

### Usage Examples

```bash
# View interactive docs
open http://localhost:8000/docs

# Download JSON schema
curl http://localhost:8000/openapi.json > openapi.json

# Download YAML schema (requires PyYAML)
curl http://localhost:8000/openapi.yaml > openapi.yaml

# Export to file on server
curl -X POST http://localhost:8000/openapi/export
```

### Import into API Tools

The exported schema can be imported into:
- **Postman** - Import OpenAPI JSON for collection generation
- **Insomnia** - Import for request building
- **Bruno** - Import for offline API testing
- **Stoplight** - Import for documentation hosting

## Database Schema

Six tables stored in SQLite:

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ inventory_items │  │ detection_events│  │     config      │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ id              │  │ id              │  │ id              │
│ item_name       │  │ event_type      │  │ key (unique)    │
│ display_name    │  │ item_name       │  │ value (JSON)    │
│ count           │  │ count_before    │  │ description     │
│ max_capacity    │  │ count_after     │  │ updated_at      │
│ confidence      │  │ confidence      │  └─────────────────┘
│ last_updated    │  │ details (JSON)  │
└─────────────────┘  │ created_at      │
                     └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  admin_users    │  │  alert_rules    │  │   audit_log     │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ id              │  │ id              │  │ id              │
│ username        │  │ name            │  │ username        │
│ password_hash   │  │ alert_type      │  │ user_id         │
│ role            │  │ item_name       │  │ action          │
│ display_name    │  │ threshold       │  │ resource        │
│ email           │  │ is_enabled      │  │ details (JSON)  │
│ is_active       │  │ created_at      │  │ ip_address      │
│ last_login      │  └─────────────────┘  │ created_at      │
│ created_at      │                       └─────────────────┘
└─────────────────┘
```

## Project Structure

```
server/
├── app/
│   ├── __init__.py           # Version
│   ├── main.py               # FastAPI entry point
│   ├── config.py             # Pydantic settings
│   ├── database.py           # SQLAlchemy engine & session
│   ├── db/
│   │   ├── __init__.py
│   │   └── models.py         # SQLAlchemy ORM models
│   ├── routers/
│   │   ├── health.py         # Health endpoints
│   │   ├── inventory.py      # Inventory CRUD
│   │   └── admin.py          # Admin API (authenticated)
│   └── services/
│       └── sqlite.py         # SQLite service layer
├── scripts/
│   └── init_db.py            # Database initialization
├── tests/
│   └── test_health.py        # Unit tests
├── data/                     # Database files (gitignored)
│   └── foodinsight.db
├── pyproject.toml            # Dependencies
└── .env                      # Environment config
```

## Default Configuration

On first startup, these configuration values are created:

| Key | Default Value |
|-----|---------------|
| `device.name` | FoodInsight Device |
| `device.location` | Break Room |
| `detection.model` | yolo11s-snacks.hef |
| `detection.confidence_threshold` | 0.5 |
| `detection.interval_ms` | 100 |
| `detection.motion_enabled` | true |
| `detection.motion_threshold` | 0.02 |
| `alerts.low_stock_threshold` | 3 |
| `alerts.email_enabled` | false |
| `privacy.mode` | inventory_only |
| `privacy.blur_strength` | 51 |
| `system.timezone` | UTC |
| `system.log_retention_days` | 90 |

## Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app

# Test specific endpoint
curl http://localhost:8000/health
curl http://localhost:8000/inventory
curl -u admin:admin http://localhost:8000/admin/status
```

## Example API Calls

### Get Inventory

```bash
curl http://localhost:8000/inventory
```

Response:
```json
{
  "device_id": "foodinsight-001",
  "location": "Break Room",
  "items": [
    {
      "id": 1,
      "item_name": "chips",
      "display_name": "Chips",
      "count": 5,
      "confidence": 0.95,
      "last_updated": "2026-01-11T18:49:19"
    }
  ],
  "last_updated": "2026-01-11T18:49:19"
}
```

### Push Inventory Update

```bash
curl -X POST http://localhost:8000/inventory/update \
  -H "Content-Type: application/json" \
  -d '{
    "items": {
      "chips": {"count": 5, "confidence": 0.95},
      "cookies": {"count": 3, "confidence": 0.88}
    }
  }'
```

### Admin Status (with auth)

```bash
curl -u admin:admin http://localhost:8000/admin/status
```

Response:
```json
{
  "device_id": "foodinsight-001",
  "device_name": "FoodInsight Device",
  "location": "Break Room",
  "platform": "Linux",
  "python_version": "3.11.0",
  "load_average": [0.5, 0.3, 0.2],
  "environment": "production"
}
```

## Security Notes

- **Password Hashing**: SHA-256 with random salt (no external dependencies)
- **Local Trust Model**: Inventory endpoints have no auth (device-internal communication)
- **Admin Auth**: HTTP Basic authentication with role-based access control
- **Audit Logging**: All admin actions logged with IP address and timestamp

## Related

- [FoodInsight Main](../README.md) - Project overview
- [FoodInsight PWA](../app/README.md) - Consumer frontend
