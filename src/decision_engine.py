import datetime
from typing import List, Optional
from src.config import (
    FUNDAMENTAL_STRONG_THRESHOLD,
    GMP_HIGH_THRESHOLD,
    GMP_VERY_HIGH_THRESHOLD,
    GMP_WEAK_THRESHOLD,
    IDEAL_ROE,
    IDEAL_ROCE,
    IDEAL_DEBT_TO_EQUITY,
    IDEAL_PE_BENCHMARK
)
from src.models import (
    DecisionType,
    DecisionBadgeColor,
    FundamentalAnalysis,
    HypeAnalysis,
    BookWisdomAnalysis,
    IPODecision,
    FinancialYearItem
)

class DecisionEngine:
    """
    Dual-Pillar IPO Decision Engine with Canonical Book Wisdom:
    Integrates audited SEBI DRHP corporate fundamentals, Grey Market Premium (GMP),
    and empirical principles from Benjamin Graham, Peter Lynch, Prof. Jay Ritter,
    Warren Buffett, and Philip Fisher.
    """

    @staticmethod
    def evaluate_fundamentals(
        roe: Optional[float] = None,
        roce: Optional[float] = None,
        debt_to_equity: Optional[float] = None,
        pe: Optional[float] = None,
        eps: Optional[float] = None,
        financials: Optional[List[FinancialYearItem]] = None
    ) -> FundamentalAnalysis:
        analysis = FundamentalAnalysis()
        analysis.roe = roe
        analysis.roce = roce
        analysis.debt_to_equity = debt_to_equity
        analysis.pe = pe
        analysis.eps = eps

        rev_growth: Optional[float] = None
        pat_growth: Optional[float] = None
        pat_margin: Optional[float] = None

        if financials and len(financials) >= 2:
            latest = financials[0]
            prev = financials[1]
            if latest.revenue_cr and prev.revenue_cr and prev.revenue_cr > 0:
                rev_growth = ((latest.revenue_cr - prev.revenue_cr) / prev.revenue_cr) * 100
            if latest.pat_cr and prev.pat_cr and prev.pat_cr > 0:
                pat_growth = ((latest.pat_cr - prev.pat_cr) / prev.pat_cr) * 100
            if latest.revenue_cr and latest.revenue_cr > 0 and latest.pat_cr is not None:
                pat_margin = (latest.pat_cr / latest.revenue_cr) * 100

        analysis.revenue_growth_yoy = rev_growth
        analysis.pat_growth_yoy = pat_growth
        analysis.pat_margin_pct = pat_margin

        # 1. Growth Score (Max 25 pts)
        growth_pts = 0.0
        if rev_growth is not None:
            if rev_growth >= 20.0:
                growth_pts = 25.0
            elif rev_growth >= 10.0:
                growth_pts = 18.0
            elif rev_growth > 0.0:
                growth_pts = 10.0
            else:
                growth_pts = 0.0
        else:
            growth_pts = 12.5

        # 2. Profitability & PAT Margins (Max 25 pts)
        prof_pts = 0.0
        if pat_growth is not None and pat_margin is not None:
            if pat_margin > 12.0 and pat_growth >= 15.0:
                prof_pts = 25.0
            elif pat_margin > 6.0 and pat_growth > 0.0:
                prof_pts = 18.0
            elif pat_margin > 0.0:
                prof_pts = 10.0
            else:
                prof_pts = 0.0
        elif pat_margin is not None:
            if pat_margin > 10.0:
                prof_pts = 20.0
            elif pat_margin > 0.0:
                prof_pts = 12.0
            else:
                prof_pts = 0.0
        else:
            prof_pts = 12.5

        # 3. Capital Efficiency (ROE & ROCE) (Max 25 pts)
        eff_pts = 0.0
        valid_roe = roe if roe is not None else 0.0
        valid_roce = roce if roce is not None else 0.0

        if valid_roe >= IDEAL_ROE and valid_roce >= IDEAL_ROCE:
            eff_pts = 25.0
        elif valid_roe >= 12.0 or valid_roce >= 12.0:
            eff_pts = 18.0
        elif valid_roe >= 8.0 or valid_roce >= 8.0:
            eff_pts = 10.0
        elif valid_roe > 0.0:
            eff_pts = 5.0
        else:
            eff_pts = 0.0

        # 4. Balance Sheet Leverage (Debt-to-Equity) (Max 15 pts)
        lev_pts = 0.0
        if debt_to_equity is not None:
            if debt_to_equity <= 0.4:
                lev_pts = 15.0
            elif debt_to_equity <= IDEAL_DEBT_TO_EQUITY:
                lev_pts = 11.0
            elif debt_to_equity <= 1.5:
                lev_pts = 6.0
            else:
                lev_pts = 0.0
        else:
            lev_pts = 8.0

        # 5. Valuation Fairness (P/E Ratio) (Max 10 pts)
        val_pts = 0.0
        if pe is not None and pe > 0:
            if pe <= 22.0:
                val_pts = 10.0
            elif pe <= IDEAL_PE_BENCHMARK:
                val_pts = 7.0
            elif pe <= 55.0:
                val_pts = 4.0
            else:
                val_pts = 0.0
        else:
            val_pts = 5.0

        total = growth_pts + prof_pts + eff_pts + lev_pts + val_pts
        analysis.growth_score = round(growth_pts, 1)
        analysis.profitability_score = round(prof_pts, 1)
        analysis.capital_efficiency_score = round(eff_pts, 1)
        analysis.leverage_score = round(lev_pts, 1)
        analysis.valuation_score = round(val_pts, 1)
        analysis.total_score = round(total, 1)
        analysis.is_strong = (total >= FUNDAMENTAL_STRONG_THRESHOLD)

        return analysis

    @staticmethod
    def evaluate_hype(
        gmp_rs: Optional[float],
        gmp_pct: Optional[float],
        price: Optional[float],
        trend: Optional[str] = "Stable",
        subscription: Optional[float] = None
    ) -> HypeAnalysis:
        hype = HypeAnalysis()
        hype.gmp_rs = gmp_rs
        hype.gmp_pct = gmp_pct
        hype.price = price
        hype.gmp_trend = trend
        hype.subscription_times = subscription

        if price and price > 0 and gmp_rs is not None:
            hype.estimated_listing_price = round(price + gmp_rs, 2)
            if gmp_pct is None:
                gmp_pct = round((gmp_rs / price) * 100, 2)
                hype.gmp_pct = gmp_pct

        pct = gmp_pct if gmp_pct is not None else 0.0

        score = 0.0
        demand = "Weak"
        if pct >= 50.0:
            score = 100.0
            demand = "Frenzied"
        elif pct >= GMP_VERY_HIGH_THRESHOLD:
            score = 85.0
            demand = "Very High"
        elif pct >= GMP_HIGH_THRESHOLD:
            score = 70.0
            demand = "High"
        elif pct >= GMP_WEAK_THRESHOLD:
            score = 50.0
            demand = "Moderate"
        elif pct >= 5.0:
            score = 30.0
            demand = "Low"
        elif pct >= 0.0:
            score = 15.0
            demand = "Flat"
        else:
            score = 0.0
            demand = "Discount Risk"

        if subscription and subscription > 10.0:
            score = min(100.0, score + 10.0)

        hype.hype_score = round(score, 1)
        hype.demand_level = demand
        return hype

    @staticmethod
    def evaluate_book_wisdom(
        fundamentals: FundamentalAnalysis,
        hype: HypeAnalysis,
        fresh_issue_cr: Optional[float] = None,
        ofs_cr: Optional[float] = None,
        ofs_ratio_pct: Optional[float] = None
    ) -> BookWisdomAnalysis:
        wisdom = BookWisdomAnalysis()
        wisdom.fresh_issue_cr = fresh_issue_cr
        wisdom.ofs_cr = ofs_cr
        wisdom.ofs_ratio_pct = ofs_ratio_pct

        # 1. Peter Lynch Insider Selling & Capital Deployment Test
        if ofs_ratio_pct is not None:
            if ofs_ratio_pct >= 70.0:
                wisdom.lynch_verdict = "Promoter Cashout Alert"
                wisdom.lynch_rationale = (
                    f"Over {ofs_ratio_pct:.0f}% of this IPO is Offer For Sale (OFS). As Peter Lynch warned in "
                    "'One Up On Wall Street', when private equity and founders cash out heavily at the offering, "
                    "less capital remains to grow the core business."
                )
            elif ofs_ratio_pct <= 35.0:
                wisdom.lynch_verdict = "Growth Expansion Confirmed"
                wisdom.lynch_rationale = (
                    f"Majority ({100 - ofs_ratio_pct:.0f}%) is Fresh Capital entering company reserves for capex and debt reduction, "
                    "meeting Lynch's classic requirement for productive business expansion."
                )
            else:
                wisdom.lynch_verdict = "Balanced Allocation"
                wisdom.lynch_rationale = "Proceeds balance secondary founder monetization with new growth equity."
        else:
            wisdom.lynch_verdict = "Standard Offering"
            wisdom.lynch_rationale = "Capital allocation breakdown pending final DRHP issue apportionment."

        # 2. Benjamin Graham Margin of Safety Test (The Intelligent Investor)
        pe = fundamentals.pe
        roe = fundamentals.roe or 0.0
        de = fundamentals.debt_to_equity or 0.0

        if pe and pe > 45.0:
            wisdom.graham_verdict = "Speculative Valuation"
            wisdom.graham_rationale = (
                f"P/E multiple of {pe}x breaches Benjamin Graham's margin of safety. Graham observed that sellers choose IPO timing "
                "to capitalize on bull-market euphoria. Without massive sustained earnings expansion, downside risk is heightened."
            )
        elif pe and pe <= 22.0 and de <= 0.8:
            wisdom.graham_verdict = "Strong Margin of Safety"
            wisdom.graham_rationale = (
                f"Attractive issue pricing at {pe}x P/E with conservative balance sheet leverage (D/E: {de}). "
                "Satisfies Graham's value requirements for defensive investors."
            )
        else:
            wisdom.graham_verdict = "Fair Market Valuation"
            wisdom.graham_rationale = f"Valuation ({pe or 'N/A'}x P/E) aligns with historical industry sector medians."

        # 3. Prof. Jay Ritter Empirical Performance & Exit Discipline
        gmp_pct = hype.gmp_pct or 0.0
        if gmp_pct >= GMP_VERY_HIGH_THRESHOLD and not fundamentals.is_strong:
            wisdom.ritter_verdict = "Mandatory Day-1 Exit"
            wisdom.ritter_rationale = (
                "Prof. Jay Ritter's 40 years of empirical IPO data shows high-pop IPOs with weak underlying financials underperform "
                "the broad market by 15-20% over 3 years. Strategy: Harvest the initial listing pop on Day 1; do NOT get trapped holding."
            )
        elif fundamentals.is_strong and gmp_pct >= GMP_HIGH_THRESHOLD:
            wisdom.ritter_verdict = "Dual Strategy Qualified"
            wisdom.ritter_rationale = (
                "Empirically rare issue combining genuine return on capital with strong first-day market liquidity. "
                "Safe for either an opening day profit-booking or multi-year wealth compounding."
            )
        else:
            wisdom.ritter_verdict = "Subdued Listing Probability"
            wisdom.ritter_rationale = (
                "Empirical data shows issues with low listing premia rarely produce significant post-listing momentum."
            )

        # 4. Warren Buffett & Charlie Munger Capital Efficiency Test
        roce = fundamentals.roce or 0.0
        if roce >= 15.0 and roe >= 15.0 and de <= 0.6:
            wisdom.buffett_verdict = "Economic Moat Certified"
            wisdom.buffett_rationale = (
                f"Generates exceptional returns on capital (ROCE: {roce}%, ROE: {roe}%) without relying on debt leverage. "
                "Satisfies Buffett & Munger's criteria for durable competitive economic moats."
            )
        elif roce > 0 and (roce < 10.0 or de > 1.2):
            wisdom.buffett_verdict = "Weak Economic Moat"
            wisdom.buffett_rationale = (
                "Sub-par capital efficiency or high debt reliance fails the Berkshire Hathaway quality screen."
            )
        else:
            wisdom.buffett_verdict = "Moderate Moat"
            wisdom.buffett_rationale = "Satisfactory return ratios consistent with standard operational cycles."

        # 5. Philip Fisher Earnings Quality Check
        if fundamentals.pat_growth_yoy and fundamentals.pat_growth_yoy > 15.0 and fundamentals.pat_margin_pct and fundamentals.pat_margin_pct > 10.0:
            wisdom.fisher_verdict = "High Growth Durability"
            wisdom.fisher_rationale = "Organic earnings acceleration and double-digit profit margins confirm Fisher-grade growth quality."
        else:
            wisdom.fisher_verdict = "Moderate Growth Durability"
            wisdom.fisher_rationale = "Growth trends require ongoing quarterly validation."

        return wisdom

    @staticmethod
    def calculate_allotment_chance(
        subscription_times: Optional[float],
        open_date: Optional[str] = None,
        close_date: Optional[str] = None,
        status: Optional[str] = None,
        gmp_pct: Optional[float] = None
    ) -> str:
        """
        Derives retail allotment probability directly from how much the IPO is subscribed.
        If subscription <= 1.0x -> 100% Guaranteed allotment.
        If subscription > 1.0x -> Probability = (100 / subscription)%, converted to odds.
        """
        if subscription_times is not None and subscription_times > 0:
            if subscription_times <= 1.0:
                return f"100% Guaranteed ({subscription_times:.2f}x subscribed)"
            
            prob = min(100.0, 100.0 / subscription_times)
            if prob >= 50.0:
                return f"~{prob:.0f}% chance (~{int(round(prob/10))} in 10 • {subscription_times:.2f}x subscribed)"
            elif prob >= 10.0:
                odds = round(subscription_times, 1)
                return f"~{prob:.0f}% chance (~1 in {odds:g} • {subscription_times:.2f}x subscribed)"
            elif prob >= 1.0:
                odds = int(round(subscription_times))
                return f"~{prob:.1f}% lottery (~1 in {odds} • {subscription_times:.1f}x subscribed)"
            else:
                odds = int(round(subscription_times))
                return f"< 1% lottery (~1 in {odds} • {subscription_times:.1f}x subscribed)"

        # When subscription is not yet recorded or '-'
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        if status == "UPCOMING" or (open_date and open_date > today_str):
            open_display = open_date[5:] if (open_date and len(open_date) >= 10) else (open_date or "soon")
            return f"Bidding not open yet (Opens {open_display})"
        elif open_date and open_date == today_str:
            return "Bidding opened today (Awaiting Day 1 tally)"
        else:
            if gmp_pct and gmp_pct >= 30.0:
                return "Competitive bidding expected (~1 in 10+ lottery)"
            elif gmp_pct and gmp_pct >= 15.0:
                return "Moderate demand expected (~1 in 3-5 chance)"
            return "Awaiting subscription tally"

    @classmethod
    def resolve_decision(
        cls,
        fundamentals: FundamentalAnalysis,
        hype: HypeAnalysis,
        company_name: str,
        fresh_issue_cr: Optional[float] = None,
        ofs_cr: Optional[float] = None,
        ofs_ratio_pct: Optional[float] = None
    ) -> IPODecision:
        f_score = fundamentals.total_score
        is_strong = fundamentals.is_strong
        gmp_pct = hype.gmp_pct if hype.gmp_pct is not None else 0.0

        # Run Book Wisdom Engine
        wisdom = cls.evaluate_book_wisdom(
            fundamentals=fundamentals,
            hype=hype,
            fresh_issue_cr=fresh_issue_cr,
            ofs_cr=ofs_cr,
            ofs_ratio_pct=ofs_ratio_pct
        )

        points = []

        f_summary = (
            f"Fundamental Health Score: {f_score}/100. "
            f"ROE: {fundamentals.roe or 'N/A'}%, ROCE: {fundamentals.roce or 'N/A'}%, "
            f"D/E: {fundamentals.debt_to_equity or 'N/A'}, P/E: {fundamentals.pe or 'N/A'}x."
        )
        h_summary = (
            f"Market Hype Score: {hype.hype_score}/100. "
            f"GMP: ₹{hype.gmp_rs or 0} ({gmp_pct}%), Demand: {hype.demand_level}."
        )

        allotment_chance = DecisionEngine.calculate_allotment_chance(
            subscription_times=hype.subscription_times,
            gmp_pct=gmp_pct
        )

        top_3 = []

        # 1. APPLY for Listing Gains as well as Long Term
        if is_strong and gmp_pct >= GMP_HIGH_THRESHOLD:
            verdict = DecisionType.APPLY_BOTH
            color = DecisionBadgeColor.GREEN
            headline = f"Strong Buy: Robust business fundamentals reinforced by high grey market demand ({gmp_pct}% GMP)."
            
            top_3 = [
                f"Superior Business Health: Scored {f_score:.0f}/100 with ROE of {fundamentals.roe or 'N/A'}% and solid balance sheet.",
                f"High Listing Buffer: {gmp_pct:.1f}% GMP provides ample margin of safety against market opening volatility.",
                "Dual Flexibility: You can pocket immediate Day-1 listing gains or comfortably retain for compound long-term wealth."
            ]

        # 2. APPLY only for Long Term
        elif is_strong and gmp_pct < GMP_HIGH_THRESHOLD:
            verdict = DecisionType.APPLY_LONG_TERM
            color = DecisionBadgeColor.PURPLE
            headline = f"Long-Term Value: High corporate quality ({f_score}/100), but muted listing buzz ({gmp_pct}% GMP)."
            
            top_3 = [
                f"Resilient Fundamentals: High-quality company ({f_score:.0f}/100) with healthy return on capital.",
                f"Fair Valuation Multiple: Sensibly priced at {fundamentals.pe or 'reasonable'}x P/E for multi-year re-rating.",
                f"Muted Listing Pop: At {gmp_pct:.1f}% GMP, do NOT apply for short-term flips; apply exclusively for patient holding."
            ]

        # 3. APPLY only for Listing Gains
        elif (not is_strong) and gmp_pct >= GMP_VERY_HIGH_THRESHOLD:
            verdict = DecisionType.APPLY_LISTING_GAINS
            color = DecisionBadgeColor.AMBER
            headline = f"Tactical Listing Flip: Market frenzy ({gmp_pct}% GMP) offers listing upside, but fundamentals do not support long-term holding."
            
            top_3 = [
                f"Strong Listing Demand: {gmp_pct:.1f}% GMP offers attractive listing-day profit opportunity.",
                "Strict Day-1 Exit Discipline: Jay Ritter rule applies — exit on listing session; do NOT hold as long-term investment.",
                f"Weak Corporate Moat: Fundamentals scored only {f_score:.0f}/100 with debt, lower margins, or high valuation."
            ]

        # 4. DO NOT APPLY (AVOID)
        else:
            verdict = DecisionType.AVOID
            color = DecisionBadgeColor.RED
            headline = f"Do Not Apply: Unfavorable risk-reward with weak fundamentals ({f_score}/100) and insufficient listing cushion ({gmp_pct}% GMP)."
            
            top_3 = [
                f"Sub-Par Financial Health: Total score {f_score:.0f}/100 indicates below-average financial stability.",
                f"Deficient Listing Buffer: At {gmp_pct:.1f}% GMP, there is significant risk of listing flat or at a discount.",
                "Capital preservation priority: Conserve capital and skip this issue to bid on higher-priority IPOs."
            ]

        return IPODecision(
            verdict=verdict,
            badge_color=color,
            headline=headline,
            key_points=top_3,
            top_3_reasons=top_3,
            allotment_chance=allotment_chance,
            fundamental_summary=f_summary,
            sentiment_summary=h_summary,
            book_wisdom=wisdom
        )

    @staticmethod
    def rank_ipos(ipos: List) -> List:
        """
        Ranks IPOs into an explicit 1-2-3-4-5 priority order based on composite attractiveness:
        Priority #1 is the highest return/safety opportunity, down to Avoids at the bottom.
        """
        def get_priority_weight(ipo):
            v = ipo.decision.verdict
            f_score = ipo.fundamentals.total_score or 0.0
            gmp_pct = ipo.hype.gmp_pct or 0.0
            
            if v == DecisionType.APPLY_BOTH:
                return 1000.0 + (f_score * 0.5) + (gmp_pct * 0.5)
            elif v == DecisionType.APPLY_LONG_TERM:
                return 700.0 + (f_score * 0.7) + (gmp_pct * 0.3)
            elif v == DecisionType.APPLY_LISTING_GAINS:
                return 500.0 + (gmp_pct * 0.8) + (f_score * 0.2)
            else:
                return 100.0 + f_score

        # Sort all by priority weight
        sorted_ipos = sorted(ipos, key=get_priority_weight, reverse=True)
        
        # Assign explicit 1-based ranks
        for idx, ipo in enumerate(sorted_ipos, start=1):
            ipo.priority_rank = idx
            ipo.decision.priority_rank = idx
            ipo.top_3_reasons = ipo.decision.top_3_reasons
            status_str = ipo.status.value if hasattr(ipo.status, 'value') else str(ipo.status)
            chance = DecisionEngine.calculate_allotment_chance(
                subscription_times=ipo.hype.subscription_times,
                open_date=ipo.open_date,
                close_date=ipo.close_date,
                status=status_str,
                gmp_pct=ipo.hype.gmp_pct
            )
            ipo.allotment_chance = chance
            ipo.decision.allotment_chance = chance

        return sorted_ipos

