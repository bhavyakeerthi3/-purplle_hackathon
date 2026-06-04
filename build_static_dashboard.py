"""
build_static_dashboard.py — Automatically compiles the static dashboard for Vercel
by baking the generated JSON files directly into vercel-dashboard/index.html.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DASHBOARD_SRC = os.path.join(BASE_DIR, "dashboard.html")
DEST_DIR = os.path.join(BASE_DIR, "vercel-dashboard")
DEST_HTML = os.path.join(DEST_DIR, "index.html")
DEST_VERCEL = os.path.join(DEST_DIR, "vercel.json")

def load_json_or_default(filename, default):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: {filename} not found, using empty default.")
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return default

def load_jsonl_or_default(filename, limit=200):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: {filename} not found, using empty events list.")
        return []
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
    return events[:limit]

def main():
    print("Compiling static dashboard...")
    os.makedirs(DEST_DIR, exist_ok=True)

    # 1. Load the mock data files
    store_analytics = load_json_or_default("store_analytics.json", {})
    sales_analytics = load_json_or_default("sales_analytics.json", {})
    anomalies = load_json_or_default("anomalies.json", [])
    events = load_jsonl_or_default("generated_events.jsonl")

    # 2. Build the fallback datasets
    # Overview payloads
    overview_ST1008 = {
        "store_id": "ST1008",
        "total_unique_visitors": len({e.get("id_token") or e.get("track_id") for e in events if e.get("event_type") == "entry" and (e.get("store_id") == "ST1008" or e.get("store_code") == "ST1008")}),
        "total_revenue": sales_analytics.get("total_revenue", 0),
        "total_orders": sales_analytics.get("total_orders", 0),
        "cameras_active": len(store_analytics.get("ST1008", {}))
    }
    overview_ST1009 = {
        "store_id": "ST1009",
        "total_unique_visitors": len({e.get("id_token") or e.get("track_id") for e in events if e.get("event_type") == "entry" and (e.get("store_id") == "ST1009" or e.get("store_code") == "ST1009")}),
        "total_revenue": sales_analytics.get("total_revenue", 0) * 0.7, # scaled for demo variety
        "total_orders": int(sales_analytics.get("total_orders", 0) * 0.7),
        "cameras_active": len(store_analytics.get("ST1009", {}))
    }

    # Queue payloads
    def calc_queue(store_id):
        q_events = [e for e in events if e.get("event_type") in ("queue_completed", "queue_abandoned") and (e.get("store_id") == store_id or e.get("store_code") == store_id)]
        completed = [e for e in q_events if e["event_type"] == "queue_completed"]
        abandoned = [e for e in q_events if e["event_type"] == "queue_abandoned"]
        wait_times = [e.get("wait_seconds", 0) for e in q_events]
        total = len(q_events) or 1
        return {
            "store_id": store_id,
            "total_served": len(completed),
            "total_abandoned": len(abandoned),
            "abandonment_rate": round(len(abandoned) / total * 100, 1),
            "avg_wait_seconds": round(sum(wait_times) / max(len(wait_times), 1), 1)
        }
    queue_ST1008 = calc_queue("ST1008")
    queue_ST1009 = calc_queue("ST1009")

    # Funnel payloads
    def calc_funnel(store_id):
        store_events = [e for e in events if e.get("store_id") == store_id or e.get("store_code") == store_id]
        entries = len({e.get("id_token") or e.get("track_id") for e in store_events if e.get("event_type") == "entry"})
        browsing = len({e.get("track_id") for e in store_events if e.get("event_type") == "zone_entered"})
        queue = len({e.get("track_id") for e in store_events if e.get("event_type") in ("queue_completed", "queue_abandoned")})
        purchase = len({e.get("track_id") for e in store_events if e.get("event_type") == "queue_completed"})
        return {
            "store_id": store_id,
            "funnel": [
                {"stage": "Store Entry", "count": entries, "percentage": 100.0},
                {"stage": "Zone Browsing", "count": browsing, "percentage": round(browsing / max(entries, 1) * 100, 1)},
                {"stage": "Billing Queue", "count": queue, "percentage": round(queue / max(entries, 1) * 100, 1)},
                {"stage": "Purchase", "count": purchase, "percentage": round(purchase / max(entries, 1) * 100, 1)}
            ],
            "conversion_rate": round(purchase / max(entries, 1) * 100, 1)
        }
    funnel_ST1008 = calc_funnel("ST1008")
    funnel_ST1009 = calc_funnel("ST1009")

    # Demographics payloads (realistic mock)
    demographics_ST1008 = {
        "store_id": "ST1008",
        "total_visitors": overview_ST1008["total_unique_visitors"],
        "gender": [
            {"label": "F", "count": int(overview_ST1008["total_unique_visitors"] * 0.63), "percentage": 63.0},
            {"label": "M", "count": int(overview_ST1008["total_unique_visitors"] * 0.37), "percentage": 37.0}
        ],
        "age_buckets": [
            {"label": "18-24", "count": int(overview_ST1008["total_unique_visitors"] * 0.20), "percentage": 20.0},
            {"label": "25-34", "count": int(overview_ST1008["total_unique_visitors"] * 0.49), "percentage": 49.0},
            {"label": "35-44", "count": int(overview_ST1008["total_unique_visitors"] * 0.21), "percentage": 21.0},
            {"label": "45+", "count": int(overview_ST1008["total_unique_visitors"] * 0.10), "percentage": 10.0}
        ]
    }
    demographics_ST1009 = {
        "store_id": "ST1009",
        "total_visitors": overview_ST1009["total_unique_visitors"],
        "gender": [
            {"label": "F", "count": int(overview_ST1009["total_unique_visitors"] * 0.58), "percentage": 58.0},
            {"label": "M", "count": int(overview_ST1009["total_unique_visitors"] * 0.42), "percentage": 42.0}
        ],
        "age_buckets": [
            {"label": "18-24", "count": int(overview_ST1009["total_unique_visitors"] * 0.25), "percentage": 25.0},
            {"label": "25-34", "count": int(overview_ST1009["total_unique_visitors"] * 0.43), "percentage": 43.0},
            {"label": "35-44", "count": int(overview_ST1009["total_unique_visitors"] * 0.22), "percentage": 22.0},
            {"label": "45+", "count": int(overview_ST1009["total_unique_visitors"] * 0.10), "percentage": 10.0}
        ]
    }

    # Hourly and brands payloads
    hourly_payload = {"hourly": sales_analytics.get("hourly", [])}
    summary_payload = {
        "total_revenue": sales_analytics.get("total_revenue", 0),
        "total_orders": sales_analytics.get("total_orders", 0),
        "top_brands": sales_analytics.get("top_brands", [])
    }

    # Footfall and Heatmaps
    def make_footfall_heatmap(store_id):
        store_data = store_analytics.get(store_id, {})
        zones = []
        heatmap = []
        for cam_id, cam_data in store_data.items():
            for zone_name, dwell in cam_data.get("dwell", {}).items():
                zones.append({
                    "zone": zone_name,
                    "camera_id": cam_id,
                    "unique_visitors": dwell.get("unique_visitors", 0),
                    "avg_dwell_sec": dwell.get("avg_dwell_sec", 0),
                    "max_dwell_sec": dwell.get("max_dwell_sec", 0)
                })
            for zone_name, peak in cam_data.get("peak", {}).items():
                heatmap.append({
                    "zone": zone_name,
                    "camera_id": cam_id,
                    "peak_count": peak.get("peak_count", 0),
                    "avg_count": peak.get("avg_count", 0)
                })
        return {"zones": zones, "heatmap": heatmap}

    fh_ST1008 = make_footfall_heatmap("ST1008")
    fh_ST1009 = make_footfall_heatmap("ST1009")

    # Combine everything into a dictionary mapped by API endpoint paths
    mock_registry = {
        "/api/v1/health": {"ready": True, "files": {"store_analytics.json": True, "sales_analytics.json": True, "anomalies.json": True, "generated_events.jsonl": True}},
        "/api/v1/schema/events": {
            "version": "1.0",
            "description": "Normalized event contracts emitted by the CCTV intelligence pipeline.",
            "common_fields": {
                "event_type": "entry | exit | zone_entered | zone_exited | queue_completed | queue_abandoned",
                "store_id": "Canonical store code"
            },
            "event_types": {}
        },
        "/api/v1/store/all/overview": {
            "total_unique_visitors": overview_ST1008["total_unique_visitors"] + overview_ST1009["total_unique_visitors"],
            "total_revenue": overview_ST1008["total_revenue"] + overview_ST1009["total_revenue"],
            "total_orders": overview_ST1008["total_orders"] + overview_ST1009["total_orders"],
            "cameras_active": 8,
            "stores_active": 2
        },
        "/api/v1/store/ST1008/overview": overview_ST1008,
        "/api/v1/store/ST1009/overview": overview_ST1009,
        "/api/v1/sales/hourly": hourly_payload,
        "/api/v1/sales/summary": summary_payload,
        "/api/v1/anomalies": {"total": len(anomalies), "anomalies": anomalies},
        "/api/v1/store/ST1008/footfall": {"store_id": "ST1008", "zones": fh_ST1008["zones"]},
        "/api/v1/store/ST1009/footfall": {"store_id": "ST1009", "zones": fh_ST1009["zones"]},
        "/api/v1/store/ST1008/heatmap": {"store_id": "ST1008", "heatmap": fh_ST1008["heatmap"]},
        "/api/v1/store/ST1009/heatmap": {"store_id": "ST1009", "heatmap": fh_ST1009["heatmap"]},
        "/api/v1/store/ST1008/queue": queue_ST1008,
        "/api/v1/store/ST1009/queue": queue_ST1009,
        "/api/v1/store/ST1008/funnel": funnel_ST1008,
        "/api/v1/store/ST1009/funnel": funnel_ST1009,
        "/api/v1/store/ST1008/demographics": demographics_ST1008,
        "/api/v1/store/ST1009/demographics": demographics_ST1009,
        # Filtered event queues
        "/api/v1/events?event_type=queue_completed&limit=20&store_id=ST1008": {
            "total": len([e for e in events if e.get("event_type") == "queue_completed" and (e.get("store_id") == "ST1008" or e.get("store_code") == "ST1008")]),
            "events": [e for e in events if e.get("event_type") == "queue_completed" and (e.get("store_id") == "ST1008" or e.get("store_code") == "ST1008")][:20]
        },
        "/api/v1/events?event_type=queue_completed&limit=20&store_id=ST1009": {
            "total": len([e for e in events if e.get("event_type") == "queue_completed" and (e.get("store_id") == "ST1009" or e.get("store_code") == "ST1009")]),
            "events": [e for e in events if e.get("event_type") == "queue_completed" and (e.get("store_id") == "ST1009" or e.get("store_code") == "ST1009")][:20]
        },
        "/api/v1/events?limit=100": {
            "total": len(events),
            "events": events[:100]
        }
    }

    # Also register generic paths with query strings stripped
    generic_registry = {
        "/api/v1/events": {
            "total": len(events),
            "events": events[:100]
        }
    }

    # Read dashboard.html source
    with open(DASHBOARD_SRC, "r", encoding="utf-8") as f:
        html = f.read()

    # 3. Create the replacement JS for static dashboard
    # We will inject a dynamic API configuration widget in the HTML
    settings_widget = """
  <!-- STATIC CONFIGURATION WIDGET -->
  <div id="static-settings" style="position:fixed;bottom:10px;right:10px;background:rgba(45,27,71,0.95);border:1px solid rgba(151,71,212,0.4);border-radius:12px;padding:12px;z-index:99999;box-shadow:0 8px 32px rgba(0,0,0,0.4);backdrop-filter:blur(8px);width:300px;font-family:var(--f-body);color:white;display:flex;flex-direction:column;gap:8px;transition:opacity 0.3s">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span style="font-weight:600;font-size:12px;letter-spacing:0.5px;color:#F5F0FC">CONNECTIONS & DEMO</span>
      <button onclick="document.getElementById('static-settings').style.opacity='0.1'" style="background:none;border:none;color:var(--ink4);cursor:pointer;font-size:12px">×</button>
    </div>
    <div style="display:flex;flex-direction:column;gap:4px">
      <label style="font-size:10px;color:var(--ink4)">API HOST URL</label>
      <div style="display:flex;gap:6px">
        <input type="text" id="api-host-input" value="" placeholder="http://localhost:8000" style="flex:1;background:rgba(255,255,255,0.08);border:1px solid rgba(151,71,212,0.3);border-radius:6px;padding:4px 8px;font-family:var(--f-mono);font-size:11px;color:white">
        <button onclick="saveApiHost()" style="background:var(--plum);border:none;border-radius:6px;color:white;padding:4px 8px;cursor:pointer;font-size:11px;font-weight:500">Save</button>
      </div>
    </div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-top:4px">
      <span id="connection-status-badge" style="font-family:var(--f-mono);font-size:10px;padding:2px 6px;border-radius:4px;background:rgba(233,30,140,0.2);color:var(--pink2)">Offline Demo</span>
      <button onclick="testConnection()" style="background:transparent;border:1px solid rgba(255,255,255,0.2);border-radius:6px;color:white;padding:2px 8px;cursor:pointer;font-size:10px">Test Connect</button>
    </div>
  </div>
