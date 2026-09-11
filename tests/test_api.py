import unittest
from starlette.testclient import TestClient
from src.app import app

class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_get_status(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("stats", data)

    def test_get_ipos(self):
        response = self.client.get("/api/ipos")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_ipos_filter(self):
        response = self.client.get("/api/ipos?status=open")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_ipos_date_sorting(self):
        response = self.client.get("/api/ipos?status=open&sort=date")
        self.assertEqual(response.status_code, 200)
        ipos = response.json()
        if len(ipos) >= 2:
            d1 = ipos[0].get("close_date") or "9999"
            d2 = ipos[1].get("close_date") or "9999"
            self.assertLessEqual(d1, d2)

    def test_html_endpoints(self):
        # Root path
        r_root = self.client.get("/")
        self.assertEqual(r_root.status_code, 200)
        self.assertIn("IPO Advisor", r_root.text)

        r_index = self.client.get("/index.html")
        self.assertEqual(r_index.status_code, 200)
        self.assertIn("IPO Advisor", r_index.text)

    def test_standalone_endpoints(self):
        from api.ipos import app as ipos_app
        from api.status import app as status_app
        from api.refresh import app as refresh_app

        ipos_client = TestClient(ipos_app)
        r_ipos = ipos_client.get("/api/ipos")
        self.assertEqual(r_ipos.status_code, 200)
        self.assertIsInstance(r_ipos.json(), list)

        status_client = TestClient(status_app)
        r_status = status_client.get("/api/status")
        self.assertEqual(r_status.status_code, 200)
        self.assertIn("status", r_status.json())

        refresh_client = TestClient(refresh_app)
        r_refresh = refresh_client.post("/api/refresh")
        self.assertEqual(r_refresh.status_code, 200)

    def test_route_aliases(self):
        # Without /api prefix
        r_ipos = self.client.get("/ipos")
        self.assertEqual(r_ipos.status_code, 200)
        self.assertIsInstance(r_ipos.json(), list)

        r_status = self.client.get("/status")
        self.assertEqual(r_status.status_code, 200)
        self.assertIn("status", r_status.json())

if __name__ == "__main__":
    unittest.main()
