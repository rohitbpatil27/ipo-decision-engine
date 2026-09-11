import unittest
import tempfile
from pathlib import Path
from src.storage import Storage
from src.models import (
    IPODetail, StatusType, FundamentalAnalysis, HypeAnalysis,
    IPODecision, DecisionType, DecisionBadgeColor
)

class TestStorage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.storage = Storage(db_path=self.db_path, auto_seed=False)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_auto_seed_on_empty_db(self):
        auto_storage = Storage(db_path=self.db_path, auto_seed=True)
        ipos = auto_storage.get_all_ipos()
        self.assertGreaterEqual(len(ipos), 15)
        stats = auto_storage.get_stats()
        self.assertGreaterEqual(stats["total_mainboard_ipos"], 15)

    def test_save_and_retrieve_ipo(self):
        ipo = IPODetail(
            id=101,
            name="Test Mainboard IPO",
            slug="/gmp/test-ipo/101/",
            category="IPO",
            status=StatusType.OPEN,
            price=150.0,
            price_band="₹150",
            lot_size=100,
            issue_size_cr="₹500 Cr",
            open_date="2026-09-10",
            close_date="2026-09-14",
            fundamentals=FundamentalAnalysis(roe=18.0, roce=20.0, total_score=75.0, is_strong=True),
            financials=[],
            hype=HypeAnalysis(gmp_rs=45.0, gmp_pct=30.0, hype_score=85.0),
            decision=IPODecision(
                verdict=DecisionType.APPLY_BOTH,
                badge_color=DecisionBadgeColor.GREEN,
                headline="Great IPO",
                key_points=["Solid numbers"],
                fundamental_summary="High quality",
                sentiment_summary="High GMP"
            ),
            updated_at="2026-09-10 12:00:00"
        )

        self.storage.save_ipo(ipo)
        all_ipos = self.storage.get_all_ipos()
        self.assertEqual(len(all_ipos), 1)
        self.assertEqual(all_ipos[0].name, "Test Mainboard IPO")
        self.assertEqual(all_ipos[0].decision.verdict, DecisionType.APPLY_BOTH)

        # Retrieve by ID
        fetched = self.storage.get_ipo_by_id(101)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, 101)

        # Retrieve stats
        stats = self.storage.get_stats()
        self.assertEqual(stats["total_mainboard_ipos"], 1)
        self.assertEqual(stats["open_count"], 1)

if __name__ == "__main__":
    unittest.main()
