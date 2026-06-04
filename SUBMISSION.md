# Submission Guide

## 🚀 Quickest Way to Evaluate

```bash
git clone https://github.com/bhavyakeerthi3/-purplle_hackathon.git
cd -purplle_hackathon
docker compose up --build
```

Open:
- **Dashboard**: http://localhost:8000/dashboard
- **Swagger**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

> Demo analytics data is already in `output/` — the dashboard populates immediately with no extra steps.

---

## 🐍 Local Python Alternative

```bash
pip install -r requirements.txt
python server.py
```

Open http://localhost:8000/dashboard.

---

## 📂 What To Review

| File | What It Shows |
|---|---|
| `process_videos.py` | YOLOv8 detection, ByteTrack tracking, zone events, queue events, anomaly detection |
| `config.py` | Store/camera/zone polygon configuration |
| `server.py` | FastAPI routes, Pydantic models, SSE stream, dashboard serving |
| `dashboard.html` | Live KPI, chart, heatmap, video, event, and anomaly dashboard |
| `test_server.py` | 10 API unit tests |
| `ARCHITECTURE.md` | System design decisions and production upgrade path |

---

## 🌐 Key API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | Data readiness check |
| `GET /api/v1/store/{store_id}/overview` | Store KPI summary |
| `GET /api/v1/store/{store_id}/footfall` | Zone dwell analytics |
| `GET /api/v1/store/{store_id}/heatmap` | Peak and average occupancy |
| `GET /api/v1/store/{store_id}/queue` | Queue metrics |
| `GET /api/v1/store/{store_id}/funnel` | Conversion funnel analytics |
| `GET /api/v1/store/{store_id}/demographics` | Aggregate demographic breakdown |
| `GET /api/v1/sales/summary` | Revenue and brand summary |
| `GET /api/v1/anomalies` | Operational anomaly alerts |
| `GET /api/v1/events` | Paginated event log with filters |
| `GET /api/v1/events/stream` | SSE event replay stream |

Full interactive API docs at: http://localhost:8000/docs

---

## 💪 Strong Signals In This Build

- **End-to-end pipeline** from raw CCTV video to live dashboard — no manual steps.
- **Real event schema** — 6 event types (entry, exit, zone_entered, zone_exited, queue_completed, queue_abandoned) not just screenshots.
- **SSE event replay stream** at `/api/v1/events/stream` — queryable in real time.
- **Pydantic response models** — strict schema validation on all 15 API endpoints.
- **Dockerized deployment** — one-command `docker compose up --build` for instant setup.
- **Conversion funnel** — Entry → Browse → Queue → Purchase with per-stage drop-off rates.
- **Queue abandonment detection** — surfaces when customers leave billing without purchasing.
- **Multi-store support** — ST1008 and ST1009 with 8 cameras, switchable live in dashboard.
- **10 unit tests passing** — covers every major endpoint.
- **Privacy-aware design** — demographics are demo-mode aggregates; production safeguards documented.

---

## 📌 Important Repository Note

Raw CCTV videos and large generated media are excluded from Git per hackathon rules:
- `data/**/*.mp4` — raw footage
- `output/output_*.mp4` — full-resolution annotated clips
- `output/compressed_*.mp4` — compressed clips

Pre-generated demo analytics (`output/*.json`, `output/*.jsonl`) **are committed** so evaluators get a working dashboard immediately.

Run the pipeline locally to regenerate outputs from raw footage:
```bash
pip install -r requirements-pipeline.txt
python process_videos.py
```