"""

    # Inject the widget before the end of the body
    html = html.replace("</body>", settings_widget + "\n</body>")

    # Now let's customize the script block to handle local mock database fetch
    old_script_start = "const API = window.location.origin;"
    new_script_start = f"""
const MOCK_REGISTRY = {json.dumps(mock_registry, indent=2)};
const GENERIC_REGISTRY = {json.dumps(generic_registry, indent=2)};

// Retrieve API from LocalStorage or default to current host
let API = localStorage.getItem('purplle_api_host') || '';
let currentStore = 'ST1008';

function getMockData(path) {{
  console.log('Serving mock data for:', path);
  if (MOCK_REGISTRY[path]) return MOCK_REGISTRY[path];
  
  // Strip query string and match generic
  const urlOnly = path.split('?')[0];
  if (MOCK_REGISTRY[urlOnly]) return MOCK_REGISTRY[urlOnly];
  if (GENERIC_REGISTRY[urlOnly]) return GENERIC_REGISTRY[urlOnly];
  
  // Fallbacks
  if (path.includes('/overview')) {{
    return path.includes('ST1009') ? MOCK_REGISTRY['/api/v1/store/ST1009/overview'] : MOCK_REGISTRY['/api/v1/store/ST1008/overview'];
  }}
  if (path.includes('/footfall')) {{
    return path.includes('ST1009') ? MOCK_REGISTRY['/api/v1/store/ST1009/footfall'] : MOCK_REGISTRY['/api/v1/store/ST1008/footfall'];
  }}
  if (path.includes('/heatmap')) {{
    return path.includes('ST1009') ? MOCK_REGISTRY['/api/v1/store/ST1009/heatmap'] : MOCK_REGISTRY['/api/v1/store/ST1008/heatmap'];
  }}
  if (path.includes('/queue')) {{
    return path.includes('ST1009') ? MOCK_REGISTRY['/api/v1/store/ST1009/queue'] : MOCK_REGISTRY['/api/v1/store/ST1008/queue'];
  }}
  if (path.includes('/funnel')) {{
    return path.includes('ST1009') ? MOCK_REGISTRY['/api/v1/store/ST1009/funnel'] : MOCK_REGISTRY['/api/v1/store/ST1008/funnel'];
  }}
  if (path.includes('/demographics')) {{
    return path.includes('ST1009') ? MOCK_REGISTRY['/api/v1/store/ST1009/demographics'] : MOCK_REGISTRY['/api/v1/store/ST1008/demographics'];
  }}
  return {{}};
}}

