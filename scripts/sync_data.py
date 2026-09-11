import os
import sys
import json
from pathlib import Path

# Add project root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.storage import Storage
from src.scraper import IPOScraper

def run_sync():
    print("[SYNC] Starting automated live sync...")
    storage = Storage(auto_seed=True)
    scraper = IPOScraper(storage)
    
    results = scraper.run_sync()
    count = len(results) if results else 0
    print(f"[SYNC] Scraping complete: {count} Mainboard IPOs synchronized.")
    
    # Export to src/seed_data.py
    ipos = storage.get_all_ipos()
    data = [i.model_dump(mode='json') for i in ipos]
    raw_json = json.dumps(data, ensure_ascii=False)
    
    code = f'''# Auto-generated seed data for Vercel serverless cold starts
import json

_DATA = {json.dumps(raw_json)}
SEED_IPOS = json.loads(_DATA)
'''
    seed_file = BASE_DIR / "src" / "seed_data.py"
    with open(seed_file, "w", encoding="utf-8") as f:
        f.write(code)
    
    print(f"[SYNC] Exported {len(data)} IPOs cleanly to {seed_file}")
    print("[SYNC] Daily sync finished successfully!")

if __name__ == "__main__":
    run_sync()
