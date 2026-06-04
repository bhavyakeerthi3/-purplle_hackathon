<![CDATA[# 🛍️ Purplle Store Intelligence System

![Python](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green) ![Docker](https://img.shields.io/badge/Docker-Ready-blue) ![YOLOv8](https://img.shields.io/badge/YOLOv8-Detection-purple) ![License](https://img.shields.io/badge/License-MIT-yellow)

> End-to-end store intelligence from CCTV footage: person detection, multi-object tracking, zone analytics, queue intelligence, anomaly detection, sales correlation, production APIs, and a live dashboard.

**🔴 Live Demo**: [View Dashboard](https://vercel-dashboard-eta-sand.vercel.app)


Built for the **Purplle Tech Challenge 2026 — Round 2**. Runs in two modes:

| Mode | Description |
|------|-------------|
| **Demo mode** | Synthetic events, sales, and anomalies — instant evaluation without videos |
| **Full pipeline** | YOLOv8 + ByteTrack processing over store CCTV videos in `data/` |

> ⚠️ Do not commit the hackathon dataset or video files. The `.gitignore` excludes local videos, generated analytics, and compressed outputs.

---

## ✨ Key Features

- 🎯 **Person Detection & Tracking** — YOLOv8 + ByteTrack for stable identity across frames
- 🗺️ **Zone-Based Analytics** — Polygon-configured zones per camera for dwell time, peak occupancy, and heatmap generation
- 🚶 **Footfall Intelligence** — Unique visitor counting from entry cameras across multiple stores
- 🕐 **Queue Analytics** — Billing queue completion, abandonment, and wait-time metrics
- ⚡ **Real-Time Anomaly Detection** — Crowd density alerts, dead zones, high dwell, queue drops
- 💰 **Sales Correlation** — Overlay POS transaction data onto visual intelligence for conversion insights
- 📊 **Live Dashboard** — Auto-refreshing KPI cards, charts, video playback, and event feed
- 🔌 **Production-Grade APIs** — FastAPI with filtering, pagination, health checks, SSE streaming, and Swagger docs
- 📝 **Event Streaming** — Append-only JSONL event log, replayable and Kafka-ready
- 🐳 **Docker-Ready** — Single-command deployment with `docker-compose`

---

## 🏗️ Architecture Diagram

```text
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ CCTV Feeds  │───▸│ YOLOv8 +     │───▸│ Event Engine │───▸│ FastAPI +    │
│ (8 cameras) │    │ ByteTrack    │    │ (JSONL)      │    │ Dashboard    │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                          │                    │                    │
                   ┌──────▾──────┐    ┌───────▾───────┐   ┌───────▾───────┐
                   │ Zone Polygon│    │ Anomaly       │   │ Swagger Docs  │
                   │ Assignment  │    │ Detection     │   │ /docs         │
                   └─────────────┘    └───────────────┘   └───────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for design trade-offs, event schema decisions, and production-readiness notes.

---

## 🐳 Docker Quick Start

```bash
docker-compose up --build
```

Then open:

- **Dashboard**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🚀 Quick Start (Local)

```bash
pip install -r requirements.txt
python generate_demo_data.py
python server.py
```

Open:

- Dashboard: http://localhost:8000/dashboard
- Swagger docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

---

## 🎬 Full Video Pipeline

Place videos in these local folders:

```text
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

Then run:

```bash
python process_videos.py
python server.py
```

Useful options:

```bash
python process_videos.py --store ST1      # Process single store
python process_videos.py --store ST2      # Process single store
python process_videos.py --skip-compress  # Skip video compression
python server.py --port 9000             # Custom port
```

---

## 📡 API Highlights

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Data readiness check |
| `GET /api/v1/store/{store_id}/overview` | Store KPI summary |
| `GET /api/v1/store/all/overview` | Combined KPI summary |
| `GET /api/v1/stores/overview` | Alias for combined KPI summary |
| `GET /api/v1/store/{store_id}/footfall` | Zone dwell analytics |
| `GET /api/v1/store/{store_id}/heatmap` | Peak and average occupancy |
| `GET /api/v1/store/{store_id}/queue` | Queue served, abandoned, wait metrics |
| `GET /api/v1/store/{store_id}/funnel` | Conversion funnel analytics |
| `GET /api/v1/store/{store_id}/demographics` | Visitor demographic breakdown |
| `GET /api/v1/sales/summary` | Revenue, order, brand summary |
| `GET /api/v1/sales/hourly` | Revenue by hour |
| `GET /api/v1/anomalies` | Detected operational anomalies |
| `GET /api/v1/events` | Paginated event log with filters |
| `GET /api/v1/events/stream` | Server-sent event replay stream |
| `GET /api/v1/schema/events` | Event contract documentation |

### 💻 curl Examples

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Store overview for ST1008
curl http://localhost:8000/api/v1/store/ST1008/overview

# Filter events by type and store
curl "http://localhost:8000/api/v1/events?store_id=ST1008&event_type=zone_entered&limit=10"

# Queue metrics
curl http://localhost:8000/api/v1/store/ST1008/queue

# Conversion funnel
curl http://localhost:8000/api/v1/store/ST1008/funnel

# All anomalies
curl http://localhost:8000/api/v1/anomalies

# Sales summary
curl http://localhost:8000/api/v1/sales/summary

# SSE event stream (real-time replay)
curl -N http://localhost:8000/api/v1/events/stream
```

---

## 📁 Project Structure

```text
config.py               Store, camera, and zone polygon configuration
process_videos.py       Detection, tracking, event generation, analytics
generate_demo_data.py   Synthetic data for evaluator-friendly demo mode
server.py               FastAPI app, dashboard serving, APIs, SSE stream
dashboard.html          Live analytics dashboard
requirements.txt        Runtime dependencies
ARCHITECTURE.md         System design and production notes
SUBMISSION.md           Concise evaluator guide
```

---

## 🔧 Production Readiness Notes

- The event log is JSONL to mimic append-only streaming and make replay/debugging easy.
- `config.py` separates business zone definitions from model inference code.
- API endpoints support filtering, pagination, health checks, and documented contracts.
- The system degrades gracefully into demo mode when videos or POS data are unavailable.
- In production, JSONL output would be replaced with Kafka/PubSub, object storage, and a time-series or analytical database.

---

<p align="center">
  Built with ❤️ for the <strong>Purplle Tech Challenge 2026</strong>
</p>
]]>
