# IPO Decision Engine & Allotment Advisor

A high-performance, data-driven web application and quantitative advisory engine for **Indian Mainboard IPOs**. Built with a minimalist, high-contrast **Zerodha Kite** user interface, it provides unambiguous investment recommendations, **mathematical allotment probabilities**, and **priority ranking** based strictly on audited SEBI DRHP balance sheets and live market bidding.

> **SME IPOs are strictly excluded** to focus entirely on Mainboard issues.

---

## Key Features

1. **Unambiguous Investment Verdicts**:
   - 🟢 **Apply for Listing Gains as well as Long Term**: High return on capital + ample listing premium.
   - 🟣 **Apply only for Long Term**: Strong business compounding, but flat/muted listing pop.
   - 🟡 **Apply only for Listing Gains**: Speculative listing frenzy; mandates strict Day-1 exit.
   - 🔴 **Do Not Apply (Avoid)**: Unfavorable risk-reward, weak fundamentals, or elevated debt.

2. **Capital Allocation Priority Ranking (#1, #2, #3...)**:
   - Ranks all available Mainboard IPOs numerically so investors know exactly which issue to allocate capital to first.

3. **Live Retail Allotment Probability Engine**:
   - Calculates exact retail allotment odds directly from live exchange subscription tallies ($S\times$):
     - **$\le 1.0\times$ (Undersubscribed)**: `100% Guaranteed Allotment`.
     - **$> 1.0\times$ (Oversubscribed Lottery)**: Converts mathematically to computerized lottery probability: $\text{Prob} = \frac{100}{S}\%$ (e.g. `~9.8% lottery (~1 in 10 chance)`).
     - **Upcoming / Not Yet Open**: Displays clean opening schedule (e.g. `Bidding not open yet (Opens 16-Sep)`).

4. **Date-First Urgency Sorting**:
   - Automatically orders currently open IPOs chronologically by closing date so you never miss a 4:30 PM UPI bidding cutoff.
   - Color-coded urgency badges: **`Closes Today`** (Red), **`Closes Tomorrow`** (Amber), and future dates.

5. **Top 3 Specific Reasons**:
   - Distills balance sheets into the 3 most critical reasons why an investor should apply or avoid.

6. **Canonical Investment Wisdom**:
   - Codifies quantitative rules from **Peter Lynch** (Fresh Issue vs. OFS insider selling), **Benjamin Graham** (margin of safety and cycle valuation), **Prof. Jay Ritter** (1-day listing anomaly), and **Warren Buffett & Charlie Munger** (ROCE moat without leverage).

---

## Project Structure

```
ipo-decision-engine/
├── api/
│   └── index.py            # Vercel Serverless Function entrypoint
├── data/
│   └── ipo_advisor.db      # SQLite database (pre-seeded with Mainboard IPOs)
├── frontend/
│   └── index.html          # Minimalist Zerodha-inspired dashboard
├── src/
│   ├── app.py              # FastAPI application & REST endpoints
│   ├── config.py           # Vercel-aware config & thresholds
│   ├── decision_engine.py  # Fundamental scoring, allotment odds & ranking
│   ├── models.py           # Pydantic data schemas
│   ├── scheduler.py        # Daily background sync scheduler
│   ├── scraper.py          # DRHP balance sheet & live GMP parser
│   └── storage.py          # SQLite persistence & rank hydrator
├── tests/                  # Complete unit & integration test suite
├── vercel.json             # Vercel deployment configuration
├── main.py                 # Local server & CLI entrypoint
├── requirements.txt        # Python package dependencies
└── run.bat                 # Windows 1-click launcher
```

---

## Local Development & Setup

### Prerequisites
- Python 3.10 or higher
- pip

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Local Web Dashboard
```bash
python main.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

*(On Windows, you can simply double-click `run.bat`)*

### 3. Run Headless CLI Report
```bash
python main.py --cli
```

### 4. Run Automated Tests
```bash
python -m unittest discover -s tests -v
```

---

## Deploying to Vercel

This repository is pre-configured for seamless deployment to **Vercel** as a Python Serverless Application.

### Option A: Deploy via GitHub (Recommended)
1. Push this repository to GitHub:
   ```bash
   git push -u origin main
   ```
2. Go to [Vercel Dashboard](https://vercel.com/dashboard) and click **"Add New..." > "Project"**.
3. Import your `ipo-decision-engine` repository.
4. Leave the default settings (Framework Preset: **Other**, Root Directory: `./`).
5. Click **Deploy**. Vercel will automatically detect `vercel.json`, install dependencies from `requirements.txt`, and deploy the application.

### Option B: Deploy via Vercel CLI
```bash
npm install -g vercel
vercel
```

---

## REST API Endpoints

- `GET /api/ipos`: Returns all Mainboard IPOs. Query parameters:
  - `status`: `open`, `upcoming`, or omitted for all.
  - `sort`: `date` (default), `priority`, `sub`, `gmp_desc`, `score_desc`.
- `GET /api/ipos/{id}`: Returns detailed financial and book wisdom metrics for a specific IPO.
- `GET /api/status`: Returns sync status, last update timestamp, and IPO counts.
- `POST /api/refresh`: Triggers an immediate online refresh of live bidding data and GMP.

---

## Disclaimer

*Educational and research tool only. Not SEBI-registered investment advice. Initial Public Offerings involve substantial market risk, and Grey Market Premiums (GMP) are unofficial and unregulated. Perform independent financial due diligence before bidding.*
