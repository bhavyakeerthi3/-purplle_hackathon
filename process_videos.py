"""
process_videos.py — YOLO tracking pipeline (replaces Colab Cells 7–9)

Usage:
    python process_videos.py
    python process_videos.py --store ST1        # process one store only
    python process_videos.py --pos data/pos.csv # custom POS file path

Outputs written to output/:
    generated_events.jsonl
    store_analytics.json
    sales_analytics.json
    anomalies.json
    output_<store>_<cam>.mp4       (annotated full-res)
    compressed_<store>_<cam>.mp4   (web-ready 640px)
"""

import cv2
import json
import uuid
import glob
import argparse
import subprocess
import numpy as np
import os
import pandas as pd
from ultralytics import YOLO
import supervision as sv
from collections import defaultdict
from datetime import datetime, timedelta
import random

from config import STORE_CONFIG, OUTPUT_DIR, DATA_DIR

# ── Constants ─────────────────────────────────────────────────────
SAMPLE_EVERY = 3
BASE_TS      = datetime(2026, 4, 10, 18, 10, 0)

model = YOLO("yolov8n.pt")  # downloads on first run


# ── Helpers ───────────────────────────────────────────────────────

def mock_demographics():
    genders = ["F", "F", "F", "M", "F", "M"]
    buckets = [("18-24", 21), ("25-34", 28), ("25-34", 31), ("35-44", 38), ("18-24", 22)]
    g = random.choice(genders)
    bucket, age = random.choice(buckets)
    return g, age, bucket


# ── Core per-camera processor ─────────────────────────────────────

