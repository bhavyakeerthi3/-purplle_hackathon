"""
generate_demo_data.py — Create synthetic analytics data to test the dashboard
without needing actual video files or YOLO processing.

Usage:
    python generate_demo_data.py

This creates all required JSON/JSONL files in output/ so you can
immediately run:  python server.py  and see the full dashboard.
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

random.seed(42)

# ─── Helpers ─────────────────────────────────────────────────────

def ts(base, offset_sec):
    return (base + timedelta(seconds=offset_sec)).isoformat()

BASE = datetime(2026, 4, 10, 18, 10, 0)

STORE_ZONES = {
    "ST1008": {
        "CAM1": [
            {"zone_id": "ST1008_Z01", "zone_name": "Left Wall Brands", "zone_type": "SHELF", "is_revenue_zone": "Yes"},
            {"zone_id": "ST1008_Z02", "zone_name": "FOH Center", "zone_type": "DISPLAY", "is_revenue_zone": "Yes"},
        ],
        "CAM2": [
            {"zone_id": "ST1008_Z03", "zone_name": "Right Wall Brands", "zone_type": "SHELF", "is_revenue_zone": "Yes"},
            {"zone_id": "ST1008_Z04", "zone_name": "Makeup Unit", "zone_type": "DISPLAY", "is_revenue_zone": "Yes"},
        ],
        "CAM3": [
            {"zone_id": "ST1008_Z_ENTRY", "zone_name": "Store Entry", "zone_type": "ENTRY", "is_revenue_zone": "No"},
        ],
        "CAM5": [
            {"zone_id": "ST1008_Z_BILLING", "zone_name": "Billing Counter Queue", "zone_type": "BILLING", "is_revenue_zone": "Yes"},
        ],
    },
    "ST1009": {
        "CAM1": [
            {"zone_id": "ST1009_Z01", "zone_name": "Main Zone", "zone_type": "SHELF", "is_revenue_zone": "Yes"},
            {"zone_id": "ST1009_Z02", "zone_name": "Gondola Area", "zone_type": "DISPLAY", "is_revenue_zone": "Yes"},
        ],
        "CAM_E1": [
            {"zone_id": "ST1009_Z_ENTRY1", "zone_name": "Entry Left", "zone_type": "ENTRY", "is_revenue_zone": "No"},
        ],
        "CAM_E2": [
            {"zone_id": "ST1009_Z_ENTRY2", "zone_name": "Entry Right", "zone_type": "ENTRY", "is_revenue_zone": "No"},
        ],
        "CAM_B": [
            {"zone_id": "ST1009_Z_BILLING", "zone_name": "Billing Counter Queue", "zone_type": "BILLING", "is_revenue_zone": "Yes"},
        ],
    },
}


def rand_demo():
    g = random.choice(["F", "F", "F", "M", "F", "M"])
    bucket, age = random.choice([("18-24", 21), ("25-34", 28), ("25-34", 31), ("35-44", 38), ("18-24", 22)])
    return g, age, bucket


# ─── Generate events ────────────────────────────────────────────

events = []
tid = 0

for store_id, cams in STORE_ZONES.items():
    for cam_id, zones in cams.items():
        for zone in zones:
            n_visitors = random.randint(5, 20)
            for _ in range(n_visitors):
                tid += 1
                g, age, bucket = rand_demo()
                offset = random.randint(0, 1800)

                if zone["zone_type"] == "ENTRY":
                    events.append({
                        "event_type": "entry", "id_token": f"ID_{60000+tid}",
                        "store_code": store_id, "camera_id": cam_id,
                        "event_timestamp": ts(BASE, offset),
                        "is_staff": False, "gender_pred": g, "age_pred": age,
                        "age_bucket": bucket, "is_face_hidden": False,
                        "group_id": None, "group_size": None,
                    })
                    events.append({
                        "event_type": "exit", "id_token": f"ID_{60000+tid}",
                        "store_code": store_id, "camera_id": cam_id,
                        "event_timestamp": ts(BASE, offset + random.randint(120, 600)),
                        "is_staff": False, "gender_pred": g, "age_pred": age,
                        "age_bucket": bucket, "is_face_hidden": False,
                        "group_id": None, "group_size": None,
                    })

                elif zone["zone_type"] == "BILLING":
                    dwell = random.randint(15, 180)
                    abandoned = dwell > 120
                    events.append({
                        "queue_event_id": str(uuid.uuid4()),
                        "event_type": "queue_abandoned" if abandoned else "queue_completed",
                        "track_id": tid, "store_id": store_id, "camera_id": cam_id,
                        "zone_id": zone["zone_id"], "zone_name": zone["zone_name"],
                        "zone_type": "BILLING", "is_revenue_zone": "Yes",
                        "queue_join_ts": ts(BASE, offset),
                        "queue_served_ts": None if abandoned else ts(BASE, offset + int(dwell * 0.8)),
                        "queue_exit_ts": ts(BASE, offset + dwell),
                        "wait_seconds": dwell,
                        "queue_position_at_join": random.randint(1, 6),
                        "abandoned": abandoned,
                        "zone_hotspot_x": 0.0, "zone_hotspot_y": 0.0,
                        "gender": g, "age": age, "age_bucket": bucket,
                    })

                else:
                    dwell = random.randint(5, 90)
                    events.append({
                        "event_type": "zone_entered", "track_id": tid,
                        "store_id": store_id, "camera_id": cam_id,
                        "zone_id": zone["zone_id"], "zone_name": zone["zone_name"],
                        "zone_type": zone["zone_type"], "is_revenue_zone": zone["is_revenue_zone"],
                        "event_time": ts(BASE, offset),
                        "zone_hotspot_x": round(random.uniform(100, 800), 1),
                        "zone_hotspot_y": round(random.uniform(100, 600), 1),
                        "gender": g, "age": age, "age_bucket": bucket,
                    })
                    events.append({
                        "event_type": "zone_exited", "track_id": tid,
                        "store_id": store_id, "camera_id": cam_id,
                        "zone_id": zone["zone_id"], "zone_name": zone["zone_name"],
                        "zone_type": zone["zone_type"], "is_revenue_zone": zone["is_revenue_zone"],
                        "event_time": ts(BASE, offset + dwell),
                        "zone_hotspot_x": 0.0, "zone_hotspot_y": 0.0,
                        "gender": g, "age": age, "age_bucket": bucket,
                    })

with open(os.path.join(OUTPUT_DIR, "generated_events.jsonl"), "w") as f:
    for e in events:
        f.write(json.dumps(e) + "\n")
print(f"[ok] generated_events.jsonl - {len(events)} events")


# ─── Store analytics ────────────────────────────────────────────

store_analytics = {}
for store_id, cams in STORE_ZONES.items():
    store_analytics[store_id] = {}
    for cam_id, zones in cams.items():
        dwell_data = {}
        peak_data = {}
        for zone in zones:
            key = zone["zone_name"].lower().replace(" ", "_")
            dwell_data[key] = {
                "unique_visitors": random.randint(3, 18),
                "avg_dwell_sec": round(random.uniform(8, 55), 2),
                "max_dwell_sec": round(random.uniform(30, 120), 2),
            }
            peak_data[key] = {
                "peak_count": random.randint(1, 7),
                "avg_count": round(random.uniform(0.5, 4), 2),
            }
        store_analytics[store_id][cam_id] = {"dwell": dwell_data, "peak": peak_data}

with open(os.path.join(OUTPUT_DIR, "store_analytics.json"), "w") as f:
    json.dump(store_analytics, f, indent=2)
print("[ok] store_analytics.json")


# ─── Sales analytics ────────────────────────────────────────────

brands = ["Lakme", "Maybelline", "L'Oreal", "MAC", "Nykaa", "Sugar", "Colorbar", "Faces", "Revlon", "Plum"]
hourly = [{"hour": h, "orders": random.randint(4, 22), "revenue": round(random.uniform(3000, 22000), 2)}
          for h in range(10, 22)]
top_brands = sorted(
    [{"brand_name": b, "total_amount": round(random.uniform(4000, 52000), 2)} for b in brands],
    key=lambda x: -x["total_amount"],
)
sales = {
    "total_revenue": round(sum(h["revenue"] for h in hourly), 2),
    "total_orders": sum(h["orders"] for h in hourly),
    "hourly": hourly,
    "top_brands": top_brands,
}

with open(os.path.join(OUTPUT_DIR, "sales_analytics.json"), "w") as f:
    json.dump(sales, f, indent=2)
print(f"[ok] sales_analytics.json - INR {sales['total_revenue']:,.0f}")


# ─── Anomalies ──────────────────────────────────────────────────

anomalies = []
for store_id, cams in store_analytics.items():
    for cam_id, analytics in cams.items():
        for zone, peak in analytics.get("peak", {}).items():
            if peak["peak_count"] >= 4:
                anomalies.append({
                    "type": "HIGH_CROWD_DENSITY",
                    "severity": "HIGH" if peak["peak_count"] >= 5 else "MEDIUM",
                    "store_id": store_id, "camera_id": cam_id, "zone": zone,
                    "peak_count": peak["peak_count"],
                    "message": f"Peak {peak['peak_count']} people in {zone}",
                })
        for zone, dwell in analytics.get("dwell", {}).items():
            if dwell["avg_dwell_sec"] > 45:
                anomalies.append({
                    "type": "HIGH_DWELL_TIME", "severity": "INFO",
                    "store_id": store_id, "camera_id": cam_id, "zone": zone,
                    "avg_dwell_sec": dwell["avg_dwell_sec"],
                    "message": f"High avg dwell {dwell['avg_dwell_sec']}s in {zone}",
                })

abandoned_count = len([e for e in events if e.get("event_type") == "queue_abandoned"])
if abandoned_count:
    anomalies.append({
        "type": "QUEUE_ABANDONMENT", "severity": "HIGH",
        "count": abandoned_count,
        "message": f"{abandoned_count} customers abandoned billing queue",
    })

with open(os.path.join(OUTPUT_DIR, "anomalies.json"), "w") as f:
    json.dump(anomalies, f, indent=2)
print(f"[ok] anomalies.json - {len(anomalies)} anomalies")

print("\nDemo data ready. Run: python server.py")
