from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DecisionType(str, Enum):
    APPLY_BOTH = "Apply for Listing Gains as well as Long Term"
    APPLY_LONG_TERM = "Apply only for Long Term"
    APPLY_LISTING_GAINS = "Apply only for Listing Gains"
    AVOID = "Do Not Apply"

class DecisionBadgeColor(str, Enum):
    GREEN = "green"   # Apply for Listing Gains & Long Term
    PURPLE = "purple" # Apply only for Long Term
    AMBER = "amber"   # Apply only for Listing Gains
    RED = "red"       # Do Not Apply

class StatusType(str, Enum):
    OPEN = "OPEN"
    UPCOMING = "UPCOMING"
    CLOSED = "CLOSED"
    LISTED = "LISTED"

class FinancialYearItem(BaseModel):
    period: str
    assets_cr: Optional[float] = None
    revenue_cr: Optional[float] = None
    pat_cr: Optional[float] = None
    net_worth_cr: Optional[float] = None
    borrowing_cr: Optional[float] = None

class BookWisdomAnalysis(BaseModel):
    # 1. Peter Lynch Rule (Fresh Issue vs OFS)
    lynch_verdict: str = "Neutral"
    lynch_rationale: str = ""
    fresh_issue_cr: Optional[float] = None
    ofs_cr: Optional[float] = None
    ofs_ratio_pct: Optional[float] = None

    # 2. Benjamin Graham Rule (Margin of Safety & Cycle Valuation)
    graham_verdict: str = "Neutral"
    graham_rationale: str = ""

    # 3. Prof. Jay Ritter Empirical Rule (1-Day Flip vs 3-Yr Underperformance)
    ritter_verdict: str = "Neutral"
    ritter_rationale: str = ""

    # 4. Buffett & Munger Moat & Capital Efficiency Test
    buffett_verdict: str = "Neutral"
    buffett_rationale: str = ""

    # 5. Philip Fisher Earnings Quality Test
    fisher_verdict: str = "Neutral"
    fisher_rationale: str = ""

class FundamentalAnalysis(BaseModel):
    roe: Optional[float] = None
    roce: Optional[float] = None
    debt_to_equity: Optional[float] = None
    pe: Optional[float] = None
    eps: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    pat_growth_yoy: Optional[float] = None
    pat_margin_pct: Optional[float] = None
    
    # Sub-scores
    growth_score: float = 0.0          # Max 25
    profitability_score: float = 0.0   # Max 25
    capital_efficiency_score: float = 0.0 # Max 25
    leverage_score: float = 0.0        # Max 15
    valuation_score: float = 0.0       # Max 10
    total_score: float = 0.0           # Max 100
    is_strong: bool = False

class HypeAnalysis(BaseModel):
    gmp_rs: Optional[float] = None
    gmp_pct: Optional[float] = None
    price: Optional[float] = None
    estimated_listing_price: Optional[float] = None
    gmp_trend: Optional[str] = "Stable"
    subscription_times: Optional[float] = None
    hype_score: float = 0.0            # Max 100
    demand_level: str = "Neutral"      # Very High, High, Moderate, Low, Weak

class IPODecision(BaseModel):
    verdict: DecisionType
    badge_color: DecisionBadgeColor
    headline: str
    key_points: List[str]
    top_3_reasons: List[str] = []
    allotment_chance: str = "Awaiting bid data"
    priority_rank: Optional[int] = None
    fundamental_summary: str
    sentiment_summary: str
    book_wisdom: BookWisdomAnalysis = Field(default_factory=BookWisdomAnalysis)

class IPODetail(BaseModel):
    id: int
    name: str
    slug: str
    category: str = "IPO"              # Strictly mainboard
    status: StatusType
    priority_rank: Optional[int] = None
    allotment_chance: Optional[str] = None
    top_3_reasons: List[str] = []
    price: Optional[float] = None
    price_band: Optional[str] = None
    lot_size: Optional[int] = None
    issue_size_cr: Optional[str] = None
    fresh_issue_cr: Optional[float] = None
    ofs_cr: Optional[float] = None
    ofs_ratio_pct: Optional[float] = None
    open_date: Optional[str] = None
    close_date: Optional[str] = None
    allotment_date: Optional[str] = None
    listing_date: Optional[str] = None
    
    # Raw & Parsed Data
    fundamentals: FundamentalAnalysis
    financials: List[FinancialYearItem] = []
    hype: HypeAnalysis
    decision: IPODecision
    book_wisdom: BookWisdomAnalysis = Field(default_factory=BookWisdomAnalysis)
    
    updated_at: str
    source_url: Optional[str] = None
