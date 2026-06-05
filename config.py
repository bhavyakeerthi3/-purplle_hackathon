"""
config.py — Store & Camera Zone Configuration
Place your video files inside data/store1/ and data/store2/
"""

import os

try:
    import numpy as np
except ImportError:
    np = None

# ── Base paths ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
OUTPUT_DIR  = os.path.join(BASE_DIR, "output")

try:
    os.makedirs(os.path.join(DATA_DIR, "store1"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "store2"), exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
except Exception:
    # Ignore directory creation failures in read-only filesystems (e.g. Vercel)
    pass

# ── Store configuration ───────────────────────────────────────────
# STORE_CONFIG uses numpy for polygon definitions and is only needed
# by the video processing pipeline (process_videos.py).
# The API server (server.py) only needs BASE_DIR and OUTPUT_DIR above.

def _build_store_config():
    """Build the full store/camera/zone config. Requires numpy."""
    if np is None:
        raise ImportError(
            "numpy is required for STORE_CONFIG (video pipeline). "
            "Install it with: pip install numpy"
        )
    return {
        "ST1": {
            "store_id": "ST1008",
            "cameras": {
                "CAM1": {
                    "file": os.path.join(DATA_DIR, "store1", "CAM 1 - zone.mp4"),
                    "type": "zone",
                    "zones": {
                        "left_wall_brands": {
                            "polygon": np.array([[0,0],[960,0],[960,540],[0,540]]),
                            "zone_id": "ST1008_Z01", "zone_type": "SHELF",
                            "zone_name": "Left Wall Brands", "is_revenue_zone": "Yes",
                        },
                        "foh_center": {
                            "polygon": np.array([[0,540],[960,540],[960,1080],[0,1080]]),
                            "zone_id": "ST1008_Z02", "zone_type": "DISPLAY",
                            "zone_name": "FOH Center", "is_revenue_zone": "Yes",
                        },
                    },
                },
                "CAM2": {
                    "file": os.path.join(DATA_DIR, "store1", "CAM 2 - zone.mp4"),
                    "type": "zone",
                    "zones": {
                        "right_wall_brands": {
                            "polygon": np.array([[0,0],[960,0],[960,540],[0,540]]),
                            "zone_id": "ST1008_Z03", "zone_type": "SHELF",
                            "zone_name": "Right Wall Brands", "is_revenue_zone": "Yes",
                        },
                        "makeup_unit": {
                            "polygon": np.array([[0,540],[960,540],[960,1080],[0,1080]]),
                            "zone_id": "ST1008_Z04", "zone_type": "DISPLAY",
                            "zone_name": "Makeup Unit", "is_revenue_zone": "Yes",
                        },
                    },
                },
                "CAM3": {
                    "file": os.path.join(DATA_DIR, "store1", "CAM 3 - entry.mp4"),
                    "type": "entry",
                    "zones": {
                        "entry_gate": {
                            "polygon": np.array([[600,600],[1300,600],[1300,1080],[600,1080]]),
                            "zone_id": "ST1008_Z_ENTRY", "zone_type": "ENTRY",
                            "zone_name": "Store Entry", "is_revenue_zone": "No",
                        },
                    },
                },
                "CAM5": {
                    "file": os.path.join(DATA_DIR, "store1", "CAM 5 - billing.mp4"),
                    "type": "billing",
                    "zones": {
                        "billing_queue": {
                            "polygon": np.array([[100,50],[860,50],[860,700],[100,700]]),
                            "zone_id": "ST1008_Z_BILLING", "zone_type": "BILLING",
                            "zone_name": "Billing Counter Queue", "is_revenue_zone": "Yes",
                        },
                    },
                },
            },
        },
        "ST2": {
            "store_id": "ST1009",
            "cameras": {
                "CAM1": {
                    "file": os.path.join(DATA_DIR, "store2", "zone.mp4"),
                    "type": "zone",
                    "zones": {
                        "main_zone": {
                            "polygon": np.array([[0,0],[1920,0],[1920,540],[0,540]]),
                            "zone_id": "ST1009_Z01", "zone_type": "SHELF",
                            "zone_name": "Main Zone", "is_revenue_zone": "Yes",
                        },
                        "gondola_area": {
                            "polygon": np.array([[0,540],[1920,540],[1920,1080],[0,1080]]),
                            "zone_id": "ST1009_Z02", "zone_type": "DISPLAY",
                            "zone_name": "Gondola Area", "is_revenue_zone": "Yes",
                        },
                    },
                },
                "CAM_E1": {
                    "file": os.path.join(DATA_DIR, "store2", "entry 1.mp4"),
                    "type": "entry",
                    "zones": {
                        "entry_left": {
                            "polygon": np.array([[0,400],[960,400],[960,1080],[0,1080]]),
                            "zone_id": "ST1009_Z_ENTRY1", "zone_type": "ENTRY",
                            "zone_name": "Entry Left", "is_revenue_zone": "No",
                        },
                    },
                },
                "CAM_E2": {
                    "file": os.path.join(DATA_DIR, "store2", "entry 2.mp4"),
                    "type": "entry",
                    "zones": {
                        "entry_right": {
                            "polygon": np.array([[0,400],[960,400],[960,1080],[0,1080]]),
                            "zone_id": "ST1009_Z_ENTRY2", "zone_type": "ENTRY",
                            "zone_name": "Entry Right", "is_revenue_zone": "No",
                        },
                    },
                },
                "CAM_B": {
                    "file": os.path.join(DATA_DIR, "store2", "billing_area.mp4"),
                    "type": "billing",
                    "zones": {
                        "billing_queue": {
                            "polygon": np.array([[100,50],[860,50],[860,900],[100,900]]),
                            "zone_id": "ST1009_Z_BILLING", "zone_type": "BILLING",
                            "zone_name": "Billing Counter Queue", "is_revenue_zone": "Yes",
                        },
                    },
                },
            },
        },
    }


# Build STORE_CONFIG eagerly if numpy is available, otherwise defer
STORE_CONFIG = _build_store_config() if np is not None else None

