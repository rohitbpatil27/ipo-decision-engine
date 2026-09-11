import sqlite3
import json
from typing import List, Optional, Dict, Any
from src.config import DB_PATH
from src.models import IPODetail, StatusType, BookWisdomAnalysis

class Storage:
    def __init__(self, db_path=DB_PATH, auto_seed: bool = True):
        self.db_path = str(db_path)
        self.auto_seed = auto_seed
        self.init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ipos (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    price REAL,
                    price_band TEXT,
                    lot_size INTEGER,
                    issue_size_cr TEXT,
                    fresh_issue_cr REAL,
                    ofs_cr REAL,
                    ofs_ratio_pct REAL,
                    open_date TEXT,
                    close_date TEXT,
                    allotment_date TEXT,
                    listing_date TEXT,
                    fundamentals_json TEXT,
                    financials_json TEXT,
                    hype_json TEXT,
                    decision_json TEXT,
                    book_wisdom_json TEXT,
                    updated_at TEXT,
                    source_url TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ipos_status ON ipos(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ipos_category ON ipos(category)")

            # Run migrations for existing DBs
            cols = [row[1] for row in cursor.execute("PRAGMA table_info(ipos)").fetchall()]
            if "fresh_issue_cr" not in cols:
                cursor.execute("ALTER TABLE ipos ADD COLUMN fresh_issue_cr REAL")
            if "ofs_cr" not in cols:
                cursor.execute("ALTER TABLE ipos ADD COLUMN ofs_cr REAL")
            if "ofs_ratio_pct" not in cols:
                cursor.execute("ALTER TABLE ipos ADD COLUMN ofs_ratio_pct REAL")
            if "book_wisdom_json" not in cols:
                cursor.execute("ALTER TABLE ipos ADD COLUMN book_wisdom_json TEXT")

            conn.commit()

            # Automatically seed database on cold-start if table is empty
            if self.auto_seed:
                try:
                    cursor.execute("SELECT COUNT(*) FROM ipos")
                    if cursor.fetchone()[0] == 0:
                        self._seed_default_data(conn)
                except Exception as e:
                    print(f"Notice: Initial seed check: {e}")

    def _seed_default_data(self, conn=None):
        """Seeds SQLite database from bundled Python seed data on fresh deployment"""
        try:
            from src.seed_data import SEED_IPOS
            from src.models import IPODetail
            should_close = False
            if conn is None:
                conn = self._get_connection()
                should_close = True

            cursor = conn.cursor()
            for item in SEED_IPOS:
                ipo = IPODetail(**item)
                cursor.execute("""
                    INSERT INTO ipos (
                        id, name, slug, category, status, price, price_band,
                        lot_size, issue_size_cr, fresh_issue_cr, ofs_cr, ofs_ratio_pct,
                        open_date, close_date, allotment_date, listing_date,
                        fundamentals_json, financials_json, hype_json, decision_json,
                        book_wisdom_json, updated_at, source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status=excluded.status,
                        decision_json=excluded.decision_json,
                        hype_json=excluded.hype_json,
                        updated_at=excluded.updated_at
                """, (
                    ipo.id,
                    ipo.name,
                    ipo.slug,
                    ipo.category,
                    ipo.status.value,
                    ipo.price,
                    ipo.price_band,
                    ipo.lot_size,
                    ipo.issue_size_cr,
                    ipo.fresh_issue_cr,
                    ipo.ofs_cr,
                    ipo.ofs_ratio_pct,
                    ipo.open_date,
                    ipo.close_date,
                    ipo.allotment_date,
                    ipo.listing_date,
                    json.dumps(ipo.fundamentals.model_dump()),
                    json.dumps([f.model_dump() for f in ipo.financials]),
                    json.dumps(ipo.hype.model_dump()),
                    json.dumps(ipo.decision.model_dump()),
                    json.dumps(ipo.book_wisdom.model_dump()),
                    ipo.updated_at,
                    ipo.source_url
                ))
            conn.commit()
            if should_close:
                conn.close()
        except Exception as e:
            print(f"Warning: Auto-seed failed: {e}")

    def save_ipo(self, ipo: IPODetail):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ipos (
                    id, name, slug, category, status, price, price_band,
                    lot_size, issue_size_cr, fresh_issue_cr, ofs_cr, ofs_ratio_pct,
                    open_date, close_date, allotment_date, listing_date,
                    fundamentals_json, financials_json, hype_json, decision_json,
                    book_wisdom_json, updated_at, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    slug=excluded.slug,
                    category=excluded.category,
                    status=excluded.status,
                    price=excluded.price,
                    price_band=excluded.price_band,
                    lot_size=excluded.lot_size,
                    issue_size_cr=excluded.issue_size_cr,
                    fresh_issue_cr=excluded.fresh_issue_cr,
                    ofs_cr=excluded.ofs_cr,
                    ofs_ratio_pct=excluded.ofs_ratio_pct,
                    open_date=excluded.open_date,
                    close_date=excluded.close_date,
                    allotment_date=excluded.allotment_date,
                    listing_date=excluded.listing_date,
                    fundamentals_json=excluded.fundamentals_json,
                    financials_json=excluded.financials_json,
                    hype_json=excluded.hype_json,
                    decision_json=excluded.decision_json,
                    book_wisdom_json=excluded.book_wisdom_json,
                    updated_at=excluded.updated_at,
                    source_url=excluded.source_url
            """, (
                ipo.id,
                ipo.name,
                ipo.slug,
                ipo.category,
                ipo.status.value,
                ipo.price,
                ipo.price_band,
                ipo.lot_size,
                ipo.issue_size_cr,
                ipo.fresh_issue_cr,
                ipo.ofs_cr,
                ipo.ofs_ratio_pct,
                ipo.open_date,
                ipo.close_date,
                ipo.allotment_date,
                ipo.listing_date,
                json.dumps(ipo.fundamentals.model_dump()),
                json.dumps([f.model_dump() for f in ipo.financials]),
                json.dumps(ipo.hype.model_dump()),
                json.dumps(ipo.decision.model_dump()),
                json.dumps(ipo.book_wisdom.model_dump()),
                ipo.updated_at,
                ipo.source_url
            ))
            conn.commit()

    def get_all_ipos(self, status_filter: Optional[str] = None) -> List[IPODetail]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.auto_seed:
                    cursor.execute("SELECT COUNT(*) FROM ipos")
                    if cursor.fetchone()[0] == 0:
                        self._seed_default_data(conn)

                if status_filter:
                    query = "SELECT * FROM ipos WHERE status = ? AND category = 'IPO' ORDER BY id DESC"
                    cursor.execute(query, (status_filter.upper(),))
                else:
                    query = "SELECT * FROM ipos WHERE category = 'IPO' ORDER BY id DESC"
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                results = []
                for r in rows:
                    results.append(self._row_to_model(r))
                
                if any(x.priority_rank is None for x in results):
                    from src.decision_engine import DecisionEngine
                    results = DecisionEngine.rank_ipos(results)
                    
                if results or not self.auto_seed:
                    return results
        except Exception as e:
            print(f"Database query failed, using in-memory seed fallback: {e}")

        # In-memory fallback guaranteeing the UI is NEVER empty on fresh cloud cold starts
        if self.auto_seed:
            try:
                from src.seed_data import SEED_IPOS
                fallback = [IPODetail(**x) for x in SEED_IPOS]
                if status_filter:
                    fallback = [x for x in fallback if x.status.value == status_filter.upper()]
                from src.decision_engine import DecisionEngine
                return DecisionEngine.rank_ipos(fallback)
            except Exception:
                return []
        return []

    def get_ipo_by_id(self, ipo_id: int) -> Optional[IPODetail]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ipos WHERE id = ?", (ipo_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_model(row)
        except Exception:
            pass

        if self.auto_seed:
            try:
                from src.seed_data import SEED_IPOS
                for item in SEED_IPOS:
                    if item.get("id") == ipo_id:
                        return IPODetail(**item)
            except Exception:
                pass
        return None

    def get_stats(self) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ipos WHERE category = 'IPO'")
                total = cursor.fetchone()[0]
                if total == 0 and self.auto_seed:
                    self._seed_default_data(conn)
                    cursor.execute("SELECT COUNT(*) FROM ipos WHERE category = 'IPO'")
                    total = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM ipos WHERE category = 'IPO' AND status = 'OPEN'")
                open_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM ipos WHERE category = 'IPO' AND status = 'UPCOMING'")
                upcoming_count = cursor.fetchone()[0]

                cursor.execute("SELECT updated_at FROM ipos ORDER BY updated_at DESC LIMIT 1")
                row = cursor.fetchone()
                last_updated = row[0] if row else None

                if total > 0 or not self.auto_seed:
                    return {
                        "total_mainboard_ipos": total,
                        "open_count": open_count,
                        "upcoming_count": upcoming_count,
                        "last_updated": last_updated
                    }
        except Exception as e:
            print(f"Stats query error: {e}")

        if self.auto_seed:
            try:
                from src.seed_data import SEED_IPOS
                total = len(SEED_IPOS)
                open_count = sum(1 for x in SEED_IPOS if x.get("status") == "OPEN")
                upcoming_count = sum(1 for x in SEED_IPOS if x.get("status") == "UPCOMING")
                last_updated = SEED_IPOS[0].get("updated_at") if SEED_IPOS else None
                return {
                    "total_mainboard_ipos": total,
                    "open_count": open_count,
                    "upcoming_count": upcoming_count,
                    "last_updated": last_updated
                }
            except Exception:
                pass
        return {
            "total_mainboard_ipos": 0,
            "open_count": 0,
            "upcoming_count": 0,
            "last_updated": None
        }

    def _row_to_model(self, row: sqlite3.Row) -> IPODetail:
        cols = row.keys()
        
        # Parse decision and ensure book_wisdom is loaded
        decision_data = json.loads(row["decision_json"])
        
        book_wisdom = None
        if "book_wisdom_json" in cols and row["book_wisdom_json"]:
            book_wisdom = BookWisdomAnalysis(**json.loads(row["book_wisdom_json"]))
        elif "book_wisdom" in decision_data:
            book_wisdom = BookWisdomAnalysis(**decision_data["book_wisdom"])
        else:
            book_wisdom = BookWisdomAnalysis()

        fresh_cr = row["fresh_issue_cr"] if "fresh_issue_cr" in cols else None
        ofs_cr = row["ofs_cr"] if "ofs_cr" in cols else None
        ofs_ratio = row["ofs_ratio_pct"] if "ofs_ratio_pct" in cols else None

        hype_data = json.loads(row["hype_json"])
        sub_times = hype_data.get("subscription_times")
        allotment_chance = decision_data.get("allotment_chance")
        
        # Recalculate allotment chance if subscription data is present
        if (not allotment_chance or allotment_chance == "Awaiting bid data") and sub_times:
            from src.decision_engine import DecisionEngine
            allotment_chance = DecisionEngine.calculate_allotment_chance(
                subscription_times=sub_times,
                open_date=row["open_date"],
                close_date=row["close_date"],
                status=row["status"],
                gmp_pct=hype_data.get("gmp_pct")
            )
            decision_data["allotment_chance"] = allotment_chance

        reasons = decision_data.get("top_3_reasons") or decision_data.get("key_points") or []

        return IPODetail(
            id=row["id"],
            name=row["name"],
            slug=row["slug"],
            category=row["category"],
            status=StatusType(row["status"]),
            priority_rank=decision_data.get("priority_rank"),
            allotment_chance=allotment_chance,
            top_3_reasons=reasons,
            price=row["price"],
            price_band=row["price_band"],
            lot_size=row["lot_size"],
            issue_size_cr=row["issue_size_cr"],
            fresh_issue_cr=fresh_cr,
            ofs_cr=ofs_cr,
            ofs_ratio_pct=ofs_ratio,
            open_date=row["open_date"],
            close_date=row["close_date"],
            allotment_date=row["allotment_date"],
            listing_date=row["listing_date"],
            fundamentals=json.loads(row["fundamentals_json"]),
            financials=json.loads(row["financials_json"]),
            hype=hype_data,
            decision=decision_data,
            book_wisdom=book_wisdom,
            updated_at=row["updated_at"],
            source_url=row["source_url"]
        )
