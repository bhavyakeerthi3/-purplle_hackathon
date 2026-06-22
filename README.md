# Purplle Intelligence - Hackathon Submission

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Detection-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)



Repository name: `-purplle_hackathon`

Built for the Purplle Tech Challenge 2026 Round 2.

**Important:** raw hackathon videos and large generated media are intentionally not committed. Demo JSON/JSONL analytics are tracked so evaluators can run the API and dashboard immediately.

## What This Solves

Purplle store teams need visibility into what happens between a customer entering a store and completing a purchase. This project converts CCTV footage into structured analytics:

- How many visitors entered each store.
- Which shelves or zones attracted attention.
- Where customers spent the most time.
- How crowded each zone became.
- How many customers reached billing.
- How many customers abandoned the queue.
- How sales correlate with store traffic and hourly behavior.
- Which operational anomalies require action.

## Core Features

- YOLOv8 person detection.
- ByteTrack multi-object tracking.
- Polygon-based zone assignment per camera.
- Entry, exit, zone enter, zone exit, queue completed, and queue abandoned event generation.
- JSONL event log suitable for replay and streaming.
- Store-level analytics for 2 stores and 8 cameras.
- Dwell time, unique visitor, peak occupancy, and heatmap metrics.
- Queue wait-time and abandonment analytics.
- Conversion funnel: Store Entry -> Zone Browsing -> Billing Queue -> Purchase.
- Demo-mode demographics endpoint for aggregate gender and age buckets.
- Sales analytics with POS fallback.
- Anomaly detection for high crowd density, high dwell, dead zones, and queue abandonment.
- FastAPI REST API with Pydantic response models.
- Pagination and filtering for events.
- Server-sent event replay stream.
- Swagger API docs at `/docs`.
- Live dashboard with KPI cards, charts, heatmaps, video panels, anomalies, and event feed.
- Docker and Docker Compose support.
- Unit tests for the main API endpoints.

## Evaluation Criteria Coverage

| Requirement | Status | Implementation |
|---|---:|---|
| Containerized solution | Done | `Dockerfile`, `docker-compose.yml` |
| Runs out of the box | Done | Docker build generates demo data automatically |
| Schema-validated events | Done | Pydantic response models in `server.py` |
| REST API | Done | FastAPI endpoints under `/api/v1` |
| Dashboard | Done | `dashboard.html` |
| Event streaming | Done | `/api/v1/events/stream` SSE replay |
| Conversion funnel | Done | `/api/v1/store/{store_id}/funnel` |
| Queue analytics | Done | `/api/v1/store/{store_id}/queue` |
| Anomaly detection | Done | `/api/v1/anomalies` |
| Sales correlation | Done | `sales_analytics.json` and sales APIs |
| Documentation | Done | `README.md`, `ARCHITECTURE.md`, `SUBMISSION.md` |
| Tests | Done | `test_server.py` |

## Architecture

```text
CCTV videos
    |
    v
YOLOv8 person detection
    |
    v
ByteTrack tracking
    |
    v
Zone polygon analytics
    |
    +--> JSONL event log
    +--> Store analytics JSON
    +--> Sales analytics JSON
    +--> Anomaly JSON
    |
    v
FastAPI REST + SSE
    |
    v
Dashboard + Swagger docs
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for design trade-offs, event schema details, privacy notes, and production upgrade paths.

## Project Structure

```text
config.py                       Store, camera, and zone polygon configuration
process_videos.py               YOLOv8 + ByteTrack video processing pipeline
generate_demo_data.py           Synthetic data generator for instant demo mode
server.py                       FastAPI app, API models, routes, dashboard serving, SSE
dashboard.html                  Live local dashboard served by FastAPI
build_static_dashboard.py       Builds static Vercel dashboard package
test_server.py                  API unit tests
Dockerfile                      Multi-stage production container
docker-compose.yml              One-command local container run
requirements.txt                API/runtime dependencies
requirements-pipeline.txt       Full video pipeline dependencies
notebooks/Training_set.ipynb    Google Colab T4 training notebook for YOLO output experiments
output/                         Tracked demo analytics JSON/JSONL files
vercel-dashboard/               Static Vercel dashboard
scripts/import_demo_videos.ps1  Helper to import generated annotated videos
ARCHITECTURE.md                 System design documentation
SUBMISSION.md                   Short evaluator guide
```

## Training Notebook

`notebooks/Training_set.ipynb` documents the Google Colab T4 workflow used to train and validate the outputs for the YOLO video-processing pipeline.

## Quick Start With Docker

```bash
docker compose up --build
```

Open:

- Local dashboard: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

Stop the stack:

```bash
docker compose down
```

## Quick Start Locally

Demo analytics data is already included in the repository under `output/`, so the dashboard works immediately after cloning:

```bash
git clone https://github.com/bhavyakeerthi3/-purplle_hackathon.git
cd -purplle_hackathon
pip install -r requirements.txt
python server.py
```

Open:

- Dashboard: http://localhost:8000/dashboard
- Swagger docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

To regenerate demo data (optional):

```bash
pip install numpy
python generate_demo_data.py
```


## Full Video Pipeline

Install the pipeline dependencies:

```bash
pip install -r requirements-pipeline.txt
```

Place videos in this layout:

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

Run the pipeline:

```bash
python process_videos.py
python server.py
```

Useful options:

```bash
python process_videos.py --store ST1
python process_videos.py --store ST2
python process_videos.py --skip-compress
python server.py --port 9000
```

Pipeline outputs:

```text
output/generated_events.jsonl
output/store_analytics.json
output/sales_analytics.json
output/anomalies.json
output/output_<store>_<camera>.mp4
output/compressed_<store>_<camera>.mp4
```

## Import Already Generated YOLO Videos

If annotated videos already exist in Downloads, import them into `output/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\import_demo_videos.ps1 -Source "$env:USERPROFILE\Downloads"
```

The dashboard expects compressed clips with these names:

```text
compressed_ST1008_CAM1.mp4
compressed_ST1008_CAM2.mp4
compressed_ST1008_CAM3.mp4
compressed_ST1008_CAM5.mp4
compressed_ST1009_CAM1.mp4
compressed_ST1009_CAM_B.mp4
compressed_ST1009_CAM_E1.mp4
compressed_ST1009_CAM_E2.mp4
```

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Service metadata with dynamic dashboard/docs URLs |
| `GET /api/v1/health` | Data readiness check |
| `GET /api/v1/schema/events` | Event contract documentation |
| `GET /api/v1/store/all/overview` | Combined KPI summary |
| `GET /api/v1/stores/overview` | Alias for combined KPI summary |
| `GET /api/v1/store/{store_id}/overview` | Store KPI summary |
| `GET /api/v1/store/{store_id}/footfall` | Zone dwell analytics |
| `GET /api/v1/store/{store_id}/heatmap` | Peak and average occupancy |
| `GET /api/v1/store/{store_id}/queue` | Queue served, abandoned, and wait metrics |
| `GET /api/v1/store/{store_id}/funnel` | Conversion funnel analytics |
| `GET /api/v1/store/{store_id}/demographics` | Demo-mode aggregate demographic breakdown |
| `GET /api/v1/sales/summary` | Revenue, order, and brand summary |
| `GET /api/v1/sales/hourly` | Revenue and orders by hour |
| `GET /api/v1/anomalies` | Detected operational anomalies |
| `GET /api/v1/events` | Paginated event log with filters |
| `GET /api/v1/events/stream` | Server-sent event replay stream |

## API Examples

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/store/ST1008/overview
curl http://localhost:8000/api/v1/store/ST1008/footfall
curl http://localhost:8000/api/v1/store/ST1008/heatmap
curl http://localhost:8000/api/v1/store/ST1008/queue
curl http://localhost:8000/api/v1/store/ST1008/funnel
curl http://localhost:8000/api/v1/store/ST1008/demographics
curl http://localhost:8000/api/v1/sales/summary
curl http://localhost:8000/api/v1/anomalies
curl "http://localhost:8000/api/v1/events?store_id=ST1008&event_type=zone_entered&limit=10"
curl -N http://localhost:8000/api/v1/events/stream
```

