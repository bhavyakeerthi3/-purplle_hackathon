"""
server.py — Purplle Store Intelligence API

Usage:
    python server.py                  # default port 8000
    python server.py --port 9000

Open http://localhost:8000/dashboard in your browser.
"""

import argparse
import asyncio
import json
import logging
import os
import time
from collections import Counter
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import OUTPUT_DIR, BASE_DIR

# ─────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-5s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("purplle")

# ─────────────────────────────────────────────────────────────────
# Pydantic Response Models
# ─────────────────────────────────────────────────────────────────


class HealthStatus(BaseModel):
    ready: bool
    files: Dict[str, bool]


class StoreOverview(BaseModel):
    store_id: str
    total_unique_visitors: int
    total_revenue: float
    total_orders: int
    cameras_active: int


class AllStoresOverview(BaseModel):
    total_unique_visitors: int
    total_revenue: float
    total_orders: int
    cameras_active: int
    stores_active: int


class ZoneFootfall(BaseModel):
    zone: str
    camera_id: str
    unique_visitors: int = 0
    avg_dwell_sec: float = 0
    max_dwell_sec: float = 0


class FootfallResponse(BaseModel):
    store_id: str
    zones: List[ZoneFootfall]


class HeatmapCell(BaseModel):
    zone: str
    camera_id: str
    peak_count: int = 0
    avg_count: float = 0


class HeatmapResponse(BaseModel):
    store_id: str
    heatmap: List[HeatmapCell]


class QueueResponse(BaseModel):
    store_id: str
    total_served: int
    total_abandoned: int
    abandonment_rate: float
    avg_wait_seconds: float


class SalesSummary(BaseModel):
    total_revenue: float
    total_orders: int
    top_brands: List[Dict[str, Any]]


class HourlyEntry(BaseModel):
    hour: int
    orders: int
    revenue: float


class SalesHourly(BaseModel):
    hourly: List[HourlyEntry]


class AnomalyItem(BaseModel):
    type: str
    severity: str
    message: str
    store_id: Optional[str] = None
    camera_id: Optional[str] = None
    zone: Optional[str] = None
    peak_count: Optional[int] = None
    avg_dwell_sec: Optional[float] = None
    count: Optional[int] = None


class AnomalyResponse(BaseModel):
    total: int
    anomalies: List[AnomalyItem]


class EventRecord(BaseModel):
    event_type: str
    store_id: Optional[str] = None
    store_code: Optional[str] = None
    camera_id: Optional[str] = None
    track_id: Optional[int] = None
    id_token: Optional[str] = None
    event_time: Optional[str] = None
    event_timestamp: Optional[str] = None

    class Config:
        extra = "allow"


class EventsResponse(BaseModel):
    total: int
    offset: int
    limit: int
    events: List[EventRecord]


class FunnelStage(BaseModel):
    stage: str
    count: int
    percentage: float = Field(..., description="Percentage relative to entry stage")


class FunnelResponse(BaseModel):
    store_id: str
    funnel: List[FunnelStage]
    conversion_rate: float = Field(..., description="End-to-end conversion %")


class DemographicBucket(BaseModel):
    label: str
    count: int
    percentage: float


class DemographicsResponse(BaseModel):
    store_id: str
    total_visitors: int
    gender: List[DemographicBucket]
    age_buckets: List[DemographicBucket]


class EventSchemaResponse(BaseModel):
    version: str
    description: str
    common_fields: Dict[str, str]
    event_types: Dict[str, List[str]]


# ─────────────────────────────────────────────────────────────────
# Data loading helpers
# ─────────────────────────────────────────────────────────────────

