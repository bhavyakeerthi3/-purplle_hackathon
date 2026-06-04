# 🛍️ Purplle Intelligence — Retail Store AI

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/YOLOv8-Detection-8B5CF6?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/ByteTrack-Tracking-EC4899?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Tests-10%20Passing-22C55E?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge"/>
</p>

<p align="center">
  <b>End-to-end computer vision pipeline that transforms raw CCTV footage into actionable retail intelligence.</b><br/>
  Person detection · Multi-object tracking · Zone analytics · Queue management · Anomaly detection · Live dashboard
</p>

---

> **Purplle Tech Challenge 2026 — Round 2 Submission**  
> Repository: `bhavyakeerthi3/-purplle_hackathon`

---

## 🎯 The Problem

Offline retail stores are flying blind. E-commerce teams know exactly where users click, how long they browse, and where they drop off. Physical stores don't. Store managers at Purplle know their POS revenue but have no visibility into:

- Why customers abandon the billing queue.
- Which shelves attract the most attention but generate the least sales.
- When zones get overcrowded and drive customers away.
- How footfall patterns change hour by hour.

**Purplle Intelligence solves this** by converting existing CCTV infrastructure into a real-time analytics engine — no new hardware required.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CCTV Cameras (8 feeds)               │
│           ST1008 (4 cams) · ST1009 (4 cams)             │
└────────────────────┬────────────────────────────────────┘
                     │  raw MP4
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  process_videos.py                      │
│  YOLOv8 Detection → ByteTrack Tracking → Zone Mapping  │
│         Event Emission → Aggregation → Anomalies        │
└────────┬────────────────────────────────────┬───────────┘
         │                                    │
         ▼                                    ▼
  JSONL event log                    JSON analytics files
  (replayable stream)                store_analytics.json
                                     sales_analytics.json
                                     anomalies.json
         │                                    │
         └────────────────┬───────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     server.py (FastAPI)                 │
│    REST API · SSE Event Stream · Pydantic Validation    │
│        Swagger Docs /docs · Dashboard /dashboard        │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Evaluation Criteria — Full Coverage

| Requirement | Status | Implementation |
|---|:---:|---|
| Containerized solution | ✅ Done | `Dockerfile` + `docker-compose.yml` |
| Runs out of the box | ✅ Done | Demo data pre-bundled in `output/` |
| Schema-validated events | ✅ Done | Pydantic models on all API responses |
| REST API | ✅ Done | 15 endpoints under `/api/v1` |
| Live Dashboard | ✅ Done | `dashboard.html` served by FastAPI |
| Event streaming | ✅ Done | `/api/v1/events/stream` SSE replay |
| Conversion funnel | ✅ Done | `/api/v1/store/{store_id}/funnel` |
| Queue analytics | ✅ Done | `/api/v1/store/{store_id}/queue` |
| Anomaly detection | ✅ Done | `/api/v1/anomalies` with severity levels |
| Sales correlation | ✅ Done | POS data + hourly footfall correlation |
| Documentation | ✅ Done | `README.md`, `ARCHITECTURE.md`, `SUBMISSION.md` |
| Unit tests | ✅ Done | 10 tests passing in `test_server.py` |
| Multi-store support | ✅ Done | ST1008 and ST1009 with 8 cameras |
| Privacy-aware design | ✅ Done | Documented in `ARCHITECTURE.md` |

---

## 🚀 Quick Start

### Option 1: Docker (Recommended — one command)

```bash
git clone https://github.com/bhavyakeerthi3/-purplle_hackathon.git
cd -purplle_hackathon
docker compose up --build
```

Open:
- 📊 **Dashboard**: http://localhost:8000/dashboard
- 📄 **Swagger API Docs**: http://localhost:8000/docs
- ❤️ **Health Check**: http://localhost:8000/api/v1/health

Stop with: `docker compose down`

---

### Option 2: Local Python (60 seconds)

