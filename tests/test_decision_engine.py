import unittest
from src.decision_engine import DecisionEngine
from src.models import DecisionType, DecisionBadgeColor, FinancialYearItem

class TestDecisionEngine(unittest.TestCase):

    def test_case_1_apply_both(self):
        """High fundamentals (>=60) + High GMP (>=20%) -> Apply Both"""
        financials = [
            FinancialYearItem(period="FY26", revenue_cr=1000.0, pat_cr=150.0, assets_cr=2000.0, net_worth_cr=1200.0),
            FinancialYearItem(period="FY25", revenue_cr=800.0, pat_cr=110.0, assets_cr=1600.0, net_worth_cr=1000.0)
        ]
        fundamentals = DecisionEngine.evaluate_fundamentals(
            roe=25.0,
            roce=28.0,
            debt_to_equity=0.2,
            pe=25.0,
            financials=financials
        )
        self.assertTrue(fundamentals.is_strong)
        self.assertGreaterEqual(fundamentals.total_score, 60.0)

        hype = DecisionEngine.evaluate_hype(
            gmp_rs=70.0,
            gmp_pct=35.0,
            price=200.0
        )
        self.assertGreaterEqual(hype.gmp_pct, 20.0)

        decision = DecisionEngine.resolve_decision(fundamentals, hype, "Alpha Corp", fresh_issue_cr=400.0, ofs_cr=100.0, ofs_ratio_pct=20.0)
        self.assertEqual(decision.verdict, DecisionType.APPLY_BOTH)
        self.assertEqual(decision.badge_color, DecisionBadgeColor.GREEN)
        self.assertIsNotNone(decision.book_wisdom)
        self.assertEqual(decision.book_wisdom.buffett_verdict, "Economic Moat Certified")
        self.assertEqual(decision.book_wisdom.lynch_verdict, "Growth Expansion Confirmed")

    def test_case_2_apply_long_term_only(self):
        """High fundamentals (>=60) + Muted GMP (<20%) -> Apply only for Long Term"""
        financials = [
            FinancialYearItem(period="FY26", revenue_cr=1200.0, pat_cr=180.0),
            FinancialYearItem(period="FY25", revenue_cr=1000.0, pat_cr=140.0)
        ]
        fundamentals = DecisionEngine.evaluate_fundamentals(
            roe=22.0,
            roce=24.0,
            debt_to_equity=0.3,
            pe=20.0,
            financials=financials
        )
        self.assertTrue(fundamentals.is_strong)

        hype = DecisionEngine.evaluate_hype(
            gmp_rs=16.0,
            gmp_pct=8.0,
            price=200.0
        )
        self.assertLess(hype.gmp_pct, 20.0)

        decision = DecisionEngine.resolve_decision(fundamentals, hype, "Beta Quality Ltd")
        self.assertEqual(decision.verdict, DecisionType.APPLY_LONG_TERM)
        self.assertEqual(decision.badge_color, DecisionBadgeColor.PURPLE)
        self.assertTrue(any("patient" in pt for pt in decision.key_points))

    def test_case_3_apply_listing_gains_only(self):
        """Weak fundamentals (<60) + Frenzied GMP (>=25%) -> Apply only for Listing Gains"""
        financials = [
            FinancialYearItem(period="FY26", revenue_cr=500.0, pat_cr=10.0),
            FinancialYearItem(period="FY25", revenue_cr=520.0, pat_cr=15.0)
        ]
        fundamentals = DecisionEngine.evaluate_fundamentals(
            roe=4.0,
            roce=5.0,
            debt_to_equity=2.1,
            pe=65.0,
            financials=financials
        )
        self.assertFalse(fundamentals.is_strong)
        self.assertLess(fundamentals.total_score, 60.0)

        hype = DecisionEngine.evaluate_hype(
            gmp_rs=45.0,
            gmp_pct=45.0,
            price=100.0
        )
        self.assertGreaterEqual(hype.gmp_pct, 25.0)

        decision = DecisionEngine.resolve_decision(fundamentals, hype, "Gamma Hype Ltd", ofs_ratio_pct=85.0)
        self.assertEqual(decision.verdict, DecisionType.APPLY_LISTING_GAINS)
        self.assertEqual(decision.badge_color, DecisionBadgeColor.AMBER)
        # Check Jay Ritter rule and Peter Lynch rule
        self.assertEqual(decision.book_wisdom.ritter_verdict, "Mandatory Day-1 Exit")
        self.assertEqual(decision.book_wisdom.lynch_verdict, "Promoter Cashout Alert")

    def test_case_4_do_not_apply(self):
        """Weak fundamentals (<60) + Weak GMP (<15%) -> Do Not Apply (Avoid)"""
        financials = [
            FinancialYearItem(period="FY26", revenue_cr=300.0, pat_cr=-20.0),
            FinancialYearItem(period="FY25", revenue_cr=350.0, pat_cr=-10.0)
        ]
        fundamentals = DecisionEngine.evaluate_fundamentals(
            roe=-5.0,
            roce=-2.0,
            debt_to_equity=2.5,
            pe=None,
            financials=financials
        )
        self.assertFalse(fundamentals.is_strong)

        hype = DecisionEngine.evaluate_hype(
            gmp_rs=2.0,
            gmp_pct=2.0,
            price=100.0
        )
        self.assertLess(hype.gmp_pct, 15.0)

        decision = DecisionEngine.resolve_decision(fundamentals, hype, "Delta Risk Ltd")
        self.assertEqual(decision.verdict, DecisionType.AVOID)
        self.assertEqual(decision.badge_color, DecisionBadgeColor.RED)
        self.assertTrue(any("Capital preservation" in pt for pt in decision.key_points))

    def test_book_wisdom_graham_valuation(self):
        """Benjamin Graham margin of safety test for high PE issues"""
        fundamentals = DecisionEngine.evaluate_fundamentals(
            roe=12.0,
            roce=11.0,
            debt_to_equity=0.5,
            pe=55.0  # Excessive PE multiple
        )
        hype = DecisionEngine.evaluate_hype(gmp_rs=10.0, gmp_pct=10.0, price=100.0)
        wisdom = DecisionEngine.evaluate_book_wisdom(fundamentals, hype)
        self.assertEqual(wisdom.graham_verdict, "Speculative Valuation")
        self.assertIn("Benjamin Graham", wisdom.graham_rationale)

    def test_calculate_allotment_chance_subscription(self):
        """Tests retail allotment probability calculation directly from subscription data"""
        # Undersubscribed -> 100% Guaranteed
        chance_under = DecisionEngine.calculate_allotment_chance(subscription_times=0.44)
        self.assertIn("100% Guaranteed", chance_under)
        self.assertIn("0.44x", chance_under)

        # Oversubscribed 10.22x -> lottery odds
        chance_over = DecisionEngine.calculate_allotment_chance(subscription_times=10.22)
        self.assertIn("~9.8% lottery", chance_over)
        self.assertIn("10.2x subscribed", chance_over)

        # Moderately subscribed 1.42x -> ~70% chance
        chance_mod = DecisionEngine.calculate_allotment_chance(subscription_times=1.42)
        self.assertIn("~70%", chance_mod)

        # Upcoming issue
        chance_up = DecisionEngine.calculate_allotment_chance(subscription_times=None, open_date="2099-01-01", status="UPCOMING")
        self.assertIn("Bidding not open yet", chance_up)

if __name__ == "__main__":
    unittest.main()