def _load(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def _load_events() -> list:
    path = os.path.join(OUTPUT_DIR, "generated_events.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def _require(data, name: str):
    if data is None:
        raise HTTPException(
            status_code=503,
            detail=f"{name} not found. Run generate_demo_data.py or process_videos.py first.",
        )
    return data


def _store_matches(event: dict, store_id: str) -> bool:
    return event.get("store_id") == store_id or event.get("store_code") == store_id


def _all_stores_overview_payload() -> dict:
    analytics = _require(_load("store_analytics.json"), "store_analytics.json")
    sales = _load("sales_analytics.json") or {}
    events = _load_events()

    entry_ids = {e["id_token"] for e in events if e.get("event_type") == "entry"}
    total_cams = sum(len(cams) for cams in analytics.values())

    return {
        "total_unique_visitors": len(entry_ids),
        "total_revenue": sales.get("total_revenue", 0),
        "total_orders": sales.get("total_orders", 0),
        "cameras_active": total_cams,
        "stores_active": len(analytics),
    }


EVENT_SCHEMA = {
    "version": "1.0",
    "description": "Normalized event contracts emitted by the CCTV intelligence pipeline.",
    "common_fields": {
        "event_type": "entry | exit | zone_entered | zone_exited | queue_completed | queue_abandoned",
        "store_id/store_code": "Canonical store code such as ST1008 or ST1009.",
        "camera_id": "Camera identifier from config.py.",
    },
    "event_types": {
        "entry": ["event_type", "id_token", "store_code", "camera_id", "event_timestamp", "is_staff"],
        "exit": ["event_type", "id_token", "store_code", "camera_id", "event_timestamp"],
        "zone_entered": [
            "event_type", "track_id", "store_id", "camera_id", "zone_id",
            "zone_name", "zone_type", "event_time", "zone_hotspot_x", "zone_hotspot_y",
        ],
        "zone_exited": [
            "event_type", "track_id", "store_id", "camera_id", "zone_id",
            "zone_name", "zone_type", "event_time",
        ],
        "queue_completed": [
            "queue_event_id", "event_type", "track_id", "store_id", "camera_id",
            "queue_join_ts", "queue_served_ts", "queue_exit_ts", "wait_seconds",
        ],
        "queue_abandoned": [
            "queue_event_id", "event_type", "track_id", "store_id", "camera_id",
            "queue_join_ts", "queue_exit_ts", "wait_seconds", "abandoned",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Purplle Store Intelligence API",
    version="1.0.0",
    description=(
        "Real-time retail analytics from computer vision. "
        "End-to-end pipeline: CCTV → YOLOv8 detection → ByteTrack tracking → "
        "Zone analytics → Anomaly detection → REST APIs + Live Dashboard."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 1)
    if request.url.path.startswith("/api/"):
        logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response


# Serve compressed videos at /videos/<filename>
if os.path.isdir(OUTPUT_DIR):
    app.mount("/videos", StaticFiles(directory=OUTPUT_DIR), name="videos")


# ─────────────────────────────────────────────────────────────────
# Root
# ─────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root(request: Request):
    base = str(request.base_url).rstrip("/")
    return {
        "service": "Purplle Store Intelligence API",
        "version": "1.0.0",
        "status": "live",
        "dashboard": f"{base}/dashboard",
        "docs": f"{base}/docs",
    }


# Serve the dashboard HTML
@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    html_path = os.path.join(BASE_DIR, "dashboard.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="dashboard.html not found")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ─────────────────────────────────────────────────────────────────
# /api/v1/health
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/health", response_model=HealthStatus, tags=["System"])
def health():
    """Check data readiness. Returns which analytics files are available."""
    files = ["store_analytics.json", "sales_analytics.json",
             "anomalies.json", "generated_events.jsonl"]
    status = {f: os.path.exists(os.path.join(OUTPUT_DIR, f)) for f in files}
    ready = all(status.values())
    return {"ready": ready, "files": status}


# ─────────────────────────────────────────────────────────────────
# /api/v1/schema/events
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/schema/events", response_model=EventSchemaResponse, tags=["Schema"])
def event_schema():
    """Event contract documentation. Describes all event types and their fields."""
    return EVENT_SCHEMA


# ─────────────────────────────────────────────────────────────────
# Store Overview
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/store/all/overview", response_model=AllStoresOverview, tags=["Overview"])
def all_stores_overview():
    """Combined KPI summary across all stores."""
    return _all_stores_overview_payload()


@app.get("/api/v1/stores/overview", response_model=AllStoresOverview, tags=["Overview"])
def stores_overview():
    """Alias for combined KPI summary."""
    return _all_stores_overview_payload()


@app.get("/api/v1/store/{store_id}/overview", response_model=StoreOverview, tags=["Overview"])
def store_overview(store_id: str):
    """Per-store KPI summary: visitors, revenue, orders, cameras."""
    analytics = _require(_load("store_analytics.json"), "store_analytics.json")
    sales = _load("sales_analytics.json") or {}
    events = _load_events()

    entry_ids = {
        e["id_token"]
        for e in events
        if e.get("event_type") == "entry"
        and _store_matches(e, store_id)
    }

    cameras_active = len(analytics.get(store_id, {}))

    return {
        "store_id": store_id,
        "total_unique_visitors": len(entry_ids),
        "total_revenue": sales.get("total_revenue", 0),
        "total_orders": sales.get("total_orders", 0),
        "cameras_active": cameras_active,
    }


# ─────────────────────────────────────────────────────────────────
# Footfall
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/store/{store_id}/footfall", response_model=FootfallResponse, tags=["Footfall"])
def store_footfall(store_id: str):
    """Zone-level dwell time analytics for a store."""
    analytics = _require(_load("store_analytics.json"), "store_analytics.json")
    store_data = analytics.get(store_id, {})

    zones = []
    for cam_id, cam_data in store_data.items():
        for zone_name, dwell in cam_data.get("dwell", {}).items():
            zones.append({
                "zone": zone_name,
                "camera_id": cam_id,
                "unique_visitors": dwell.get("unique_visitors", 0),
                "avg_dwell_sec": dwell.get("avg_dwell_sec", 0),
                "max_dwell_sec": dwell.get("max_dwell_sec", 0),
            })

    return {"store_id": store_id, "zones": zones}


# ─────────────────────────────────────────────────────────────────
# Heatmap
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/store/{store_id}/heatmap", response_model=HeatmapResponse, tags=["Footfall"])
def store_heatmap(store_id: str):
    """Peak and average occupancy by zone for heatmap visualization."""
    analytics = _require(_load("store_analytics.json"), "store_analytics.json")
    store_data = analytics.get(store_id, {})

    heatmap = []
    for cam_id, cam_data in store_data.items():
        for zone_name, peak in cam_data.get("peak", {}).items():
            heatmap.append({
                "zone": zone_name,
                "camera_id": cam_id,
                "peak_count": peak.get("peak_count", 0),
                "avg_count": peak.get("avg_count", 0),
            })

    return {"store_id": store_id, "heatmap": heatmap}


# ─────────────────────────────────────────────────────────────────
# Queue
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/store/{store_id}/queue", response_model=QueueResponse, tags=["Queue"])
def store_queue(store_id: str):
    """Billing queue metrics: served, abandoned, wait times."""
    events = _load_events()

    queue_events = [
        e for e in events
        if e.get("event_type") in ("queue_completed", "queue_abandoned")
        and _store_matches(e, store_id)
    ]

    completed = [e for e in queue_events if e["event_type"] == "queue_completed"]
    abandoned = [e for e in queue_events if e["event_type"] == "queue_abandoned"]
    wait_times = [e.get("wait_seconds", 0) for e in queue_events]

    total = len(queue_events)
    avg_wait = round(sum(wait_times) / max(len(wait_times), 1), 1)
    abandon_rate = round(len(abandoned) / max(total, 1) * 100, 1)

    return {
        "store_id": store_id,
        "total_served": len(completed),
        "total_abandoned": len(abandoned),
        "abandonment_rate": abandon_rate,
        "avg_wait_seconds": avg_wait,
    }


# ─────────────────────────────────────────────────────────────────
# Conversion Funnel  (NEW)
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/store/{store_id}/funnel", response_model=FunnelResponse, tags=["Analytics"])
def store_funnel(store_id: str):
    """
    Conversion funnel: Entry → Zone Browsing → Billing Queue → Purchase.
    Tracks how many visitors progress through each stage.
    """
    events = _load_events()
    store_events = [e for e in events if _store_matches(e, store_id)]

    # Stage 1: Entries (unique visitors)
    entry_ids = {e.get("id_token") or e.get("track_id")
                 for e in store_events if e.get("event_type") == "entry"}

    # Stage 2: Zone browsing (unique track_ids in zones)
    zone_ids = {e.get("track_id")
                for e in store_events if e.get("event_type") == "zone_entered"}

    # Stage 3: Billing queue (joined queue)
    queue_ids = {e.get("track_id")
                 for e in store_events
                 if e.get("event_type") in ("queue_completed", "queue_abandoned")}

    # Stage 4: Purchase completed
    purchase_ids = {e.get("track_id")
                    for e in store_events if e.get("event_type") == "queue_completed"}

    entry_count = len(entry_ids) or 1  # avoid division by zero
    stages = [
        {"stage": "Store Entry", "count": len(entry_ids)},
        {"stage": "Zone Browsing", "count": len(zone_ids)},
        {"stage": "Billing Queue", "count": len(queue_ids)},
        {"stage": "Purchase", "count": len(purchase_ids)},
    ]

    for s in stages:
        s["percentage"] = round(s["count"] / entry_count * 100, 1)

    conversion = round(len(purchase_ids) / entry_count * 100, 1)

    return {
        "store_id": store_id,
        "funnel": stages,
        "conversion_rate": conversion,
    }


# ─────────────────────────────────────────────────────────────────
# Demographics  (NEW)
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/store/{store_id}/demographics", response_model=DemographicsResponse, tags=["Analytics"])
def store_demographics(store_id: str):
    """
    Demo-mode aggregate demographic breakdown by gender and age bucket.
    """
    events = _load_events()
    store_events = [
        e for e in events
        if _store_matches(e, store_id) and e.get("event_type") == "entry"
    ]

    total = len(store_events) or 1

    # Gender breakdown
    gender_counts = Counter(e.get("gender_pred", "Unknown") for e in store_events)
    gender = [
        {"label": g, "count": c, "percentage": round(c / total * 100, 1)}
        for g, c in gender_counts.most_common()
    ]

    # Age bucket breakdown
    age_counts = Counter(e.get("age_bucket", "Unknown") for e in store_events)
    age_buckets = [
        {"label": a, "count": c, "percentage": round(c / total * 100, 1)}
        for a, c in age_counts.most_common()
    ]

    return {
        "store_id": store_id,
        "total_visitors": len(store_events),
        "gender": gender,
        "age_buckets": age_buckets,
    }


# ─────────────────────────────────────────────────────────────────
# Sales
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/sales/summary", response_model=SalesSummary, tags=["Sales"])
def sales_summary():
    """Revenue, order count, and top-performing brands."""
    sales = _require(_load("sales_analytics.json"), "sales_analytics.json")
    return {
        "total_revenue": sales.get("total_revenue", 0),
        "total_orders": sales.get("total_orders", 0),
        "top_brands": sales.get("top_brands", []),
    }


@app.get("/api/v1/sales/hourly", response_model=SalesHourly, tags=["Sales"])
def sales_hourly():
    """Revenue and orders broken down by hour of day."""
    sales = _require(_load("sales_analytics.json"), "sales_analytics.json")
    return {"hourly": sales.get("hourly", [])}


# ─────────────────────────────────────────────────────────────────
# Anomalies
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/anomalies", response_model=AnomalyResponse, tags=["Anomalies"])
def get_anomalies(severity: Optional[str] = Query(None, description="Filter by severity: HIGH, MEDIUM, LOW, INFO")):
    """Detected operational anomalies with optional severity filter."""
    raw = _require(_load("anomalies.json"), "anomalies.json")
    items = raw if isinstance(raw, list) else []
    if severity:
        items = [a for a in items if a.get("severity") == severity.upper()]
    return {"total": len(items), "anomalies": items}


# ─────────────────────────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/events", response_model=EventsResponse, tags=["Events"])
def get_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    store_id: Optional[str] = Query(None, description="Filter by store code"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    limit: int = Query(100, ge=1, le=5000, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """Paginated event log with filters by type, store, and camera."""
    events = _load_events()

    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    if store_id:
        events = [e for e in events if _store_matches(e, store_id)]
    if camera_id:
        events = [e for e in events if e.get("camera_id") == camera_id]

    total = len(events)
    paged = events[offset: offset + limit]

    return {"total": total, "offset": offset, "limit": limit, "events": paged}


# ─────────────────────────────────────────────────────────────────
# SSE Event Stream
# ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/events/stream", tags=["Events"])
async def stream_events(
    store_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    interval_ms: int = Query(300, ge=50, le=5000),
):
    """Server-sent event replay stream. Replays stored events at configurable speed."""
    events = _load_events()
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    if store_id:
        events = [e for e in events if _store_matches(e, store_id)]
    events = events[:limit]

    async def event_generator():
        for event in events:
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(interval_ms / 1000)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    print(f"""
+------------------------------------------------------+
|        Purplle Store Intelligence  v1.0.0            |
+------------------------------------------------------+
|  Dashboard  ->  http://{args.host}:{args.port}/dashboard
|  API Docs   ->  http://{args.host}:{args.port}/docs
|  Health     ->  http://{args.host}:{args.port}/api/v1/health
+------------------------------------------------------+
""")
    uvicorn.run("server:app", host=args.host, port=args.port, reload=True)
