# Epic 2: Cloud Backend + Consumer App - User Stories

**Epic Goal:** Inventory data flows to cloud, employees view via PWA

**PRD Reference:** [[FoodInsight PRD]]
**Architecture Reference:** [[FoodInsight Solution Architecture]]

**Epic Acceptance Criteria:**
- [ ] Edge device pushes updates within 2 seconds of detection
- [ ] PWA loads in <2 seconds
- [ ] PWA installable on mobile devices
- [ ] Inventory display matches edge device state

---

## E2-S1: Create FastAPI Backend with Health Endpoint

### User Story

**As a** cloud infrastructure,
**I want** a FastAPI server deployed to Cloud Run with basic health endpoints,
**So that** I have a foundation for the inventory API.

### Acceptance Criteria

```gherkin
Feature: FastAPI Backend Scaffold

Scenario: Health endpoint returns ok
  Given the FastAPI server is running
  When I GET /health
  Then I receive status 200
  And the response contains {"status": "ok", "version": "1.0.0"}

Scenario: OpenAPI documentation is available
  Given the FastAPI server is running
  When I navigate to /docs
  Then Swagger UI loads successfully
  And all endpoints are documented

Scenario: CORS is configured for PWA
  Given the FastAPI server is running
  When the PWA makes a request from https://foodinsight.pages.dev
  Then the request succeeds with proper CORS headers
  And Access-Control-Allow-Origin includes the PWA domain

Scenario: Server starts in under 5 seconds
  Given a cold start on Cloud Run
  When a request triggers container startup
  Then the server responds within 5 seconds

Scenario: Environment configuration works
  Given environment variables are set
  When the server starts
  Then it reads GOOGLE_CLOUD_PROJECT from environment
  And it reads ALLOWED_ORIGINS from environment
```

### Technical Notes

**Project Structure:**
```
foodinsight-server/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Pydantic settings
│   └── routers/
│       └── health.py        # Health endpoints
├── tests/
│   └── test_health.py
├── pyproject.toml
├── Dockerfile
└── cloudbuild.yaml
```

**Main Application:**
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import health

