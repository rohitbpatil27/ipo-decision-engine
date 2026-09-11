import threading
import time
import datetime
from typing import Optional
from src.scraper import IPOScraper
from src.config import AUTO_UPDATE_INTERVAL_HOURS

class BackgroundScheduler:
    def __init__(self, scraper: Optional[IPOScraper] = None):
        self.scraper = scraper or IPOScraper()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.is_running = False
        self.last_run_time: Optional[str] = None
        self.next_run_time: Optional[str] = None
        self.is_syncing = False

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("Background daily IPO scheduler started.")

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        print("Background daily IPO scheduler stopped.")

    def run_now(self):
        """Triggers an immediate synchronization cycle asynchronously."""
        thread = threading.Thread(target=self._do_sync, daemon=True)
        thread.start()

    def _do_sync(self):
        if self.is_syncing:
            print("Sync already in progress, skipping duplicate trigger.")
            return
        self.is_syncing = True
        try:
            print(f"[{datetime.datetime.now()}] Starting IPO data synchronization...")
            results = self.scraper.run_sync()
            self.last_run_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            next_dt = datetime.datetime.now() + datetime.timedelta(hours=AUTO_UPDATE_INTERVAL_HOURS)
            self.next_run_time = next_dt.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{datetime.datetime.now()}] Synchronization complete. Updated {len(results)} Mainboard IPOs.")
        except Exception as e:
            print(f"Error during synchronization cycle: {e}")
        finally:
            self.is_syncing = False

    def _loop(self):
        # Initial run on boot if needed
        self._do_sync()

        sleep_seconds = AUTO_UPDATE_INTERVAL_HOURS * 3600
        while not self._stop_event.is_set():
            # Check every 60 seconds if stop is signaled
            for _ in range(int(sleep_seconds / 60)):
                if self._stop_event.is_set():
                    return
                time.sleep(60)
            
            if not self._stop_event.is_set():
                self._do_sync()
