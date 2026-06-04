# Architecture Notes

## Goal

Build a store intelligence system that converts raw CCTV footage into operational signals: footfall, zone engagement, queue health, crowding, sales context, and anomaly alerts.

## Pipeline

```text
Video input
  -> Frame sampling
  -> Person detection with YOLOv8
  -> Track association with ByteTrack
  -> Polygon-zone mapping
  -> Event emission
  -> Aggregation
  -> Anomaly detection
  -> FastAPI + dashboard
```

## Core Design Decisions

### YOLOv8 for detection

YOLOv8 is a practical hackathon choice because it is accurate enough for people detection, fast enough for local execution, and simple to run without a custom training phase. The implementation uses the COCO person class only, which keeps inference focused and reduces false positives from shelves or products.

### ByteTrack for identity continuity

Retail analytics depends on dwell time and queue duration, so frame-level detections are not enough. ByteTrack gives stable track IDs across frames and allows the pipeline to convert "person visible in frame" into "visitor spent 38 seconds in zone X".

### Polygon zones instead of hard-coded coordinates in logic

Store-specific camera geometry lives in `config.py`. The processing code only asks whether a tracked person is inside a configured polygon. This keeps the pipeline reusable when store layout, camera angle, or business zones change.

### JSONL event log

Events are written as append-only JSONL because it behaves like a simple local event stream:

- Easy to replay.
- Easy to inspect.
- Easy to replace with Kafka/PubSub later.
- Natural fit for downstream analytics and APIs.

### Demo mode

`generate_demo_data.py` exists so evaluators can validate the dashboard and APIs immediately even without downloading or committing large video files. It preserves the same event shape used by the video pipeline.

## Event Model

The system emits these event families:

- `entry` and `exit`: visitor-level lifecycle from entry cameras.
- `zone_entered` and `zone_exited`: movement through business zones.
- `queue_completed` and `queue_abandoned`: billing queue behavior.

The live API exposes the contract at:

```text
GET /api/v1/schema/events
```

## Aggregations

`process_videos.py` computes:

- Unique visitors from entry events.
- Dwell time by zone and camera.
- Peak and average occupancy by zone.
- Queue abandonment and wait time.
- Sales summaries from POS CSV when available.
- Synthetic sales fallback when POS is absent.

## Anomaly Detection

Current anomaly rules are interpretable and operational:

- High crowd density when peak people count crosses a threshold.
- High dwell time when average zone dwell is unusually high.
- Dead zones when a configured zone has no visitors.
- Queue abandonment when billing visitors leave before completion.

These rules are intentionally transparent for a challenge submission. A production version could layer statistical baselines, store-hour seasonality, and model-based anomaly scoring on top.

## API Layer

FastAPI exposes:

- Health/readiness.
- Store overview.
- Footfall and heatmap views.
- Queue metrics.
- Sales summaries.
- Event filtering and pagination.
- Server-sent event replay stream.
- Event schema documentation.

Swagger is available at `/docs`.

## Production Upgrade Path

| Current local implementation | Production equivalent |
| --- | --- |
| JSONL event file | Kafka / PubSub / Kinesis |
| Local output JSON | Redis + OLAP store |
| Local MP4 files | Object storage + CDN |
| Single FastAPI process | Containerized API service |
| Rule-based anomalies | Baseline-aware anomaly service |
| Static camera polygons | Admin-configurable store layout service |

## Cross-Camera Re-Identification

In the current implementation, each camera tracks visitors independently using ByteTrack. A person walking from Camera 1 (entry) to Camera 3 (zone) is assigned separate track IDs, which may lead to double-counting in multi-camera zones.

**Production approach:** A re-identification model such as **OSNet** or **BoT (Bag of Tricks)** would extract appearance embeddings from each tracked person and match them across camera views. This enables:

- **De-duplication** — A visitor counted at the entry camera is recognized in the zone camera, yielding accurate unique visitor counts.
- **Cross-camera journey mapping** — Full path reconstruction: entry → zone A → zone B → billing → exit.
- **Reduced over-counting** — Especially important in stores with overlapping camera fields of view.

The matching pipeline would work as follows:

```text
Track crop (per camera)
  → Appearance embedding (OSNet / BoT)
  → Cross-camera gallery matching (cosine similarity)
  → Unified global track ID assignment
```

For the hackathon scope, per-camera tracking is sufficient to demonstrate the pipeline architecture and analytics capability.

---

## Conversion Funnel Design

The system models a **retail conversion funnel** to compute store-level conversion rates:

```text
  Entry (counted at entry cameras)
    │
    ▼
  Zone Browsing (zone_entered / zone_exited events)
    │
    ▼
  Billing Queue (queue event start)
    │
    ▼
  Purchase Completion (queue_completed event)
```

At each stage, the system computes:

| Metric | Calculation |
|--------|-------------|
| **Browse rate** | Visitors who entered ≥1 zone / Total entries |
| **Queue intent rate** | Visitors who joined billing queue / Total entries |
| **Conversion rate** | Completed purchases / Total entries |
| **Abandonment rate** | Queue abandoned / Queue started |

This funnel is exposed via `GET /api/v1/store/{store_id}/funnel` and enables store managers to identify exactly where visitors drop off, powering targeted layout and staffing decisions.

---

## Demographic Inference

In the hackathon scope, demographics are **mocked** to demonstrate the API contract and dashboard integration. The system returns plausible age-group and gender distributions per store.

**Production implementation** would use face analysis models (e.g., InsightFace, DeepFace) with the following privacy safeguards:

- **Local-only inference** — All analysis runs on-device or on-premise; no frames leave the network.
- **No PII storage** — Only aggregated demographic counts are persisted (e.g., "12 visitors in 25–34 age group"), never individual face data.
- **Configurable opt-out** — Demographic inference can be disabled per store or camera without affecting the rest of the pipeline.
- **Consent compliance** — Designed for jurisdictions where aggregate analytics from security footage are permitted.

The demographic API is available at `GET /api/v1/store/{store_id}/demographics`.

---

## Schema Validation

All API responses use **Pydantic models** to enforce strict contracts between the backend and any consuming frontend or service:

- Response shapes are validated at serialization time — malformed data raises errors before reaching the client.
- API documentation in Swagger (`/docs`) is auto-generated from these models, ensuring docs always match the implementation.
- Pydantic models serve as a single source of truth for field names, types, optional vs. required, and default values.

This approach prevents silent contract drift between the API and dashboard, and makes it safe to evolve the schema incrementally.

---

## Reliability Considerations

- Keep raw videos out of Git and store them as local or object-storage artifacts.
- Store normalized events separately from visual output so analytics can be replayed.
- Preserve event timestamps and camera IDs for auditability.
- Add background processing and durable queues for long-running video jobs in production.
- Add model confidence thresholds and manual calibration per camera angle.

