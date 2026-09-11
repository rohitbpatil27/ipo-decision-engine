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

if __name__ == "__main__":
    unittest.main()
