# FoodInsight Product Requirements Document (PRD)

**Author:** Benny
**Date:** 2026-01-11
**Project Level:** 2 (Focused Internal Tool)
**Project Type:** Edge AI + Local Backend + PWA
**Target Scale:** Single office break room prototype

---

## Description, Context and Goals

### Description

FoodInsight is a smart snack inventory monitoring system that uses computer vision to track snack availability in office break rooms. An edge device (Raspberry Pi 5 with camera) monitors the snack shelf, detects items using YOLO11, and pushes inventory data to a cloud backend. Employees access a simple PWA to see what snacks are currently available.

### Deployment Intent

**Internal Tool Prototype** — Prove the concept works in a real office break room environment before expanding to production deployment or vending machine use cases.

### Context

Office break rooms with self-serve snack stations face a common problem: employees don't know what's available without walking to the break room, and the office manager doesn't know when to restock until items run out. The current state is manual inventory checks or empty shelves frustrating employees.

FoodInsight solves this by providing real-time inventory visibility. This prototype validates that edge AI can accurately detect packaged snacks at a cost-effective price point ($80 hardware) before investing in production-grade infrastructure.

### Goals

| Goal | Success Metric | Priority |
|------|----------------|----------|
| **G1: Accurate Detection** | ≥85% mAP on target snack classes | Must Have |
| **G2: Real-time Inventory** | Inventory updates within 5 seconds of change | Must Have |
| **G3: Employee Visibility** | Employees can check availability via PWA | Must Have |
| **G4: Cost-Effective Hardware** | Edge device under $100 total | Must Have |
| **G5: Privacy Preserved** | No faces/people stored or transmitted | Should Have |

---

## Requirements

### Functional Requirements

#### FR1: Snack Detection (Edge Device)
- **FR1.1** System shall detect and classify snack items from camera feed
- **FR1.2** System shall use YOLO11n model optimized for CPU inference (NCNN format)
- **FR1.3** System shall support motion-triggered detection to reduce CPU load
- **FR1.4** System shall maintain persistent object tracking across frames (ByteTrack)
- **FR1.5** System shall detect when items are taken (disappear) or added (appear)
- **FR1.6** System shall filter detections to configurable allowed classes only (reduces noise from non-food objects)

#### FR2: Inventory State Management (Edge Device)
- **FR2.1** System shall maintain current inventory count per snack class
- **FR2.2** System shall push delta updates to cloud backend when inventory changes
- **FR2.3** System shall include timestamp and confidence scores in updates
- **FR2.4** System shall batch updates to avoid excessive API calls (max 1 update/second)

#### FR3: Local Backend (FastAPI)
- **FR3.1** Backend shall receive and store inventory updates from edge device
- **FR3.2** Backend shall provide REST API for retrieving current inventory
- **FR3.3** Backend shall store data in SQLite for local-first operation (no cloud dependency)
- **FR3.4** Backend shall provide admin API with Basic authentication for configuration

#### FR4: Consumer PWA (Client App)
- **FR4.1** App shall display current snack inventory for the break room
- **FR4.2** App shall show item name and current count
- **FR4.3** App shall indicate when items are out of stock
- **FR4.4** App shall auto-refresh inventory periodically (every 30 seconds)
- **FR4.5** App shall work on mobile and desktop browsers
- **FR4.6** App shall be installable as PWA (add to home screen)

#### FR5: Privacy Pipeline (Edge Device)
- **FR5.1** System shall only process snack shelf ROI (region of interest)
- **FR5.2** System shall blur/mask areas outside the defined ROI
- **FR5.3** System shall NOT store or transmit full camera frames to cloud
- **FR5.4** System shall only transmit inventory metadata (counts, not images)

#### FR6: Edge Admin Portal (Edge Device)
- **FR6.1** Admin portal shall allow camera preview on local network only
- **FR6.2** Admin portal shall allow ROI configuration (drag to select snack area)
- **FR6.3** Admin portal shall display detection status and frame rate
- **FR6.4** Admin portal shall NOT be accessible from internet

### Non-Functional Requirements

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| **NFR1** | Detection latency | <500ms per frame (CPU mode) | Must Have |
| **NFR2** | API response time | <200ms for inventory queries | Must Have |
| **NFR3** | PWA load time | <2 seconds on 4G | Should Have |
| **NFR4** | System uptime | 95% during office hours | Should Have |
| **NFR5** | Edge device power | <15W continuous | Should Have |
| **NFR6** | Infrastructure cost | $0/month (local SQLite, no cloud) | Must Have |
| **NFR7** | Data retention | 30 days of inventory history | Could Have |
| **NFR8** | Offline mode | System operates fully offline (local-first design) | Must Have |

