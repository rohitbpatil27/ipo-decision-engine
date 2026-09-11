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

        # Vercel entrypoint path
        r_vercel = self.client.get("/api/index.py")
        self.assertEqual(r_vercel.status_code, 200)
        self.assertIn("IPO Advisor", r_vercel.text)

        # Catch-all SPA path
        r_spa = self.client.get("/dashboard")
        self.assertEqual(r_spa.status_code, 200)
        self.assertIn("IPO Advisor", r_spa.text)

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
