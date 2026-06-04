# Submission Guide

## 🔴 Live Demo

**Dashboard**: [https://vercel-dashboard-eta-sand.vercel.app](https://vercel-dashboard-eta-sand.vercel.app)


---

## 🐳 Docker Quick Start (Recommended)

```bash
docker-compose up --build
```

Then open:

- **Dashboard**: http://localhost:8000/dashboard
- **Swagger**: http://localhost:8000/docs

---

## One-Minute Demo (Local)

```bash
pip install -r requirements.txt
python generate_demo_data.py
python server.py
```

Open:

- Dashboard: http://localhost:8000/dashboard
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

---

## What To Review

1. `process_videos.py` for YOLOv8 detection, ByteTrack tracking, zone events, queue events, sales processing, and anomaly detection.
2. `config.py` for store/camera/zone configuration.
3. `server.py` for production-style APIs, filtering, pagination, health, schema docs, and SSE event streaming.
4. `dashboard.html` for live KPI, chart, video, event, and anomaly views.
5. `ARCHITECTURE.md` for design decisions and production upgrade path.

---

## Key API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Data readiness check |
| `GET /api/v1/store/{store_id}/overview` | Store KPI summary |
| `GET /api/v1/store/{store_id}/footfall` | Zone dwell analytics |
| `GET /api/v1/store/{store_id}/heatmap` | Peak and average occupancy |
| `GET /api/v1/store/{store_id}/queue` | Queue metrics |
| `GET /api/v1/store/{store_id}/funnel` | Conversion funnel analytics |
| `GET /api/v1/store/{store_id}/demographics` | Demo-mode aggregated demographic breakdown |
| `GET /api/v1/sales/summary` | Revenue and brand summary |
| `GET /api/v1/anomalies` | Operational anomaly alerts |
| `GET /api/v1/events` | Paginated event log |
| `GET /api/v1/events/stream` | SSE event replay stream |

---

## Strong Signals In This Build

- End-to-end pipeline from raw video to dashboard.
- Real event schema rather than only screenshots or charts.
- Local replayable event stream with `/api/v1/events/stream`.
- Combined and per-store intelligence APIs.
- Queue abandonment and crowding anomaly detection.
- Demo mode for reproducible evaluation without committing videos.
- **Pydantic response models** — Strict schema validation on all API responses.
- **Dockerized deployment** — One-command `docker-compose up --build` for instant setup.
- **Live Vercel demo** — Deployed dashboard accessible without local setup.
- **Conversion funnel analytics** — Entry → Browse → Queue → Purchase pipeline with drop-off rates.
- **Responsible demographics note** — Age/gender charts are mocked aggregate demo labels for the dashboard/API contract, with production privacy safeguards documented in `ARCHITECTURE.md`.

---

## Important Repository Note

The hackathon instruction says not to upload datasets or videos to GitHub. This repo excludes:

- `data/**/*.mp4`
- `output/*.mp4`
- large generated video files

Already-generated annotated clips can be restored locally with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\import_demo_videos.ps1 -Source "$env:USERPROFILE\Downloads"
```
- Python caches

Run the pipeline locally to regenerate outputs.