---

## User Journeys

### Journey 1: Employee Checks Snack Availability

**Persona:** Alex, Software Developer
**Goal:** See what snacks are available before walking to break room

```
1. Alex opens FoodInsight PWA on phone (bookmarked)
2. App loads showing "Break Room Snacks" header
3. Alex sees grid of snack items with counts:
   - Chips (Lays): 5
   - Candy Bar (Snickers): 2
   - Granola Bar: 0 (Out of Stock - grayed out)
   - Soda (Coke): 8
4. Alex sees there's no granola bars left
5. Alex decides to grab chips instead
6. Alex walks to break room, takes a bag of chips
7. (Behind scenes: count updates to 4 within 5 seconds)
```

**Success Criteria:**
- App loads in <2 seconds
- Inventory shown is accurate (matches physical state)
- Out of stock items clearly indicated

### Journey 2: Office Manager Reviews System (Future Phase)

> Note: Deferred to post-prototype phase. Manager dashboard not in MVP scope.

### Journey 3: Admin Configures Edge Device

**Persona:** IT Admin (Benny)
**Goal:** Set up the FoodInsight edge device in break room

```
1. Admin connects to edge device via local network (http://192.168.1.x)
2. Admin sees camera feed with live detection overlay
3. Admin clicks "Configure ROI" and drags rectangle over snack shelf area
4. Admin sees detections now only within the defined region
5. Admin verifies detection is working (sees bounding boxes on snacks)
6. Admin clicks "Save Configuration"
7. System confirms "Configuration saved. Monitoring active."
```

**Success Criteria:**
- ROI configuration intuitive (drag to select)
- Detection visually confirmed before saving
- Configuration persists across reboots

---

## UX Design Principles

| Principle | Description |
|-----------|-------------|
| **Glanceable** | Consumer view shows availability at a glance—no reading required |
| **Zero Friction** | No login required for employees to view inventory |
| **Mobile First** | Optimized for phone screens, works on desktop too |
| **Real Feedback** | Show "Last updated" timestamp so users trust data freshness |
| **Accessible** | Color + icons for stock status (not color alone) |
| **Fast** | Loads instantly, no spinners for cached data |

---

## Epics

### Epic 1: Edge Detection System (Core Infrastructure)

**Goal:** Camera captures snacks, YOLO11 detects them, inventory state managed locally

**Stories:**
1. **E1-S1:** Set up RPi 5 with camera and base OS
2. **E1-S2:** Implement YOLO11n inference with NCNN (CPU-optimized)
3. **E1-S3:** Add motion-triggered detection for CPU efficiency
4. **E1-S4:** Implement ByteTrack object tracking for persistent IDs
5. **E1-S5:** Create inventory state manager (detect additions/removals)
6. **E1-S6:** Build Edge Admin Portal (Flask+HTMX) with camera preview
7. **E1-S7:** Implement ROI configuration UI
8. **E1-S8:** Add privacy masking (blur outside ROI)

**Acceptance Criteria:**
- [x] Detection runs at 4-6 FPS on RPi 5 CPU (achieved ~45 FPS on Mac M4 Pro dev)
- [x] Admin can configure ROI via local web interface
- [x] System detects when items taken/added within 5 seconds
- [x] Privacy: only ROI area processed

**Implementation Status:** COMPLETE (2026-01-10)
- All 8 stories implemented at `/Users/bcheung/dev/FoodInsight/`
- YOLO11n exported to NCNN format, ByteTrack tracking working
- Flask admin portal with live camera preview and ROI configuration

### Epic 2: Local Backend + Consumer App

**Goal:** Inventory data stored locally, employees view via PWA

**Stories:**
1. **E2-S1:** Create FastAPI backend with /inventory endpoints
2. **E2-S2:** Implement SQLite data model (inventory, events, config, users)
3. **E2-S3:** Add Basic authentication for admin API endpoints
4. **E2-S4:** Edge device pushes delta updates to local backend
5. **E2-S5:** Build Consumer PWA with Vue 3 + Vite
6. **E2-S6:** Implement inventory grid display with stock indicators
7. **E2-S7:** Add auto-refresh (polling every 30 seconds)
8. **E2-S8:** Configure PWA manifest and service worker

**Acceptance Criteria:**
- [x] Edge device pushes updates within 2 seconds of detection
- [x] PWA loads in <2 seconds (33KB gzipped)
- [x] PWA installable on mobile devices
- [x] Inventory display matches edge device state

