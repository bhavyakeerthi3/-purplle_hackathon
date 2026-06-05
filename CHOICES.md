# Architecture and Design Choices (CHOICES.md)

This document details the engineering and architectural trade-offs made during the development of **Purplle Store Intelligence**.

---

## 1. Model Selection Decisions

### YOLOv8 (yolov8n) vs. Faster R-CNN / SSD
- **Choice**: YOLOv8 (specifically the Nano variant, `yolov8n.pt`).
- **Rationale**: Retail analytics require high frame-rate processing to capture fast movements or brief dwell times. YOLOv8 offers a state-of-the-art balance between inference speed (under 10ms on modern CPUs) and person detection accuracy. Single-stage object detectors like YOLOv8 are significantly faster than two-stage detectors (Faster R-CNN) and yield superior boundary localization compared to older SSD architectures.
- **Filtering**: We restrict inference exclusively to Class 0 (`person`), reducing memory allocation and ignoring potential false positives from static store elements.

### ByteTrack vs. SORT / DeepSORT
- **Choice**: ByteTrack.
- **Rationale**: Occlusion (e.g., customers blocking each other or walking behind shelves) is a major issue in busy stores. Classic SORT fails during occlusions, and DeepSORT requires running a secondary CNN feature extractor to compute appearance descriptors, which throttles GPU/CPU performance. ByteTrack solves this by utilizing association methods that match low-score detection boxes (occluded objects) instead of throwing them away. This yields continuous track IDs and highly accurate dwell-time logs.

### Cross-Camera Re-Identification (Re-ID)
- **Choice**: Per-camera tracking with global event correlation.
- **Rationale**: For this hackathon scope, we track visitors per camera. In production, a Re-ID model (e.g., OSNet) would extract visual embeddings to unify track IDs across overlapping fields of view. We document this transition path in `ARCHITECTURE.md` while keeping the local setup simple and reproducible.

---

## 2. Schema Design Decisions

### JSONL (JSON Lines) vs. SQLite/Relational DB
- **Choice**: JSONL file-based event stream.
- **Rationale**:
  1. **Append-Only Write Speed**: Writing events as flat lines of JSON is extremely fast and avoids the lock contention of SQLite during concurrent video processing streams.
  2. **Streaming Compatibility**: A JSONL file can be read sequentially line-by-line, making it incredibly simple to push to a Server-Sent Events (SSE) endpoint or integrate with tools like Apache Kafka or AWS Kinesis.
  3. **Resilience**: If the video processing pipeline crashes, the event log is not corrupted.

### Event Schema Fields
Our event schemas are strictly normalized to ensure consistency:
- **Track Identification**: `track_id` maps the session per camera.
- **Demographics**: `gender_pred` and `age_pred` represent aggregate demographic data points.
- **Location Hotspots**: `zone_hotspot_x` and `zone_hotspot_y` map pixel centers to represent where the customer stood, forming the basis for heatmaps.
- **Staff Exclusion**: `is_staff` flag is designed to exclude employee tracks (based on badge detection or dwell time thresholding) from final sales and customer conversion metrics.

---

## 3. API Architecture Decisions

### FastAPI vs. Flask/Django
- **Choice**: FastAPI.
- **Rationale**: FastAPI runs on Uvicorn (ASGI), providing native support for asynchronous tasks. This is crucial for handling multiple concurrent long-lived HTTP connections, such as the Server-Sent Events (SSE) replay stream.

### Server-Sent Events (SSE) vs. WebSockets
- **Choice**: SSE (`GET /api/v1/events/stream`).
- **Rationale**: The UI dashboard only needs to read events from the server (unidirectional data flow). WebSockets require a complex two-way handshake, custom ping/pong keep-alive logic, and are harder to scale through load balancers. SSE runs over standard HTTP, has native browser reconnection support, and is extremely lightweight for real-time dashboard updates.

### Pydantic Validation & Code Isolation
- **Choice**: Pydantic models for request/response serialization.
- **Rationale**: Setting up Pydantic models forces a strict API contract. If any database or JSON file contains malformed data, Pydantic raises an error at serialization rather than letting undefined fields pass to the frontend.
- **Dependency Separation**: Lightweight web runtime packages are isolated in `requirements.txt`, making it quick for evaluators to run the server on localhost. Heavy deep learning libraries are isolated in `requirements-pipeline.txt`.