## Event Schema

The normalized event stream supports:

- `entry`
- `exit`
- `zone_entered`
- `zone_exited`
- `queue_completed`
- `queue_abandoned`

Common fields include:

- `event_type`
- `store_id` or `store_code`
- `camera_id`
- `track_id` or `id_token`
- event timestamp fields

The API exposes the full event contract at:

```text
GET /api/v1/schema/events
```

## Dashboard

The local dashboard is served by FastAPI:

```text
http://localhost:8000/dashboard
```

Dashboard sections include:

- Overview KPIs.
- Conversion funnel.
- Demographic breakdown.
- Store footfall analytics.
- Heatmap view.
- Queue analytics.
- Sales trends.
- Anomaly timeline.
- Event feed.
- Annotated video playback when local clips are available.

## Vercel Static Dashboard

The static dashboard is in:

```text
vercel-dashboard/
```

It contains baked demo data and can run without the FastAPI backend.

Live deployment:

```text
https://vercel-dashboard-eta-sand.vercel.app
```

## Testing

Run API tests:

```bash
python -m unittest test_server.py
```

Verified locally:

```text
Ran 10 tests
OK
```

## Docker Verification

The Docker build was verified with:

```bash
docker compose build
docker compose up -d
curl http://localhost:8000/api/v1/health
docker compose down
```

Expected health response:

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

## Privacy And Responsible AI

Demographics in this hackathon build are demo-mode aggregate labels used to demonstrate the dashboard and API contract. A production deployment should:

- Use consent-aware local inference.
- Avoid storing faces or personally identifiable data.
- Persist only aggregate counts.
- Document retention and deletion policies.
- Provide store-level governance for CCTV analytics.

## Git And Media Policy

Tracked:

- Source code.
- Configuration.
- Demo JSON and JSONL analytics.
- Documentation.
- Docker and deployment files.
- Static Vercel dashboard.

Ignored:

- Raw CCTV videos in `data/`.
- Full-resolution generated videos in `output/output_*.mp4`.
- Optional compressed generated clips in `output/compressed_*.mp4`.
- Model weights and caches.
- Virtual environments and local tool caches.

This keeps the GitHub repository light and evaluator-friendly while allowing the complete video pipeline to run locally.

## Production Upgrade Path

- Replace JSONL files with Kafka, Pub/Sub, or Kinesis.
- Store analytics in Postgres, BigQuery, ClickHouse, or DuckDB.
- Move generated video artifacts to object storage.
- Add background workers for long-running video processing.
- Add authenticated dashboard access.
- Add alert routing for operational anomalies.
- Add cross-camera re-identification with privacy safeguards.
- Add observability with metrics, traces, and structured logs.

## Submission Checklist

- Dockerized solution: complete.
- Pydantic schema validation: complete.
- REST APIs: complete.
- Live dashboard: complete.
- Vercel demo: complete.
- Conversion funnel: complete.
- Demographics contract: complete.
- Tests: complete.
- Generated demo analytics: complete.
- Large videos excluded from Git: complete.

## License

MIT
