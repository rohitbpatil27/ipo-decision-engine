import argparse
import sys
import uvicorn

# Reconfigure stdout for UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.storage import Storage
from src.scraper import IPOScraper

def run_cli_view():
    """Prints a terminal summary of currently open and upcoming mainboard IPOs and recommendations."""
    print("=" * 75)
    print(" IPO DECISION ENGINE: MAINBOARD ADVISORY REPORT")
    print("=" * 75)
    storage = Storage()
    ipos = storage.get_all_ipos()
    if not ipos:
        print("No IPO data found locally. Running initial live synchronization...")
        scraper = IPOScraper(storage)
        ipos = scraper.run_sync()

    open_ipos = [x for x in ipos if x.status.value == "OPEN"]
    upcoming_ipos = [x for x in ipos if x.status.value == "UPCOMING"]

    print(f"\n[🔥 CURRENTLY OPEN MAINBOARD IPOS ({len(open_ipos)})]")
    if not open_ipos:
        print("  No mainboard IPOs are open for bidding today.")
    for ipo in open_ipos:
        print(f"\n* {ipo.name.upper()} (Price: ₹{ipo.price or 'TBD'})")
        print(f"  VERDICT    : [{ipo.decision.verdict.value}]")
        print(f"  FUNDAMENTAL: {ipo.fundamentals.total_score}/100 | ROE: {ipo.fundamentals.roe or 'N/A'}% | P/E: {ipo.fundamentals.pe or 'N/A'}x")
        print(f"  MARKET GMP : ₹{ipo.hype.gmp_rs or 0} ({ipo.hype.gmp_pct or 0}%) | Demand: {ipo.hype.demand_level}")
        print(f"  RATIONALE  : {ipo.decision.headline}")
        for pt in ipo.decision.key_points[:2]:
            print(f"    - {pt}")

    print(f"\n[⏳ UPCOMING MAINBOARD IPOS ({len(upcoming_ipos)})]")
    for ipo in upcoming_ipos[:5]:
        print(f"\n* {ipo.name} (Opens: {ipo.open_date})")
        print(f"  VERDICT    : [{ipo.decision.verdict.value}]")
        print(f"  FUNDAMENTAL: {ipo.fundamentals.total_score}/100 | GMP: {ipo.hype.gmp_pct or 0}%")
        print(f"  RATIONALE  : {ipo.decision.headline}")
    print("\n" + "=" * 75)

def main():
    parser = argparse.ArgumentParser(description="IPO Decision Engine & Web Advisor")
    parser.add_argument("--cli", action="store_true", help="Print decisions in terminal and exit")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    args = parser.parse_args()

    if args.cli:
        run_cli_view()
        sys.exit(0)

    print(f"Starting IPO Decision Engine Web Server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to terminate.")
    uvicorn.run("src.app:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