> Demo analytics data is pre-bundled in `output/` — the dashboard works immediately after cloning.

```bash
git clone https://github.com/bhavyakeerthi3/-purplle_hackathon.git
cd -purplle_hackathon
pip install -r requirements.txt
python server.py
```

Open http://localhost:8000/dashboard — done!

To regenerate the demo data (optional):
```bash
pip install numpy
python generate_demo_data.py
```

---

## 🔬 Core Features

### 🤖 Computer Vision Pipeline
- **YOLOv8 person detection** — COCO person class only, minimizes false positives from shelves/products.
- **ByteTrack multi-object tracking** — Stable track IDs across frames; enables dwell time and queue duration calculation.
- **Polygon zone assignment** — Store-specific camera geometry in `config.py`; zero code changes when store layout changes.
- **8-camera support** — ST1008 (4 cameras: 2 zone, 1 entry, 1 billing) + ST1009 (4 cameras: 1 zone, 2 entry, 1 billing).

### 📊 Analytics Engine
- **Footfall tracking** — Unique visitor counts per store, zone entry/exit events per camera.
- **Zone dwell time** — Average seconds spent per zone; identifies high-engagement shelves.
- **Peak occupancy heatmap** — Colour-coded zone density across the store floor.
- **Conversion funnel** — Entry → Zone Browsing → Billing Queue → Purchase, with drop-off rates at each stage.
- **Queue intelligence** — Wait times, abandonment rate, and served-customer counts at billing.
- **Sales correlation** — POS revenue mapped against hourly footfall to surface productivity insights.
- **Anomaly detection** — High crowd density, abnormal dwell times, dead zones, and queue abandonment alerts with severity levels (HIGH / MEDIUM / LOW / INFO).

### 🌐 Production-Grade API
- **15 REST endpoints** under `/api/v1` with Pydantic schema validation.
- **Server-Sent Events** (SSE) replay stream at `/api/v1/events/stream`.
- **Pagination and filtering** on the event log by `store_id`, `event_type`, and `limit`.
- **Auto-generated Swagger docs** at `/docs` — always in sync with the implementation.
- **Health/readiness endpoint** that verifies all data files before reporting ready.

### 🖥️ Live Dashboard
A single-page analytics dashboard with zero external dependencies beyond Chart.js:
- KPI cards: Visitors, Revenue, Orders, Queue Served, Active Cameras, Anomalies.
- Hourly revenue bar chart + Brand mix donut chart.
- Zone heatmap with peak occupancy colours.
- Anomaly timeline with severity badges.
- Queue events table.
- Event feed with multi-filter support.
- Annotated CCTV video playback when local clips are present.
- 8-second auto-refresh with live clock.
- Multi-store switcher (ST1008 / ST1009).

---

## 📡 API Reference

| Endpoint | Description |
|---|---|
| `GET /` | Service metadata with dashboard and docs URLs |
| `GET /api/v1/health` | Data readiness check — verifies all JSON/JSONL files |
| `GET /api/v1/schema/events` | Full event contract documentation |
| `GET /api/v1/stores/overview` | Combined KPI across all stores |
| `GET /api/v1/store/{store_id}/overview` | Per-store KPI summary |
| `GET /api/v1/store/{store_id}/footfall` | Zone dwell time and unique visitor analytics |
| `GET /api/v1/store/{store_id}/heatmap` | Peak and average occupancy per zone |
| `GET /api/v1/store/{store_id}/queue` | Queue served, abandoned, and wait-time metrics |
| `GET /api/v1/store/{store_id}/funnel` | Conversion funnel with drop-off rates |
| `GET /api/v1/store/{store_id}/demographics` | Aggregate gender and age-bucket breakdown |
| `GET /api/v1/sales/summary` | Revenue, orders, and top brands |
| `GET /api/v1/sales/hourly` | Revenue and orders broken down by hour |
| `GET /api/v1/anomalies` | Detected operational anomaly alerts |
| `GET /api/v1/events` | Paginated, filterable event log |
| `GET /api/v1/events/stream` | SSE real-time event replay stream |