**Implementation Status:** COMPLETE (2026-01-11)
- FastAPI backend with SQLite at `/Users/bcheung/dev/FoodInsight/server/`
- Vue 3 PWA at `/Users/bcheung/dev/FoodInsight/app/`
- Local-first design: no cloud dependency required
- Full stack tested locally: backend on :8000, frontend on :5173, admin on :8080

---

## Out of Scope (Prototype Phase)

| Feature | Reason | Future Phase |
|---------|--------|--------------|
| Manager Dashboard | Not needed for prototype validation | Phase 2 |
| Low Stock Alerts | Requires manager role/notifications | Phase 2 |
| Multi-machine Support | Prototype uses single break room | Phase 2 |
| Operator/Restock Mode | Internal tool doesn't need this | Phase 3 |
| Hailo-8L Acceleration | CPU-only for cost reduction | Phase 2 if needed |
| Custom Snack Model Training | Use pre-trained/Roboflow datasets first | Phase 2 |
| Usage Analytics | Focus on core detection first | Phase 3 |
| WebSocket Real-time | Polling sufficient for prototype | Phase 2 |

---

## Assumptions and Dependencies

### Assumptions

1. **Lighting:** Break room has consistent lighting during office hours
2. **Shelf Layout:** Snacks displayed on open shelving (not behind glass)
3. **Network:** Break room has WiFi connectivity for edge device
4. **Snack Variety:** 8-15 different snack types to detect
5. **Existing Data:** Pre-labeled snack datasets available from Roboflow Universe

### Dependencies

| Dependency | Type | Risk |
|------------|------|------|
| Raspberry Pi 4/5 availability | Hardware | Low |
| Roboflow Universe snack datasets | Data | Low |
| Local network connectivity | Infrastructure | Low |
| SQLite (bundled with Python) | Database | None |

---

## Technical Preferences (Captured)

From architecture proposal:
- **Edge Device:** Raspberry Pi 5 8GB ($80) or RPi 4 ($55)
- **Detection Model:** YOLO11n (NCNN format for CPU)
- **Backend:** FastAPI (Python 3.11+) with SQLite
- **Database:** SQLite (local-first, no cloud dependency)
- **Client App:** Vue 3 + Vite PWA
- **Edge Admin:** Flask + HTMX
- **Hosting:** All local (PWA served from device or static hosting)
- **Allowed Classes:** Configurable filter for detection (default: food-related COCO classes - bottle, cup, bowl, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake, etc.)
- **Camera Index:** Configurable camera selection for development (0=iPhone via Continuity Camera, 1=built-in webcam on Mac)
- **Motion Threshold:** 0.008 (high sensitivity for item detection)

---

## Next Steps

### Immediate Actions

1. **Run Solution Architecture Workflow**
   - Input: This PRD
   - Output: `architecture.md` with component design

2. **Generate User Stories**
   - Command: `workflow create-story`
   - Output: Detailed stories with acceptance criteria

3. **Procure Hardware**
   - Order: Raspberry Pi 5 8GB, Camera Module 3, 64GB SD card
   - Estimated cost: ~$120 total

4. **Download Snack Datasets**
   - Source: Roboflow Universe (snack, vending machine datasets)
   - Action: Download and validate class coverage

---

## Document Status

- [x] Goals and context defined
- [x] Functional requirements complete
- [x] Non-functional requirements specified
- [x] User journeys mapped (2 of 3)
- [x] Epic structure defined (2 epics, 16 stories)
- [x] Architecture phase complete
- [x] **Epic 1 IMPLEMENTED** (2026-01-10)
- [x] **Epic 2 IMPLEMENTED** (2026-01-11, migrated to SQLite)

## Implementation Summary

| Component | Location | Status |
|-----------|----------|--------|
| Edge Detection | `detection/` | Complete |
| Admin Portal | `admin/` | Complete |
| Privacy Pipeline | `privacy/` | Complete |
| Local Backend (SQLite) | `server/` | Complete |
| Consumer PWA | `app/` | Complete |
| Dev Scripts | `scripts/` | Complete |

**MVP Status:** Ready for local deployment (no cloud required)

---

_This PRD is scoped for Level 2 (Internal Tool Prototype) — focused delivery without overburden._

---

**Related Documents:**
- [[FoodInsight Modernized Architecture Proposal]] — Technical foundation
- [[HIVE AI Insight Codebase Research]] — Reference architecture patterns