def process_camera(store_id: str, cam_id: str, cam_config: dict, base_ts: datetime):
    filename = cam_config["file"]
    cam_type = cam_config["type"]
    zones    = cam_config["zones"]

    if not os.path.exists(filename):
        print(f"  [warn] {filename} not found - skipping")
        return [], {}

    print(f"  [video] {cam_id} ({os.path.basename(filename)})...", end=" ", flush=True)

    zone_objects = {
        name: sv.PolygonZone(polygon=z["polygon"])
        for name, z in zones.items()
    }

    tracker   = sv.ByteTrack()
    box_ann   = sv.BoxAnnotator()
    label_ann = sv.LabelAnnotator()

    track_first_seen   = {}
    track_demographics = {}
    track_zone_entry   = {}
    zone_dwell         = defaultdict(lambda: defaultdict(int))
    zone_counts        = defaultdict(list)
    queue_join_info    = {}
    queue_position     = 0

    cap   = cv2.VideoCapture(filename)
    fps   = cap.get(cv2.CAP_PROP_FPS) or 25
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out_path = os.path.join(OUTPUT_DIR, f"output_{store_id}_{cam_id}.mp4")
    out = cv2.VideoWriter(
        out_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps, (w, h),
    )

    events    = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        ts     = base_ts + timedelta(seconds=frame_idx / fps)
        ts_str = ts.isoformat()

        if frame_idx % SAMPLE_EVERY != 0:
            out.write(frame)
            continue

        results    = model(frame, classes=[0], verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)
        detections = tracker.update_with_detections(detections)

        current_ids = set()
        if detections.tracker_id is not None:
            current_ids = set(detections.tracker_id.tolist())

        # ── New person → entry event ──────────────────────────────
        for tid in current_ids:
            if tid not in track_first_seen:
                track_first_seen[tid] = ts_str
                g, age, bucket = mock_demographics()
                track_demographics[tid] = (g, age, bucket)
                if cam_type == "entry":
                    events.append({
                        "event_type":      "entry",
                        "id_token":        f"ID_{60000 + tid}",
                        "store_code":      store_id,
                        "camera_id":       cam_id,
                        "event_timestamp": ts_str,
                        "is_staff":        False,
                        "gender_pred":     g,
                        "age_pred":        age,
                        "age_bucket":      bucket,
                        "is_face_hidden":  False,
                        "group_id":        None,
                        "group_size":      None,
                    })

        # ── Person gone → exit event ──────────────────────────────
        gone_ids = set(track_first_seen.keys()) - current_ids
        for tid in list(gone_ids):
            if cam_type == "entry" and tid in track_demographics:
                g, age, bucket = track_demographics[tid]
                events.append({
                    "event_type":      "exit",
                    "id_token":        f"ID_{60000 + tid}",
                    "store_code":      store_id,
                    "camera_id":       cam_id,
                    "event_timestamp": ts_str,
                    "is_staff":        False,
                    "gender_pred":     g,
                    "age_pred":        age,
                    "age_bucket":      bucket,
                    "is_face_hidden":  False,
                    "group_id":        None,
                    "group_size":      None,
                })
            del track_first_seen[tid]
            track_demographics.pop(tid, None)

        # ── Zone events ───────────────────────────────────────────
        for zone_name, zone_obj in zone_objects.items():
            zone_cfg    = zones[zone_name]
            mask        = zone_obj.trigger(detections=detections)
            ids_in_zone = set()
            if detections.tracker_id is not None:
                ids_in_zone = set(detections.tracker_id[mask].tolist())

            for tid in ids_in_zone:
                key = (tid, zone_name)
                if key not in track_zone_entry:
                    track_zone_entry[key] = ts
                    g, age, bucket = track_demographics.get(tid, mock_demographics())
                    if zone_cfg["zone_type"] == "BILLING":
                        queue_position += 1
                        queue_join_info[tid] = {
                            "join_ts": ts_str, "position": queue_position,
                            "zone_cfg": zone_cfg, "cam_id": cam_id,
                            "gender": g, "age": age, "bucket": bucket,
                        }
                    else:
                        cx, cy = 0.0, 0.0
                        if detections.tracker_id is not None:
                            id_list = detections.tracker_id.tolist()
                            if tid in id_list:
                                idx = id_list.index(tid)
                                box = detections.xyxy[idx]
                                cx  = float((box[0] + box[2]) / 2)
                                cy  = float((box[1] + box[3]) / 2)
                        events.append({
                            "event_type":      "zone_entered",
                            "track_id":        tid,
                            "store_id":        store_id,
                            "camera_id":       cam_id,
                            "zone_id":         zone_cfg["zone_id"],
                            "zone_name":       zone_cfg["zone_name"],
                            "zone_type":       zone_cfg["zone_type"],
                            "is_revenue_zone": zone_cfg["is_revenue_zone"],
                            "event_time":      ts_str,
                            "zone_hotspot_x":  round(cx, 1),
                            "zone_hotspot_y":  round(cy, 1),
                            "gender": g, "age": age, "age_bucket": bucket,
                        })
                zone_dwell[zone_name][tid] += SAMPLE_EVERY

            exited = {k for k in track_zone_entry if k[1] == zone_name and k[0] not in ids_in_zone}
            for key in exited:
                tid      = key[0]
                entry_ts = track_zone_entry.pop(key)
                dwell    = (ts - entry_ts).total_seconds()
                g, age, bucket = track_demographics.get(tid, mock_demographics())
                if zone_cfg["zone_type"] == "BILLING" and tid in queue_join_info:
                    info      = queue_join_info.pop(tid)
                    served_ts = (entry_ts + timedelta(seconds=min(dwell * 0.1, 15))).isoformat()
                    abandoned = dwell > 120
                    events.append({
                        "queue_event_id":         str(uuid.uuid4()),
                        "event_type":             "queue_abandoned" if abandoned else "queue_completed",
                        "track_id":               tid,
                        "store_id":               store_id,
                        "camera_id":              cam_id,
                        "zone_id":                zone_cfg["zone_id"],
                        "zone_name":              zone_cfg["zone_name"],
                        "zone_type":              "BILLING",
                        "is_revenue_zone":        "Yes",
                        "queue_join_ts":          info["join_ts"],
                        "queue_served_ts":        None if abandoned else served_ts,
                        "queue_exit_ts":          ts_str,
                        "wait_seconds":           round(dwell),
                        "queue_position_at_join": info["position"],
                        "abandoned":              abandoned,
                        "zone_hotspot_x":         0.0,
                        "zone_hotspot_y":         0.0,
                        "gender": g, "age": age, "age_bucket": bucket,
                    })
                else:
                    events.append({
                        "event_type":      "zone_exited",
                        "track_id":        tid,
                        "store_id":        store_id,
                        "camera_id":       cam_id,
                        "zone_id":         zone_cfg["zone_id"],
                        "zone_name":       zone_cfg["zone_name"],
                        "zone_type":       zone_cfg["zone_type"],
                        "is_revenue_zone": zone_cfg["is_revenue_zone"],
                        "event_time":      ts_str,
                        "zone_hotspot_x":  0.0,
                        "zone_hotspot_y":  0.0,
                        "gender": g, "age": age, "age_bucket": bucket,
                    })

            zone_counts[zone_name].append({"timestamp": round(frame_idx / fps, 2), "count": len(ids_in_zone)})

        # ── Annotate frame ────────────────────────────────────────
        labels = [f"ID:{t}" for t in detections.tracker_id] if detections.tracker_id is not None else []
        frame  = box_ann.annotate(frame, detections)
        frame  = label_ann.annotate(frame, detections, labels)
        for zone_name, z_cfg in zones.items():
            poly = z_cfg["polygon"]
            cv2.polylines(frame, [poly.astype(np.int32)], True, (0, 255, 0), 2)
            cx2, cy2 = poly.mean(axis=0).astype(int)
            cv2.putText(frame, zone_name, (max(cx2 - 60, 0), max(cy2, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        out.write(frame)

        if frame_idx % 200 == 0:
            pct = round(frame_idx / max(total, 1) * 100)
            print(f".{pct}%", end="", flush=True)

    cap.release()
    out.release()

    # ── Dwell + peak summaries ────────────────────────────────────
    dwell_summary = {}
    for zone, tracks in zone_dwell.items():
        dwell_secs = [f / fps for f in tracks.values()]
        dwell_summary[zone] = {
            "unique_visitors": len(tracks),
            "avg_dwell_sec":   round(float(np.mean(dwell_secs)), 2) if dwell_secs else 0,
            "max_dwell_sec":   round(float(max(dwell_secs)), 2)     if dwell_secs else 0,
        }

    peak_summary = {}
    for zone, frames in zone_counts.items():
        counts = [f["count"] for f in frames]
        peak_summary[zone] = {
            "peak_count": int(max(counts)) if counts else 0,
            "avg_count":  round(float(np.mean(counts)), 2) if counts else 0,
        }

    print(f" [ok] {len(events)} events")
    return events, {"dwell": dwell_summary, "peak": peak_summary}


# ── Video compression (replaces Cell 9) ──────────────────────────

def compress_videos():
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg_exe = "ffmpeg"

    for fname in os.listdir(OUTPUT_DIR):
        if fname.startswith("output_") and fname.endswith(".mp4"):
            src = os.path.join(OUTPUT_DIR, fname)
            dst = os.path.join(OUTPUT_DIR, fname.replace("output_", "compressed_"))
            if os.path.exists(dst):
                print(f"[skip] {os.path.basename(dst)} already exists, skipping")
                continue
            print(f"[compress] {fname}...")
            result = subprocess.run([
                ffmpeg_exe, "-i", src,
                "-vf", "scale=640:-2",
                "-c:v", "libx264", "-crf", "28", "-preset", "fast",
                "-c:a", "aac", "-b:a", "64k",
                "-y", dst
            ], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  [warn] ffmpeg error: {result.stderr[-200:]}")
            else:
                size = os.path.getsize(dst) // (1024 * 1024)
                print(f"  [ok] {os.path.basename(dst)} ({size} MB)")


# ── Sales & anomaly processing (replaces Cell 8) ─────────────────

def process_sales(all_events: list) -> dict:
    pos_files = (
        glob.glob(os.path.join(DATA_DIR, "**", "POS*.csv"), recursive=True)
        + glob.glob(os.path.join(DATA_DIR, "**", "pos*.csv"), recursive=True)
        + glob.glob(os.path.join(DATA_DIR, "**", "*transaction*.csv"), recursive=True)
    )
    if not pos_files:
        print("[warn] No POS CSV found in data/ - generating placeholder sales data")
        return _placeholder_sales()

    pos_file = pos_files[0]
    print(f"[sales] Using POS file: {pos_file}")
    df = pd.read_csv(pos_file)
    df["hour"] = df["order_time"].str[:2].astype(int)
    hourly = df.groupby("hour").agg(
        orders=("order_id", "nunique"),
        revenue=("total_amount", "sum"),
    ).reset_index()
    brand_perf = (
        df.groupby("brand_name")["total_amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    return {
        "total_revenue": round(float(df["total_amount"].sum()), 2),
        "total_orders":  int(df["order_id"].nunique()),
        "hourly":        hourly.to_dict(orient="records"),
        "top_brands":    brand_perf.head(10).to_dict(orient="records"),
    }


def _placeholder_sales() -> dict:
    """Synthetic sales data when no POS CSV is provided."""
    import random as r
    brands = ["Lakme", "Maybelline", "L'Oreal", "MAC", "Nykaa", "Sugar", "Colorbar", "Faces"]
    hourly = [{"hour": h, "orders": r.randint(4,18), "revenue": round(r.uniform(3000,18000),2)}
              for h in range(10, 22)]
    top_brands = sorted(
        [{"brand_name": b, "total_amount": round(r.uniform(5000, 45000), 2)} for b in brands],
        key=lambda x: -x["total_amount"],
    )
    return {
        "total_revenue": round(sum(h["revenue"] for h in hourly), 2),
        "total_orders":  sum(h["orders"] for h in hourly),
        "hourly":        hourly,
        "top_brands":    top_brands,
    }


def detect_anomalies(all_analytics: dict, all_events: list) -> list:
    anomalies = []
    for store_id, cams in all_analytics.items():
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
                if dwell["unique_visitors"] == 0:
                    anomalies.append({
                        "type": "DEAD_ZONE", "severity": "LOW",
                        "store_id": store_id, "camera_id": cam_id, "zone": zone,
                        "message": f"Zero visitors in {zone}",
                    })

    abandoned = [e for e in all_events if e.get("event_type") == "queue_abandoned"]
    if abandoned:
        anomalies.append({
            "type": "QUEUE_ABANDONMENT", "severity": "HIGH",
            "count": len(abandoned),
            "message": f"{len(abandoned)} customers abandoned billing queue",
        })
    return anomalies


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Purplle Video Analytics Pipeline")
    parser.add_argument("--store", choices=["ST1", "ST2"], default=None,
                        help="Process only one store (default: both)")
    parser.add_argument("--skip-compress", action="store_true",
                        help="Skip ffmpeg compression step")
    args = parser.parse_args()

    all_events    = []
    all_analytics = {}

    stores = {args.store: STORE_CONFIG[args.store]} if args.store else STORE_CONFIG

    for store_key, store_cfg in stores.items():
        store_id = store_cfg["store_id"]
        print(f"\n{'='*55}\nProcessing {store_key} ({store_id})\n{'='*55}")
        all_analytics[store_id] = {}
        for cam_id, cam_cfg in store_cfg["cameras"].items():
            events, analytics = process_camera(store_id, cam_id, cam_cfg, BASE_TS)
            all_events.extend(events)
            all_analytics[store_id][cam_id] = analytics

    print(f"\n\nTotal events: {len(all_events)}")
    event_types: dict = {}
    for e in all_events:
        t = e["event_type"]
        event_types[t] = event_types.get(t, 0) + 1
    print("  Breakdown:", event_types)

    # ── Save events ───────────────────────────────────────────────
    events_path = os.path.join(OUTPUT_DIR, "generated_events.jsonl")
    with open(events_path, "w") as f:
        for event in all_events:
            f.write(json.dumps(event) + "\n")
    print(f"[ok] {events_path}")

    analytics_path = os.path.join(OUTPUT_DIR, "store_analytics.json")
    with open(analytics_path, "w") as f:
        json.dump(all_analytics, f, indent=2)
    print(f"[ok] {analytics_path}")

    # ── Sales ─────────────────────────────────────────────────────
    sales_data = process_sales(all_events)
    sales_path = os.path.join(OUTPUT_DIR, "sales_analytics.json")
    with open(sales_path, "w") as f:
        json.dump(sales_data, f, indent=2)
    print(f"[ok] {sales_path} - INR {sales_data['total_revenue']:,.0f}")

    # ── Anomalies ─────────────────────────────────────────────────
    anomalies = detect_anomalies(all_analytics, all_events)
    ano_path  = os.path.join(OUTPUT_DIR, "anomalies.json")
    with open(ano_path, "w") as f:
        json.dump(anomalies, f, indent=2)
    print(f"[ok] {ano_path} - {len(anomalies)} anomalies")

    # ── Compress ──────────────────────────────────────────────────
    if not args.skip_compress:
        print("\nCompressing annotated videos...")
        compress_videos()

    print("\nPipeline complete. Run python server.py to start the dashboard.")


if __name__ == "__main__":
    main()