### Sample API Responses

**Health Check:**
```json
{
  "ready": true,
  "files": {
    "store_analytics.json": true,
    "sales_analytics.json": true,
    "anomalies.json": true,
    "generated_events.jsonl": true
  }
}
```

**Store Overview (ST1008):**
```json
{
  "store_id": "ST1008",
  "total_unique_visitors": 85,
  "total_revenue": 48320,
  "total_orders": 15,
  "cameras_active": 4
}
```

**Conversion Funnel:**
```json
{
  "funnel": [
    {"stage": "Store Entry",     "count": 85, "percentage": 100.0},
    {"stage": "Zone Browsing",   "count": 68, "percentage": 80.0},
    {"stage": "Billing Queue",   "count": 22, "percentage": 25.9},
    {"stage": "Purchase",        "count": 15, "percentage": 17.6}
  ],
  "conversion_rate": 17.6
}
```

**Quick curl examples:**
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/store/ST1008/overview
curl http://localhost:8000/api/v1/store/ST1008/funnel
curl http://localhost:8000/api/v1/store/ST1008/queue
curl http://localhost:8000/api/v1/anomalies
curl "http://localhost:8000/api/v1/events?store_id=ST1008&event_type=zone_entered&limit=10"
curl -N http://localhost:8000/api/v1/events/stream
```

---

## 📁 Project Structure

```
purplle-intelligence/
├── server.py                  FastAPI app — all routes, Pydantic models, SSE, dashboard
├── config.py                  Store/camera/zone polygon configuration
├── process_videos.py          YOLOv8 + ByteTrack video processing pipeline
├── generate_demo_data.py      Synthetic analytics generator for instant demo mode
├── dashboard.html             Live dashboard served by FastAPI at /dashboard
├── test_server.py             API unit tests (10 tests)
├── Dockerfile                 Multi-stage production container
├── docker-compose.yml         One-command local container run
├── requirements.txt           API/runtime dependencies (lightweight)
├── requirements-pipeline.txt  Full video pipeline dependencies (YOLOv8, etc.)
├── output/                    Pre-bundled demo JSON/JSONL analytics
│   ├── store_analytics.json
│   ├── sales_analytics.json
│   ├── anomalies.json
│   └── generated_events.jsonl
├── notebooks/
│   └── Training_set.ipynb     Google Colab T4 training/validation notebook
├── scripts/
│   └── import_demo_videos.ps1 Helper to import annotated output videos
├── ARCHITECTURE.md            Detailed system design, trade-offs, production path
└── SUBMISSION.md              Quick evaluator guide
```

---

## 🎬 Event Schema

Six event types emitted by the pipeline and available via the API:

| Event Type | Description |
|---|---|
| `entry` | Visitor entered the store (detected at entry camera) |
| `exit` | Visitor left the store |
| `zone_entered` | Visitor entered a named business zone |
| `zone_exited` | Visitor exited a named business zone |
| `queue_completed` | Visitor completed billing and purchased |
| `queue_abandoned` | Visitor left the billing queue without purchasing |

Common event fields: `event_type`, `store_id`, `camera_id`, `track_id`, `event_timestamp`, `zone_name`, `gender_pred`, `age_bucket`.

Full schema contract available at:
```
GET /api/v1/schema/events
```

---

## 🔎 Anomaly Detection

Anomalies are generated automatically and surfaced on the dashboard with severity levels:

| Anomaly Type | Trigger | Severity |
|---|---|---|
| High crowd density | Peak occupancy exceeds threshold | HIGH |
| Long queue wait | Average wait time unusually high | HIGH |
| Queue abandonment | Visitors leave billing queue | MEDIUM |
| High dwell time | Zone dwell abnormally long | MEDIUM |
| Dead zone | Configured zone has zero visitors | LOW |

---

## 🧪 Testing

```bash
python -m unittest test_server.py
```

```
Ran 10 tests in 1.23s
OK
```

Tests cover: health check, store overview, footfall, heatmap, queue, funnel, demographics, sales summary, hourly sales, and anomalies endpoints.

---

## 🐳 Docker Verification

```bash
docker compose build
docker compose up -d
curl http://localhost:8000/api/v1/health
docker compose down
```

---

## 🎥 Full Video Pipeline

> Only needed if you have the raw CCTV footage. The repo works instantly without this step.

```bash
pip install -r requirements-pipeline.txt
```

Place videos in:
```
data/store1/
  CAM 1 - zone.mp4
  CAM 2 - zone.mp4
  CAM 3 - entry.mp4
  CAM 5 - billing.mp4