// Settings widget helpers
function saveApiHost() {{
  const val = document.getElementById('api-host-input').value.trim();
  if (val) {{
    localStorage.setItem('purplle_api_host', val);
    API = val;
  }} else {{
    localStorage.removeItem('purplle_api_host');
    API = '';
  }}
  loadAll();
}}

function updateConnectionBadge(isOnline) {{
  const badge = document.getElementById('connection-status-badge');
  if (isOnline) {{
    badge.textContent = 'Live Connected';
    badge.style.background = 'rgba(36, 159, 112, 0.2)';
    badge.style.color = '#249F70';
  }} else {{
    badge.textContent = 'Offline Demo';
    badge.style.background = 'rgba(233,30,140,0.2)';
    badge.style.color = 'var(--pink2)';
  }}
}}

async function testConnection() {{
  try {{
    const host = API || window.location.origin;
    const r = await fetch(host + '/api/v1/health');
    if (r.ok) {{
      const d = await r.json();
      if (d.ready) {{
        alert('Successfully connected to Purplle Store Intelligence API at ' + host);
        updateConnectionBadge(true);
        return;
      }}
    }}
    alert('Found endpoint at ' + host + ' but database files are not fully ready.');
  }} catch(e) {{
    alert('Connection failed to API host: ' + (API || 'local server') + '\\nRunning in static Demo mode.');
    updateConnectionBadge(false);
  }}
}}

