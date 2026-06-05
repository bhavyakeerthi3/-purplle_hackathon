# Design Documentation (DESIGN.md)

## 1. System Goal & Pipeline Architecture

The primary goal of **Purplle Store Intelligence** is to transform raw retail CCTV video streams into high-value operational signals: footfall counts, shelf zone engagement, queue metrics, conversion rates, and real-time anomaly alerts. 

The pipeline is structured as follows:
```text
Video input (CCTV Streams)
  ──> Frame sampling (OpenCV)
  ──> Person detection (YOLOv8)
  ──> Track association / Identity continuity (ByteTrack)
  ──> Polygon-zone intersection mapping
  ──> Real-time Event emission (JSONL stream)
  ──> Event Aggregation & Metrics calculation
  ──> Rule-based Anomaly detection
  ──> FastAPI REST & SSE layer ──> Web Dashboard
```

---

## 2. Computer Vision Pipeline

### Person Detection (YOLOv8)
The detection step uses the YOLOv8 model (`yolov8n.pt`), optimized for fast local CPU/GPU execution. Inference is restricted strictly to the COCO `person` class (Class 0) to avoid false positives (e.g., misdetecting products or mannequins as customers) and minimize processing overhead.

### Tracking and Dwell Time (ByteTrack)
ByteTrack is utilized to maintain identity across frames. Dwell time is computed by tracking unique person IDs inside bounding boxes that overlap with the store's configured layout polygons.

### Zone Assignment (Polygon Mapping)
Instead of relying on hardcoded rectangle slices, the system uses coordinate polygons mapping to specific physical shelves and aisles. The intersection is validated using ray-casting/point-in-polygon checks.

---

## 3. Event Model & JSONL Stream

The system converts raw video coordinate matches into discrete store events. These events are written in an append-only JSONL format:
- **entry** / **exit**: Visitor entering or leaving the store boundaries.
- **zone_entered** / **zone_exited**: Visitor enters or leaves a specific brand or category shelf zone.
- **queue_completed** / **queue_abandoned**: Visitor joins the billing queue, stays until checkout (completed) or drops out of the line (abandoned).

---

## 4. Operational Metrics & Anomalies

The aggregation module reads the event log stream to compute:
- **Footfall Metrics**: Unique visitors, average/peak dwell time per zone.
- **Queue Metrics**: Queue lengths, average checkout wait times, queue abandonment rates.
- **Conversion Funnel**: Calculated drop-offs across the path: `Entry ──> Zone Browsing ──> Billing Queue ──> Purchase`.
- **Anomalies**: Automatically flags operational issues such as:
  - *High Crowd Density*: When peak occupancy exceeds thresholds.
  - *High Dwell Alert*: Unusually high customer dwell time.
  - *Dead Zones*: Configured zones receiving zero traffic over an extended window.
  - *Queue Abandonment Spike*: High rates of customers leaving queue.

---

## 5. AI-Assisted Decisions Section

During the engineering phase of the **Purplle Store Intelligence** system, AI assistants (Gemini and Claude) were leveraged for critical architectural design and refactoring:

### API Response Contracts
AI was used to design clean Pydantic schemas validating all outbound REST API responses (e.g., `StoreOverview`, `FootfallResponse`, `QueueResponse`). This ensures strict typing and eliminates contract mismatch between the Python FastAPI backend and vanilla JavaScript UI.

### Optimization of Local Runtime
Initially, the FastAPI server failed to start on lightweight environments due to heavy imports (`numpy`, `pandas`, `ultralytics`) in the shared `config.py`. AI assisted in refactoring the imports by:
- Moving heavy mathematical dependencies out of `config.py`.
- Implementing **lazy loading** of `numpy` inside the store configuration parser only when active video processing runs.
- Enabling the FastAPI server (`server.py`) and demo data generator (`generate_demo_data.py`) to run instantly with a lightweight footprint.

### Conversion Funnel Logic
AI assisted in structuring the conversion logic, mapping distinct `track_id` transactions from raw coordinate sequences into sequential funnel stages (`Store Entry` -> `Zone Browsing` -> `Billing Queue` -> `Purchase`) using set operations to filter out double counts and transient tracking interruptions.