data/store2/
  zone.mp4
  billing_area.mp4
  entry 1.mp4
  entry 2.mp4
```

Run:
```bash
python process_videos.py        # Process all stores
python process_videos.py --store ST1   # ST1008 only
python process_videos.py --store ST2   # ST1009 only
python server.py
```

Pipeline outputs:
```
output/generated_events.jsonl
output/store_analytics.json
output/sales_analytics.json
output/anomalies.json
output/output_<store>_<camera>.mp4       (annotated)
output/compressed_<store>_<camera>.mp4  (web-optimized)
```

Import already-generated annotated clips from Downloads:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\import_demo_videos.ps1 -Source "$env:USERPROFILE\Downloads"
```

---

## 🛡️ Privacy & Responsible AI

Demographics in this hackathon build are **demo-mode aggregate labels** — no real face analysis is performed. A production deployment should:

- Use local-only inference (no frames leave the network).
- Store only aggregate counts, never individual biometric data.
- Provide per-store opt-out controls for demographic inference.
- Document data retention and deletion policies.
- Comply with applicable CCTV analytics regulations.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full production privacy design.

---

## 🔮 Production Upgrade Path

| Current (Hackathon) | Production Equivalent |
|---|---|
| JSONL event file | Kafka / Pub/Sub / Kinesis |
| Local output JSON | Redis + ClickHouse / BigQuery |
| Local MP4 files | Object storage (S3/GCS) + CDN |
| Single FastAPI process | Containerized microservices |
| Per-camera ByteTrack | Cross-camera re-ID (OSNet/BoT) |
| Rule-based anomalies | Baseline-aware ML anomaly service |
| Static camera polygons | Admin-configurable layout service |
| No auth on dashboard | OAuth2 / role-based access |

---

## 🗂️ Git & Media Policy

**Tracked in Git:**
- All source code, configuration, and documentation.
- Pre-generated demo analytics (`output/*.json`, `output/*.jsonl`).
- Docker and deployment files.

**Excluded from Git:**
- Raw CCTV videos (`data/**/*.mp4`) — never committed per hackathon rules.
- Full-resolution pipeline output videos (`output/output_*.mp4`).
- Model weights, caches, and virtual environments.

This keeps the repository under 10 MB while allowing any evaluator to run the full dashboard immediately after cloning.

---

## 📋 Submission Checklist

- [x] Containerized with Docker + Docker Compose
- [x] Runs out of the box (`docker compose up --build`)
- [x] Pydantic schema validation on all API responses
- [x] 15 REST API endpoints with Swagger docs
- [x] SSE real-time event stream
- [x] Live dashboard with KPIs, charts, heatmap, video, anomalies
- [x] Conversion funnel API and analytics
- [x] Queue intelligence (wait time, abandonment)
- [x] Anomaly detection with severity classification
- [x] Sales and footfall correlation
- [x] Multi-store support (ST1008 + ST1009, 8 cameras)
- [x] 10 unit tests passing
- [x] Privacy-aware design documented
- [x] Production upgrade path documented
- [x] No raw videos or datasets committed to Git

---

## 📄 License

MIT