app = FastAPI(
    title="FoodInsight API",
    description="Smart snack inventory monitoring API",
    version="1.0.0"
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

@app.on_event("startup")
async def startup():
    # Initialize connections
    pass
```

**Configuration:**
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_cloud_project: str = ""
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "https://foodinsight.pages.dev"
    ]
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

**Health Router:**
```python
# app/routers/health.py
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready")
async def readiness_check():
    # Add dependency checks here (Firestore, etc.)
    return {"status": "ready"}
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY app/ app/

# Install dependencies
RUN uv pip install --system -e .

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**pyproject.toml:**
```toml
[project]
name = "foodinsight-server"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
    "pytest-asyncio>=0.24.0",
]
```

### Definition of Done

- [ ] FastAPI project scaffolded with uv
- [ ] Health endpoint returns 200 with version
- [ ] OpenAPI docs accessible at /docs
- [ ] CORS configured for PWA domain
- [ ] Dockerfile builds successfully
- [ ] Unit tests pass
- [ ] Deployed to Cloud Run (dev environment)

### Dependencies

- **Requires:** GCP project setup
- **Blocked by:** None

### Complexity

**Points:** 2 (Small)
**Risk:** Low - standard FastAPI setup

---

## E2-S2: Implement Firestore Data Model

### User Story

**As a** backend service,
**I want** to store and retrieve inventory data from Firestore,
**So that** inventory state persists and can be queried by the PWA.

### Acceptance Criteria

```gherkin
Feature: Firestore Integration

Scenario: Machine document can be created
  Given a valid machine configuration
  When I call create_machine()
  Then a document is created at companies/{company}/machines/{machine_id}
  And it contains name, location, status, and last_seen fields

Scenario: Inventory can be updated
  Given a machine exists
  When I call update_inventory() with new counts
  Then the inventory document is updated
  And last_updated timestamp is set
  And the operation completes in under 100ms

Scenario: Inventory can be retrieved
  Given inventory exists for machine "breakroom-1"
  When I call get_inventory("breakroom-1")
  Then I receive the current inventory counts
  And I receive the last_updated timestamp

Scenario: Company isolation is enforced
  Given machines exist for company "acme" and "globex"
  When I query inventory for company "acme"
  Then I only receive acme's machines
  And globex data is not accessible

Scenario: Events can be logged
  Given a SNACK_TAKEN event occurs
  When I call log_event() with the event data
  Then the event is stored in the events subcollection
  And it includes timestamp, item, and count fields
```

### Technical Notes

**Firestore Schema:**
```
companies/
└── {company_id}/
    ├── machines/
    │   └── {machine_id}/
    │       ├── name: string
    │       ├── location: string
    │       ├── status: "online" | "offline"
    │       ├── last_seen: timestamp
    │       └── config: {
    │           api_key: string (hashed)
    │         }
    │
    ├── inventory/
    │   └── {machine_id}/
    │       ├── items: {
    │       │   [item_name]: {
    │       │     count: number
    │       │     confidence: number
    │       │     last_updated: timestamp
    │       │   }
    │       │ }
    │       └── last_updated: timestamp
    │
    └── events/
        └── {event_id}/
            ├── type: string
            ├── item: string
            ├── machine_id: string
            ├── timestamp: timestamp
            ├── count_before: number
            └── count_after: number
```

**Firestore Service:**
```python
# app/services/firestore.py
from google.cloud import firestore
from datetime import datetime
from app.models.inventory import InventoryItem, InventoryUpdate, MachineConfig

class FirestoreClient:
    def __init__(self, project_id: str = None):
        self.db = firestore.AsyncClient(project=project_id)

    async def get_machine(self, company: str, machine_id: str) -> dict | None:
        doc = await self.db.collection("companies").document(company) \
            .collection("machines").document(machine_id).get()
        return doc.to_dict() if doc.exists else None

    async def create_machine(
        self,
        company: str,
        machine_id: str,
        config: MachineConfig
    ) -> None:
        await self.db.collection("companies").document(company) \
            .collection("machines").document(machine_id).set({
                "name": config.name,
                "location": config.location,
                "status": "offline",
                "last_seen": None,
                "config": {
                    "api_key_hash": config.api_key_hash
                }
            })

    async def get_inventory(self, company: str, machine_id: str) -> dict | None:
        doc = await self.db.collection("companies").document(company) \
            .collection("inventory").document(machine_id).get()
        return doc.to_dict() if doc.exists else None

    async def update_inventory(
        self,
        company: str,
        machine_id: str,
        items: dict[str, InventoryItem]
    ) -> None:
        now = datetime.utcnow()

        # Update inventory document
        inventory_ref = self.db.collection("companies").document(company) \
            .collection("inventory").document(machine_id)

        inventory_data = {
            "items": {
                name: {
                    "count": item.count,
                    "confidence": item.confidence,
                    "last_updated": now
                }
                for name, item in items.items()
            },
            "last_updated": now
        }
        await inventory_ref.set(inventory_data, merge=True)

        # Update machine last_seen
        machine_ref = self.db.collection("companies").document(company) \
            .collection("machines").document(machine_id)
        await machine_ref.update({
            "status": "online",
            "last_seen": now
        })

    async def log_event(
        self,
        company: str,
        machine_id: str,
        event: dict
    ) -> str:
        events_ref = self.db.collection("companies").document(company) \
            .collection("events")

        doc_ref = await events_ref.add({
            **event,
            "machine_id": machine_id,
            "timestamp": datetime.utcnow()
        })
        return doc_ref.id

    async def get_events(
        self,
        company: str,
        machine_id: str | None = None,
        limit: int = 50
    ) -> list[dict]:
        query = self.db.collection("companies").document(company) \
            .collection("events") \
            .order_by("timestamp", direction=firestore.Query.DESCENDING) \
            .limit(limit)

        if machine_id:
            query = query.where("machine_id", "==", machine_id)

        docs = await query.get()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
```

**Pydantic Models:**
```python
# app/models/inventory.py
from pydantic import BaseModel, Field
from datetime import datetime

class InventoryItem(BaseModel):
    count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)

class MachineConfig(BaseModel):
    name: str
    location: str
    api_key_hash: str

class InventoryResponse(BaseModel):
    machine_id: str
    location: str
    items: dict[str, InventoryItem]
    last_updated: datetime | None
```

### Definition of Done

- [ ] FirestoreClient class implemented
- [ ] CRUD operations for machines
- [ ] CRUD operations for inventory
- [ ] Event logging functionality
- [ ] Company isolation verified
- [ ] Unit tests with Firestore emulator
- [ ] Documentation of schema

### Dependencies

- **Requires:** E2-S1 (FastAPI Scaffold)
- **Blocked by:** GCP Firestore setup

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - standard Firestore patterns

---

## E2-S3: Add Bearer Token Authentication

### User Story

**As a** backend service,
**I want** to authenticate edge devices using Bearer tokens,
**So that** only authorized devices can update inventory.

### Acceptance Criteria

```gherkin
Feature: Bearer Token Authentication

Scenario: Valid token grants access
  Given an edge device with valid API key "sk_test_123"
  And the key is registered for company "acme"
  When I POST /inventory/update with Bearer token "sk_test_123"
  Then the request succeeds with status 200

Scenario: Invalid token is rejected
  Given an invalid API key "sk_invalid"
  When I POST /inventory/update with Bearer token "sk_invalid"
  Then the request fails with status 401
  And the response contains {"detail": "Invalid token"}

Scenario: Missing token is rejected
  Given no Authorization header
  When I POST /inventory/update
  Then the request fails with status 401
  And the response contains {"detail": "Not authenticated"}

Scenario: Token is validated against company
  Given API key "sk_acme_123" is registered for company "acme"
  When I POST /inventory/update for company "globex" with Bearer "sk_acme_123"
  Then the request fails with status 401
  And the response contains {"detail": "Token not valid for this company"}

Scenario: Public endpoints don't require auth
  Given no Authorization header
  When I GET /inventory/breakroom-1
  Then the request succeeds with status 200
  And inventory data is returned
```

### Technical Notes

**Auth Dependency:**
```python
# app/auth/token.py
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.firestore import FirestoreClient
import hashlib

security = HTTPBearer()

def hash_token(token: str) -> str:
    """Hash token for storage comparison."""
    return hashlib.sha256(token.encode()).hexdigest()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    company: str = Query(..., description="Company identifier"),
    db: FirestoreClient = Depends()
) -> dict:
    """Verify Bearer token against company's stored API key."""

    token = credentials.credentials
    token_hash = hash_token(token)

    # Get all machines for company and check token
    machines_ref = db.db.collection("companies").document(company) \
        .collection("machines")
    machines = await machines_ref.get()

    for machine in machines:
        machine_data = machine.to_dict()
        stored_hash = machine_data.get("config", {}).get("api_key_hash")
        if stored_hash and stored_hash == token_hash:
            return {
                "company": company,
                "machine_id": machine.id,
                "machine_name": machine_data.get("name")
            }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )

# Optional auth for public endpoints
async def optional_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
    company: str | None = Query(None),
    db: FirestoreClient = Depends()
) -> dict | None:
    """Optional authentication - returns None if no token provided."""
    if credentials is None:
        return None
    return await verify_token(credentials, company, db)
```

**Protected Endpoint Example:**
```python
# app/routers/inventory.py
from fastapi import APIRouter, Depends
from app.auth.token import verify_token
from app.models.inventory import InventoryUpdate

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.post("/update")
async def update_inventory(
    data: InventoryUpdate,
    auth: dict = Depends(verify_token),
    db: FirestoreClient = Depends()
):
    """Update inventory from edge device (requires auth)."""
    await db.update_inventory(
        company=auth["company"],
        machine_id=auth["machine_id"],
        items=data.items
    )
    return {"status": "ok", "machine_id": auth["machine_id"]}
```

**Public Endpoint Example:**
```python
@router.get("/{machine_id}")
async def get_inventory(
    machine_id: str,
    company: str = Query(...),
    db: FirestoreClient = Depends()
):
    """Get current inventory (public, no auth required)."""
    inventory = await db.get_inventory(company, machine_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Machine not found")
    return inventory
```

**Token Generation (Admin Tool):**
```python
# scripts/generate_token.py
import secrets
import hashlib

def generate_api_key(prefix: str = "sk") -> tuple[str, str]:
    """Generate API key and its hash."""
    token = f"{prefix}_{secrets.token_urlsafe(24)}"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash

# Usage:
# token, hash = generate_api_key("sk_acme")
# Store hash in Firestore, give token to edge device
```

### Definition of Done

- [ ] HTTPBearer security dependency implemented
- [ ] Token verification against Firestore
- [ ] Token hashing for secure storage
- [ ] 401 response for invalid/missing tokens
- [ ] Public endpoints work without auth
- [ ] Token generation script created
- [ ] Unit tests for auth scenarios

### Dependencies

- **Requires:** E2-S2 (Firestore Integration)
- **Blocked by:** None after E2-S2

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - standard auth patterns

---

## E2-S4: Edge Device Pushes Delta Updates

### User Story

**As an** edge device,
**I want** to push inventory delta updates to the cloud backend,
**So that** the cloud has current inventory state for the PWA.

### Acceptance Criteria

```gherkin
Feature: Edge to Cloud Integration

Scenario: Delta update is received and stored
  Given the edge device detects inventory change
  When I POST /inventory/update with delta payload
  Then the inventory is updated in Firestore
  And events are logged
  And the response includes processing time

Scenario: Payload format is validated
  Given an invalid payload (missing required fields)
  When I POST /inventory/update
  Then the request fails with status 422
  And validation errors are returned

Scenario: Machine status is updated
  Given a successful inventory update
  When I check the machine document
  Then status is "online"
  And last_seen is updated to current time

Scenario: Rate limiting prevents abuse
  Given more than 60 requests per minute
  When I send another request
  Then the request fails with status 429
  And the response indicates rate limit exceeded

Scenario: Batch updates are efficient
  Given multiple items changed
  When I send a single update with all changes
  Then all items are updated atomically
  And only one Firestore write occurs
```

### Technical Notes

**Update Endpoint:**
```python
# app/routers/inventory.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth.token import verify_token
from app.services.firestore import FirestoreClient
from app.models.inventory import InventoryUpdate, InventoryEvent
from datetime import datetime
import time

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.post("/update")
async def update_inventory(
    data: InventoryUpdate,
    auth: dict = Depends(verify_token),
    db: FirestoreClient = Depends()
):
    """
    Update inventory from edge device.

    Requires Bearer token authentication.
    Accepts delta updates with current counts and events.
    """
    start_time = time.time()

    company = auth["company"]
    machine_id = auth["machine_id"]

    # Validate machine_id matches token
    if data.machine_id != machine_id:
        raise HTTPException(
            status_code=403,
            detail="Machine ID doesn't match authenticated device"
        )

    # Update inventory
    await db.update_inventory(company, machine_id, data.items)

    # Log events
    event_ids = []
    for event in data.events:
        event_id = await db.log_event(company, machine_id, event.model_dump())
        event_ids.append(event_id)

    processing_time = time.time() - start_time

    return {
        "status": "ok",
        "machine_id": machine_id,
        "items_updated": len(data.items),
        "events_logged": len(event_ids),
        "processing_time_ms": round(processing_time * 1000, 2)
    }

@router.get("/{machine_id}")
async def get_inventory(
    machine_id: str,
    company: str,
    db: FirestoreClient = Depends()
):
    """
    Get current inventory for a machine.

    Public endpoint - no authentication required.
    """
    inventory = await db.get_inventory(company, machine_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Machine not found")

    # Get machine info for location
    machine = await db.get_machine(company, machine_id)

    return {
        "machine_id": machine_id,
        "location": machine.get("location", "Unknown") if machine else "Unknown",
        "items": inventory.get("items", {}),
        "last_updated": inventory.get("last_updated")
    }
```

**Request/Response Models:**
```python
# app/models/inventory.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    SNACK_TAKEN = "SNACK_TAKEN"
    SNACK_ADDED = "SNACK_ADDED"

class InventoryItem(BaseModel):
    count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)

class InventoryEvent(BaseModel):
    type: EventType
    item: str
    count_before: int
    count_after: int

class InventoryUpdate(BaseModel):
    machine_id: str
    timestamp: datetime
    items: dict[str, InventoryItem]
    events: list[InventoryEvent] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "machine_id": "breakroom-1",
                "timestamp": "2026-01-10T12:00:00Z",
                "items": {
                    "chips_bag": {"count": 5, "confidence": 0.92},
                    "candy_bar": {"count": 3, "confidence": 0.88}
                },
                "events": [
                    {
                        "type": "SNACK_TAKEN",
                        "item": "chips_bag",
                        "count_before": 6,
                        "count_after": 5
                    }
                ]
            }
        }
    }
```

**Edge Device Client (for E1-S5):**
```python
# api/client.py (on edge device)
import httpx
from datetime import datetime

class CloudAPIClient:
    def __init__(self, base_url: str, api_key: str, company: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.company = company
        self.client = httpx.AsyncClient(timeout=10.0)

    async def push_delta(self, delta) -> dict:
        """Push inventory delta to cloud."""
        response = await self.client.post(
            f"{self.base_url}/inventory/update",
            params={"company": self.company},
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "machine_id": delta.machine_id,
                "timestamp": delta.timestamp.isoformat(),
                "items": {
                    name: {"count": item.count, "confidence": item.confidence}
                    for name, item in delta.inventory.items()
                },
                "events": [
                    {
                        "type": event.type.value,
                        "item": event.item,
                        "count_before": event.count_before,
                        "count_after": event.count_after
                    }
                    for event in delta.events
                ]
            }
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
```

**Rate Limiting (Optional):**
```python
# app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.requests = defaultdict(list)

    async def check(self, request: Request):
        client_ip = request.client.host
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > minute_ago
        ]

        if len(self.requests[client_ip]) >= self.rpm:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )

        self.requests[client_ip].append(now)
```

### Definition of Done

- [ ] POST /inventory/update endpoint implemented
- [ ] Pydantic validation for payloads
- [ ] Machine status updated on each push
- [ ] Events logged to Firestore
- [ ] Rate limiting in place
- [ ] Edge client updated to push deltas
- [ ] Integration test: edge → cloud → Firestore

### Dependencies

- **Requires:** E2-S3 (Bearer Token Auth)
- **Integrates with:** E1-S5 (Inventory State Manager)

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - well-defined API contract

---

## E2-S5: Build Consumer PWA with Vue 3 + Vite

### User Story

**As a** frontend developer,
**I want** a Vue 3 PWA scaffold with Vite and Pinia,
**So that** I have a foundation for the inventory display.

### Acceptance Criteria

```gherkin
Feature: Vue PWA Scaffold

Scenario: App loads successfully
  Given the PWA is deployed
  When I navigate to the app URL
  Then the app shell loads
  And no console errors appear
  And the title shows "FoodInsight"

Scenario: Vite dev server works
  Given I am in the project directory
  When I run "bun run dev"
  Then the dev server starts on localhost:5173
  And hot module replacement works

Scenario: Production build succeeds
  Given the project is configured
  When I run "bun run build"
  Then the build completes without errors
  And output is in the dist/ directory
  And bundle size is under 200KB gzipped

Scenario: Pinia store is available
  Given the app is running
  When I access the inventory store
  Then the store is properly initialized
  And state is reactive

Scenario: Tailwind CSS is configured
  Given the app is running
  When I use Tailwind classes
  Then styles are applied correctly
  And unused styles are purged in production
```

### Technical Notes

**Project Setup:**
```bash
# Create Vue project with Vite
bun create vite foodinsight-app --template vue-ts
cd foodinsight-app

# Install dependencies
bun add pinia @vueuse/core
bun add -D tailwindcss postcss autoprefixer
bun add -D vite-plugin-pwa

# Initialize Tailwind
bunx tailwindcss init -p
```

**Project Structure:**
```
foodinsight-app/
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── views/
│   │   └── InventoryView.vue
│   ├── components/
│   │   └── .gitkeep
│   ├── stores/
│   │   └── inventory.ts
│   ├── composables/
│   │   └── useApi.ts
│   ├── types/
│   │   └── inventory.ts
│   └── assets/
│       └── main.css
├── public/
│   ├── favicon.ico
│   └── icons/
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

**Main Entry:**
```typescript
// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
```

**App Component:**
```vue
<!-- src/App.vue -->
<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-white shadow-sm">
      <div class="max-w-4xl mx-auto px-4 py-4">
        <h1 class="text-2xl font-bold text-gray-900">FoodInsight</h1>
        <p class="text-sm text-gray-500">Break Room Snacks</p>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-6">
      <InventoryView />
    </main>
  </div>
</template>

<script setup lang="ts">
import InventoryView from './views/InventoryView.vue'
</script>
```

**Inventory Store:**
```typescript
// src/stores/inventory.ts
import { defineStore } from 'pinia'
import type { InventoryItem } from '@/types/inventory'

interface InventoryState {
  items: InventoryItem[]
  lastUpdated: Date | null
  loading: boolean
  error: string | null
  machineId: string
  location: string
}

export const useInventoryStore = defineStore('inventory', {
  state: (): InventoryState => ({
    items: [],
    lastUpdated: null,
    loading: false,
    error: null,
    machineId: 'breakroom-1',
    location: 'Break Room'
  }),

  getters: {
    availableItems: (state) => state.items.filter(item => item.count > 0),
    outOfStockItems: (state) => state.items.filter(item => item.count === 0),
    totalItems: (state) => state.items.reduce((sum, item) => sum + item.count, 0)
  },

  actions: {
    async fetchInventory() {
      // Will be implemented in E2-S6
    }
  }
})
```

**Types:**
```typescript
// src/types/inventory.ts
export interface InventoryItem {
  name: string
  count: number
  confidence: number
  inStock: boolean
}

export interface InventoryResponse {
  machine_id: string
  location: string
  items: Record<string, { count: number; confidence: number }>
  last_updated: string
}
```

**Vite Config:**
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'FoodInsight',
        short_name: 'FoodInsight',
        theme_color: '#1f2937',
        icons: [
          {
            src: '/icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
```

**Tailwind Config:**
```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Main CSS:**
```css
/* src/assets/main.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Definition of Done

- [ ] Vue 3 + Vite project scaffolded
- [ ] Pinia store configured
- [ ] Tailwind CSS working
- [ ] PWA plugin configured
- [ ] TypeScript types defined
- [ ] Dev server runs without errors
- [ ] Production build under 200KB
- [ ] Deployed to Cloudflare Pages (dev)

### Dependencies

- **Requires:** None (can parallel with backend)
- **Blocked by:** None

### Complexity

**Points:** 2 (Small)
**Risk:** Low - standard Vue setup

---

## E2-S6: Implement Inventory Grid Display

### User Story

**As an** employee,
**I want** to see a grid of snack items with their counts and stock status,
**So that** I can quickly see what's available in the break room.

### Acceptance Criteria

```gherkin
Feature: Inventory Display

Scenario: Items are displayed in a grid
  Given the inventory has 6 items
  When I view the inventory page
  Then I see a responsive grid of snack cards
  And each card shows the item name and count

Scenario: Available items are clearly indicated
  Given an item has count > 0
  When I view the item card
  Then the count is displayed prominently
  And the card has a green/available indicator

Scenario: Out of stock items are indicated
  Given an item has count = 0
  When I view the item card
  Then "Out of Stock" is displayed
  And the card is grayed out
  And it appears after available items

Scenario: Last updated time is shown
  Given inventory was last updated at 12:30 PM
  When I view the page
  Then I see "Last updated: 12:30 PM" or relative time
  And this updates with each refresh

Scenario: Loading state is shown
  Given inventory is being fetched
  When the API call is in progress
  Then a loading skeleton or spinner is displayed
  And items are not shown until loaded

Scenario: Error state is handled
  Given the API returns an error
  When I view the page
  Then an error message is displayed
  And a retry button is available
```

### Technical Notes

**InventoryView:**
```vue
<!-- src/views/InventoryView.vue -->
<template>
  <div>
    <!-- Loading State -->
    <div v-if="store.loading" class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <SkeletonCard v-for="i in 6" :key="i" />
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="text-center py-8">
      <p class="text-red-600 mb-4">{{ store.error }}</p>
      <button
        @click="store.fetchInventory"
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Retry
      </button>
    </div>

    <!-- Inventory Grid -->
    <div v-else>
      <div class="mb-4 text-sm text-gray-500">
        <LastUpdated :timestamp="store.lastUpdated" />
      </div>

      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <SnackCard
          v-for="item in sortedItems"
          :key="item.name"
          :item="item"
        />
      </div>

      <p v-if="store.items.length === 0" class="text-center py-8 text-gray-500">
        No snacks configured for this location.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import SnackCard from '@/components/SnackCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import LastUpdated from '@/components/LastUpdated.vue'

const store = useInventoryStore()

// Sort: available items first, then out of stock
const sortedItems = computed(() => {
  return [...store.items].sort((a, b) => {
    if (a.inStock && !b.inStock) return -1
    if (!a.inStock && b.inStock) return 1
    return a.name.localeCompare(b.name)
  })
})

onMounted(() => {
  store.fetchInventory()
})
</script>
```

**SnackCard Component:**
```vue
<!-- src/components/SnackCard.vue -->
<template>
  <div
    class="rounded-lg p-4 shadow-sm transition-all"
    :class="cardClasses"
  >
    <div class="flex items-center justify-between mb-2">
      <span class="text-2xl">{{ emoji }}</span>
      <span
        class="px-2 py-1 text-xs rounded-full"
        :class="statusClasses"
      >
        {{ statusText }}
      </span>
    </div>

    <h3 class="font-medium text-gray-900 truncate" :title="item.name">
      {{ displayName }}
    </h3>

    <div class="mt-2">
      <span v-if="item.inStock" class="text-3xl font-bold text-gray-900">
        {{ item.count }}
      </span>
      <span v-else class="text-lg text-gray-400">
        Out of Stock
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { InventoryItem } from '@/types/inventory'

const props = defineProps<{
  item: InventoryItem
}>()

const cardClasses = computed(() => ({
  'bg-white': props.item.inStock,
  'bg-gray-100 opacity-60': !props.item.inStock
}))

const statusClasses = computed(() => ({
  'bg-green-100 text-green-800': props.item.inStock,
  'bg-gray-200 text-gray-600': !props.item.inStock
}))

const statusText = computed(() =>
  props.item.inStock ? 'Available' : 'Empty'
)

// Map item names to emojis
const emojiMap: Record<string, string> = {
  chips_bag: '🥔',
  candy_bar: '🍫',
  granola_bar: '🥜',
  soda_can: '🥤',
  water_bottle: '💧',
  energy_drink: '⚡',
  cookies_pack: '🍪',
  nuts_pack: '🥜',
  default: '🍿'
}

const emoji = computed(() =>
  emojiMap[props.item.name] || emojiMap.default
)

const displayName = computed(() =>
  props.item.name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
)
</script>
```

**LastUpdated Component:**
```vue
<!-- src/components/LastUpdated.vue -->
<template>
  <span class="flex items-center gap-1">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span v-if="timestamp">Last updated: {{ formattedTime }}</span>
    <span v-else>Never updated</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTimeAgo } from '@vueuse/core'

const props = defineProps<{
  timestamp: Date | null
}>()

const formattedTime = computed(() => {
  if (!props.timestamp) return ''

  const now = new Date()
  const diff = now.getTime() - props.timestamp.getTime()

  // If less than 1 minute ago
  if (diff < 60000) {
    return 'Just now'
  }

  // If less than 1 hour ago, show minutes
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  }

  // Otherwise show time
  return props.timestamp.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  })
})
</script>
```

**SkeletonCard Component:**
```vue
<!-- src/components/SkeletonCard.vue -->
<template>
  <div class="bg-white rounded-lg p-4 shadow-sm animate-pulse">
    <div class="flex items-center justify-between mb-2">
      <div class="w-8 h-8 bg-gray-200 rounded"></div>
      <div class="w-16 h-5 bg-gray-200 rounded-full"></div>
    </div>
    <div class="w-24 h-5 bg-gray-200 rounded mt-2"></div>
    <div class="w-12 h-8 bg-gray-200 rounded mt-2"></div>
  </div>
</template>
```

**Update Store with API Fetch:**
```typescript
// src/stores/inventory.ts (update fetchInventory action)
actions: {
  async fetchInventory() {
    this.loading = true
    this.error = null

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/inventory/${this.machineId}?company=${import.meta.env.VITE_COMPANY}`
      )

      if (!response.ok) {
        throw new Error('Failed to fetch inventory')
      }

      const data: InventoryResponse = await response.json()

      this.items = Object.entries(data.items).map(([name, item]) => ({
        name,
        count: item.count,
        confidence: item.confidence,
        inStock: item.count > 0
      }))

      this.location = data.location
      this.lastUpdated = data.last_updated ? new Date(data.last_updated) : null

    } catch (e) {
      this.error = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      this.loading = false
    }
  }
}
```

### Definition of Done

- [ ] SnackCard component with count and status
- [ ] Grid layout responsive (2 cols mobile, 3 cols desktop)
- [ ] Out of stock items grayed and sorted last
- [ ] Loading skeleton during fetch
- [ ] Error state with retry button
- [ ] Last updated timestamp displayed
- [ ] Emoji mapping for common snacks

### Dependencies

- **Requires:** E2-S5 (PWA Scaffold)
- **Requires:** E2-S4 (API available for testing)

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - standard Vue components

---

## E2-S7: Add Auto-Refresh Polling

### User Story

**As an** employee,
**I want** the inventory to automatically refresh every 30 seconds,
**So that** I always see the current snack availability.

### Acceptance Criteria

```gherkin
Feature: Auto-Refresh

Scenario: Inventory refreshes automatically
  Given I am viewing the inventory page
  When 30 seconds pass
  Then the inventory is fetched from the API
  And the display updates with new data
  And no loading indicator is shown for background refresh

Scenario: Countdown shows next refresh
  Given auto-refresh is enabled
  When I view the page
  Then I see "Refreshing in X seconds" countdown
  And the countdown updates every second

Scenario: Manual refresh is available
  Given I am viewing the inventory
  When I click the refresh button
  Then inventory fetches immediately
  And the countdown resets to 30 seconds

Scenario: Refresh pauses when tab is hidden
  Given auto-refresh is running
  When I switch to another browser tab
  Then the refresh timer pauses
  When I return to the tab
  Then the refresh triggers immediately
  And the timer resumes

Scenario: Error doesn't break refresh cycle
  Given auto-refresh is running
  When an API error occurs
  Then error is displayed
  And refresh continues after 30 seconds
  And the app doesn't crash
```

### Technical Notes

**useAutoRefresh Composable:**
```typescript
// src/composables/useAutoRefresh.ts
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useDocumentVisibility } from '@vueuse/core'

export function useAutoRefresh(
  fetchFn: () => Promise<void>,
  intervalMs: number = 30000
) {
  const secondsUntilRefresh = ref(intervalMs / 1000)
  const isRefreshing = ref(false)
  const visibility = useDocumentVisibility()

  let refreshInterval: ReturnType<typeof setInterval> | null = null
  let countdownInterval: ReturnType<typeof setInterval> | null = null

  const refresh = async () => {
    isRefreshing.value = true
    try {
      await fetchFn()
    } finally {
      isRefreshing.value = false
      resetCountdown()
    }
  }

  const resetCountdown = () => {
    secondsUntilRefresh.value = intervalMs / 1000
  }

  const startIntervals = () => {
    // Clear existing intervals
    stopIntervals()

    // Countdown timer (every second)
    countdownInterval = setInterval(() => {
      if (secondsUntilRefresh.value > 0) {
        secondsUntilRefresh.value--
      }
    }, 1000)

    // Refresh timer
    refreshInterval = setInterval(refresh, intervalMs)
  }

  const stopIntervals = () => {
    if (countdownInterval) {
      clearInterval(countdownInterval)
      countdownInterval = null
    }
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }

  // Handle tab visibility
  watch(visibility, (isVisible) => {
    if (isVisible === 'visible') {
      // Tab became visible - refresh immediately and restart
      refresh()
      startIntervals()
    } else {
      // Tab hidden - pause intervals
      stopIntervals()
    }
  })

  onMounted(() => {
    startIntervals()
  })

  onUnmounted(() => {
    stopIntervals()
  })

  return {
    secondsUntilRefresh,
    isRefreshing,
    refresh,
    resetCountdown
  }
}
```

**Update InventoryView:**
```vue
<!-- src/views/InventoryView.vue -->
<template>
  <div>
    <!-- Header with refresh status -->
    <div class="flex items-center justify-between mb-4">
      <div class="text-sm text-gray-500">
        <LastUpdated :timestamp="store.lastUpdated" />
      </div>

      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-400">
          {{ isRefreshing ? 'Refreshing...' : `Refreshing in ${secondsUntilRefresh}s` }}
        </span>
        <button
          @click="refresh"
          :disabled="isRefreshing"
          class="p-2 rounded-full hover:bg-gray-100 transition-colors"
          :class="{ 'animate-spin': isRefreshing }"
          title="Refresh now"
        >
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Loading State (only for initial load) -->
    <div v-if="store.loading && store.items.length === 0" class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <SkeletonCard v-for="i in 6" :key="i" />
    </div>

    <!-- Error State -->
    <div v-else-if="store.error && store.items.length === 0" class="text-center py-8">
      <p class="text-red-600 mb-4">{{ store.error }}</p>
      <button
        @click="refresh"
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Retry
      </button>
    </div>

    <!-- Inventory Grid -->
    <div v-else>
      <!-- Error banner for refresh failures -->
      <div v-if="store.error" class="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
        Update failed. Will retry automatically.
      </div>

      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <SnackCard
          v-for="item in sortedItems"
          :key="item.name"
          :item="item"
        />
      </div>

      <p v-if="store.items.length === 0" class="text-center py-8 text-gray-500">
        No snacks configured for this location.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import SnackCard from '@/components/SnackCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import LastUpdated from '@/components/LastUpdated.vue'

const store = useInventoryStore()

const { secondsUntilRefresh, isRefreshing, refresh } = useAutoRefresh(
  () => store.fetchInventory(),
  30000 // 30 seconds
)

const sortedItems = computed(() => {
  return [...store.items].sort((a, b) => {
    if (a.inStock && !b.inStock) return -1
    if (!a.inStock && b.inStock) return 1
    return a.name.localeCompare(b.name)
  })
})

onMounted(() => {
  store.fetchInventory()
})
</script>
```

**Update Store for Silent Refresh:**
```typescript
// src/stores/inventory.ts (add silentFetch option)
actions: {
  async fetchInventory(silent = false) {
    if (!silent) {
      this.loading = true
    }
    this.error = null

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/inventory/${this.machineId}?company=${import.meta.env.VITE_COMPANY}`
      )

      if (!response.ok) {
        throw new Error('Failed to fetch inventory')
      }

      const data: InventoryResponse = await response.json()

      this.items = Object.entries(data.items).map(([name, item]) => ({
        name,
        count: item.count,
        confidence: item.confidence,
        inStock: item.count > 0
      }))

      this.location = data.location
      this.lastUpdated = data.last_updated ? new Date(data.last_updated) : null

    } catch (e) {
      this.error = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      if (!silent) {
        this.loading = false
      }
    }
  }
}
```

### Definition of Done

- [ ] Auto-refresh every 30 seconds
- [ ] Countdown display showing seconds until refresh
- [ ] Manual refresh button
- [ ] Tab visibility detection (pause/resume)
- [ ] Silent refresh (no loading state for background)
- [ ] Error handling doesn't break cycle
- [ ] Unit tests for useAutoRefresh

### Dependencies

- **Requires:** E2-S6 (Inventory Display)
- **Blocked by:** None after E2-S6

### Complexity

**Points:** 2 (Small)
**Risk:** Low - straightforward interval logic

---

## E2-S8: Configure PWA Manifest and Service Worker

### User Story

**As an** employee,
**I want** to install FoodInsight on my phone's home screen,
**So that** I can quickly access snack availability like a native app.

### Acceptance Criteria

```gherkin
Feature: PWA Installation

Scenario: App is installable on mobile
  Given I visit the PWA on a mobile browser
  When the install criteria are met
  Then the browser shows "Add to Home Screen" prompt
  And I can install the app

Scenario: Installed app opens in standalone mode
  Given I have installed the PWA
  When I open it from my home screen
  Then it opens without browser UI
  And it shows the app's theme color in the status bar

Scenario: App icon is correct
  Given I have installed the PWA
  When I view my home screen
  Then the FoodInsight icon is displayed
  And the app name "FoodInsight" is shown

Scenario: Offline fallback works
  Given I have visited the app before
  When I go offline
  Then cached assets still load
  And I see "You're offline" message for data

Scenario: App updates automatically
  Given a new version is deployed
  When I open the installed PWA
  Then the service worker updates
  And I see the new version after refresh
```

### Technical Notes

**Vite PWA Configuration:**
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt'],

      manifest: {
        name: 'FoodInsight',
        short_name: 'FoodInsight',
        description: 'Smart snack inventory monitoring',
        theme_color: '#1f2937',
        background_color: '#f3f4f6',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/icons/icon-72.png',
            sizes: '72x72',
            type: 'image/png'
          },
          {
            src: '/icons/icon-96.png',
            sizes: '96x96',
            type: 'image/png'
          },
          {
            src: '/icons/icon-128.png',
            sizes: '128x128',
            type: 'image/png'
          },
          {
            src: '/icons/icon-144.png',
            sizes: '144x144',
            type: 'image/png'
          },
          {
            src: '/icons/icon-152.png',
            sizes: '152x152',
            type: 'image/png'
          },
          {
            src: '/icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icons/icon-384.png',
            sizes: '384x384',
            type: 'image/png'
          },
          {
            src: '/icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: '/icons/icon-512-maskable.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable'
          }
        ]
      },

      workbox: {
        // Cache strategies
        runtimeCaching: [
          {
            // Cache API responses
            urlPattern: /^https:\/\/.*\/inventory\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 // 1 minute
              },
              networkTimeoutSeconds: 5
            }
          },
          {
            // Cache static assets
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 30 * 24 * 60 * 60 // 30 days
              }
            }
          }
        ]
      },

      devOptions: {
        enabled: true // Enable PWA in dev mode for testing
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
```

**Offline Indicator Component:**
```vue
<!-- src/components/OfflineIndicator.vue -->
<template>
  <Transition name="slide">
    <div
      v-if="!isOnline"
      class="fixed bottom-0 left-0 right-0 bg-yellow-500 text-yellow-900 px-4 py-2 text-center text-sm"
    >
      You're offline. Showing cached data.
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useOnline } from '@vueuse/core'

const isOnline = useOnline()
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateY(100%);
}
</style>
```

**Update App.vue:**
```vue
<!-- src/App.vue -->
<template>
  <div class="min-h-screen bg-gray-100 pb-12">
    <header class="bg-white shadow-sm">
      <div class="max-w-4xl mx-auto px-4 py-4">
        <h1 class="text-2xl font-bold text-gray-900">FoodInsight</h1>
        <p class="text-sm text-gray-500">{{ location }}</p>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-6">
      <InventoryView />
    </main>

    <OfflineIndicator />
    <PWAUpdatePrompt />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import InventoryView from './views/InventoryView.vue'
import OfflineIndicator from './components/OfflineIndicator.vue'
import PWAUpdatePrompt from './components/PWAUpdatePrompt.vue'

const store = useInventoryStore()
const location = computed(() => store.location || 'Break Room Snacks')
</script>
```

**PWA Update Prompt:**
```vue
<!-- src/components/PWAUpdatePrompt.vue -->
<template>
  <Transition name="slide">
    <div
      v-if="needRefresh"
      class="fixed bottom-16 left-4 right-4 bg-blue-600 text-white rounded-lg shadow-lg p-4"
    >
      <p class="text-sm mb-2">A new version is available!</p>
      <div class="flex gap-2">
        <button
          @click="updateServiceWorker"
          class="px-3 py-1 bg-white text-blue-600 rounded text-sm font-medium"
        >
          Update
        </button>
        <button
          @click="close"
          class="px-3 py-1 text-blue-100 text-sm"
        >
          Later
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useRegisterSW } from 'virtual:pwa-register/vue'

const {
  needRefresh,
  updateServiceWorker
} = useRegisterSW()

const close = () => {
  needRefresh.value = false
}
</script>
```

**Icon Generation Script:**
```bash
#!/bin/bash
# scripts/generate-icons.sh

# Requires ImageMagick
# brew install imagemagick

SOURCE="public/icon-source.png"  # 1024x1024 source image
OUTPUT_DIR="public/icons"

mkdir -p $OUTPUT_DIR

# Generate various sizes
for size in 72 96 128 144 152 192 384 512; do
  convert $SOURCE -resize ${size}x${size} $OUTPUT_DIR/icon-${size}.png
done

# Generate maskable icon (with padding)
convert $SOURCE -resize 512x512 -gravity center -background white \
  -extent 614x614 $OUTPUT_DIR/icon-512-maskable.png

echo "Icons generated in $OUTPUT_DIR"
```

**HTML Meta Tags:**
```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#1f2937">
  <meta name="description" content="Smart snack inventory monitoring">

  <!-- iOS specific -->
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="FoodInsight">
  <link rel="apple-touch-icon" href="/icons/icon-192.png">

  <link rel="icon" href="/favicon.ico">
  <title>FoodInsight</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

### Definition of Done

- [ ] PWA manifest configured with all icon sizes
- [ ] Service worker registered and caching assets
- [ ] App installable on iOS and Android
- [ ] Standalone display mode working
- [ ] Offline indicator shown when offline
- [ ] Update prompt for new versions
- [ ] Icons generated at all required sizes
- [ ] Lighthouse PWA audit score > 90

### Dependencies

- **Requires:** E2-S7 (Auto-refresh for offline handling)
- **Blocked by:** None after E2-S7

### Complexity

**Points:** 3 (Medium)
**Risk:** Low - vite-plugin-pwa handles most complexity

---

## Epic 2 Summary

| Story | Title | Points | Dependencies |
|-------|-------|--------|--------------|
| E2-S1 | FastAPI Scaffold | 2 | GCP setup |
| E2-S2 | Firestore Integration | 3 | E2-S1 |
| E2-S3 | Bearer Token Auth | 3 | E2-S2 |
| E2-S4 | Edge API Integration | 3 | E2-S3 |
| E2-S5 | Vue PWA Scaffold | 2 | None |
| E2-S6 | Inventory Display | 3 | E2-S5, E2-S4 |
| E2-S7 | Auto-refresh | 2 | E2-S6 |
| E2-S8 | PWA Features | 3 | E2-S7 |
| **Total** | | **21** | |

### Dependency Graph

```
                     E2-S1 (FastAPI)
                          │
                          ▼
                     E2-S2 (Firestore)
                          │
                          ▼
                     E2-S3 (Auth)
                          │
                          ▼
                     E2-S4 (Edge API)
                          │
        ┌─────────────────┼─────────────────┐
        │                                   │
        ▼                                   ▼
E2-S5 (Vue Scaffold)              [Edge Device E1-S5]
        │
        ▼
E2-S6 (Inventory Display)
        │
        ▼
E2-S7 (Auto-refresh)
        │
        ▼
E2-S8 (PWA Features)
```

### Parallel Tracks

**Track A: Backend (E2-S1 → E2-S4)**
- Sequential due to dependencies
- Can start immediately

**Track B: Frontend (E2-S5 → E2-S8)**
- E2-S5 can start immediately (no backend deps)
- E2-S6 needs E2-S4 for real data (can mock initially)
- E2-S7, E2-S8 are sequential

### Recommended Implementation Order

1. **Sprint 1:** E2-S1 + E2-S5 in parallel (scaffolds)
2. **Sprint 1:** E2-S2 + continue E2-S5
3. **Sprint 2:** E2-S3 + E2-S6 (with mocked data)
4. **Sprint 2:** E2-S4 (connect edge)
5. **Sprint 3:** E2-S7, E2-S8 (polish)

---

## Integration Points

### Edge → Cloud (E1-S5 + E2-S4)

The edge device's `InventoryStateManager` (E1-S5) generates deltas that are pushed via `CloudAPIClient` to the FastAPI endpoint (E2-S4).

```
E1-S5 InventoryStateManager
         │
         │ get_delta()
         ▼
    CloudAPIClient
         │
         │ POST /inventory/update
         ▼
    E2-S4 FastAPI endpoint
         │
         │ update_inventory()
         ▼
    E2-S2 Firestore
```

### Cloud → PWA (E2-S4 + E2-S6)

The PWA fetches inventory via the public GET endpoint.

```
E2-S6 InventoryView
         │
         │ fetchInventory()
         ▼
    GET /inventory/{machine_id}
         │
         ▼
    E2-S4 FastAPI endpoint
         │
         │ get_inventory()
         ▼
    E2-S2 Firestore
```

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | PAI | Initial stories |
