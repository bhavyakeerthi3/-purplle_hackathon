"""
test_server.py — Automated Unit Tests for Purplle Store Intelligence API

Run via:
    pytest test_server.py
or:
    python -m unittest test_server.py
"""

import unittest
from fastapi.testclient import TestClient
from server import app

class TestStoreIntelligenceAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["service"], "Purplle Store Intelligence API")
        self.assertEqual(data["status"], "live")
        self.assertIn("dashboard", data)
        self.assertIn("docs", data)

    def test_health_endpoint(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("ready", data)
        self.assertIn("files", data)

    def test_event_schema_endpoint(self):
        response = self.client.get("/api/v1/schema/events")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["version"], "1.0")
        self.assertIn("common_fields", data)
        self.assertIn("event_types", data)

    def test_all_stores_overview(self):
        response = self.client.get("/api/v1/store/all/overview")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_unique_visitors", data)
        self.assertIn("total_revenue", data)
        self.assertIn("total_orders", data)
        self.assertIn("cameras_active", data)
        self.assertIn("stores_active", data)

    def test_store_overview_specific(self):
        response = self.client.get("/api/v1/store/ST1008/overview")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["store_id"], "ST1008")
        self.assertIn("total_unique_visitors", data)
        self.assertIn("total_revenue", data)

    def test_store_footfall(self):
        response = self.client.get("/api/v1/store/ST1008/footfall")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["store_id"], "ST1008")
        self.assertIn("zones", data)
        if len(data["zones"]) > 0:
            zone = data["zones"][0]
            self.assertIn("zone", zone)
            self.assertIn("camera_id", zone)
            self.assertIn("avg_dwell_sec", zone)

    def test_store_heatmap(self):
        response = self.client.get("/api/v1/store/ST1008/heatmap")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["store_id"], "ST1008")
        self.assertIn("heatmap", data)
        if len(data["heatmap"]) > 0:
            cell = data["heatmap"][0]
            self.assertIn("zone", cell)
            self.assertIn("peak_count", cell)

    def test_store_queue(self):
        response = self.client.get("/api/v1/store/ST1008/queue")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["store_id"], "ST1008")
        self.assertIn("total_served", data)
        self.assertIn("total_abandoned", data)
        self.assertIn("abandonment_rate", data)
        self.assertIn("avg_wait_seconds", data)

    def test_store_funnel(self):
        response = self.client.get("/api/v1/store/ST1008/funnel")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["store_id"], "ST1008")
        self.assertIn("funnel", data)
        self.assertIn("conversion_rate", data)
        self.assertTrue(len(data["funnel"]) > 0)
        stages = [s["stage"] for s in data["funnel"]]
        self.assertIn("Store Entry", stages)
        self.assertIn("Purchase", stages)

    def test_store_demographics(self):
        response = self.client.get("/api/v1/store/ST1008/demographics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["store_id"], "ST1008")
        self.assertIn("gender", data)
        self.assertIn("age_buckets", data)

if __name__ == "__main__":
    unittest.main()
