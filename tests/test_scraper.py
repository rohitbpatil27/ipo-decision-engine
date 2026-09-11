import unittest
from src.scraper import IPOScraper
from src.models import StatusType

class TestScraper(unittest.TestCase):

    def setUp(self):
        self.scraper = IPOScraper()

    def test_derive_status(self):
        # Open codes
        self.assertEqual(self.scraper._derive_status("O", None, None), StatusType.OPEN)
        self.assertEqual(self.scraper._derive_status("CT", None, None), StatusType.OPEN)

        # Closed codes
        self.assertEqual(self.scraper._derive_status("C", None, None), StatusType.CLOSED)
        self.assertEqual(self.scraper._derive_status("LT", None, None), StatusType.CLOSED)

        # Listed
        self.assertEqual(self.scraper._derive_status("L", None, None), StatusType.LISTED)

        # Upcoming
        self.assertEqual(self.scraper._derive_status("U", None, None), StatusType.UPCOMING)

    def test_sme_exclusion_logic(self):
        """Ensures SME IPOs are strictly filtered out and only mainboard IPOs are retained"""
        sample_feed = [
            {"~id": 1, "~ipo_name": "Mainboard Corp Ltd", "~ipo_category1": "IPO"},
            {"~id": 2, "~ipo_name": "SME Tiny Tech Ltd", "~ipo_category1": "SME"},
            {"~id": 3, "~ipo_name": "Another Mainboard Ltd", "~ipo_category1": "IPO"},
            {"~id": 4, "~ipo_name": "SME Textiles Ltd", "~ipo_category1": "SME"}
        ]
        
        filtered = [x for x in sample_feed if str(x.get("~ipo_category1", "")).strip().upper() == "IPO"]
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["~ipo_name"], "Mainboard Corp Ltd")
        self.assertEqual(filtered[1]["~ipo_name"], "Another Mainboard Ltd")

if __name__ == "__main__":
    unittest.main()