// Init widget field
document.addEventListener('DOMContentLoaded', () => {{
  document.getElementById('api-host-input').value = API;
}});
"""

    html = html.replace(old_script_start, new_script_start)

    # 4. Modify apiFetch to fall back cleanly to getMockData
    old_api_fetch = """async function apiFetch(path) {
  try {
    const r = await fetch(API + path);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (err) { console.warn('API:', path, err); return null; }
}"""

    new_api_fetch = """async function apiFetch(path) {
  const host = API || window.location.origin;
  try {
    const r = await fetch(host + path);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    document.getElementById('last-refresh').style.color = '#249F70';
    document.getElementById('last-refresh').textContent = 'Live • Updated ' + new Date().toLocaleTimeString();
    updateConnectionBadge(true);
    return data;
  } catch (err) {
    console.warn('API fetch failed, returning mock fallback. Path:', path, err);
    document.getElementById('last-refresh').style.color = 'var(--pink)';
    document.getElementById('last-refresh').textContent = 'Demo Mode • Updated ' + new Date().toLocaleTimeString();
    updateConnectionBadge(false);
    return getMockData(path);
  }
}"""

    html = html.replace(old_api_fetch, new_api_fetch)

    # Write out the completed html
    with open(DEST_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Successfully generated static dashboard HTML at: {DEST_HTML}")

    # 5. Write the static vercel.json configuration
    vercel_config = {
        "version": 2,
        "cleanUrls": True,
        "routes": [
            {
                "src": "/(.*)",
                "dest": "/index.html"
            }
        ]
    }
    with open(DEST_VERCEL, "w", encoding="utf-8") as f:
        json.dump(vercel_config, f, indent=2)
    print(f"Successfully generated vercel.json static configuration at: {DEST_VERCEL}")

if __name__ == "__main__":
    main()
