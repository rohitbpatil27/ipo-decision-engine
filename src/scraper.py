import re
import datetime
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple, Dict, Any

from src.config import (
    INVESTORGAIN_API_URL,
    CHITTORGARH_BASE_URL,
    HTTP_HEADERS
)
from src.models import (
    IPODetail,
    StatusType,
    FinancialYearItem
)
from src.decision_engine import DecisionEngine
from src.storage import Storage

class IPOScraper:
    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()
        self.session = requests.Session()
        self.session.headers.update(HTTP_HEADERS)
        self._chittorgarh_map: Dict[str, str] = {}

    def _load_chittorgarh_map(self):
        try:
            resp = self.session.get(f"{CHITTORGARH_BASE_URL}/ipo/ipo_list.asp", timeout=12)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                links = soup.find_all('a', href=re.compile(r'/ipo/[a-z0-9-]+-ipo/\d+/'))
                for l in links:
                    name_clean = l.get_text(strip=True).replace(' IPO', '').strip().lower()
                    href = l.get('href')
                    if href and not href.startswith('http'):
                        href = f"{CHITTORGARH_BASE_URL}{href}"
                    self._chittorgarh_map[name_clean] = href
        except Exception as e:
            print(f"Could not preload Chittorgarh map: {e}")

    def run_sync(self) -> List[IPODetail]:
        """
        Executes a complete online update cycle:
        1. Preloads Chittorgarh DRHP map
        2. Fetches all live IPOs from Investorgain
        3. Filters strictly for Mainboard IPOs (excludes SMEs)
        4. Enriches each IPO with DRHP fundamentals from Chittorgarh
        5. Calculates decision verdict
        6. Persists in DB and returns records
        """
        self._load_chittorgarh_map()
        raw_ipos = self._fetch_live_ipos()
        processed: List[IPODetail] = []

        for item in raw_ipos:
            try:
                detail = self._process_single_ipo(item)
                if detail:
                    processed.append(detail)
            except Exception as e:
                print(f"Error processing IPO {item.get('~ipo_name')}: {e}")

        # Rank all IPOs in explicit 1-2-3-4-5 priority order
        ranked = DecisionEngine.rank_ipos(processed)
        for ipo in ranked:
            self.storage.save_ipo(ipo)

        return ranked

    def _fetch_live_ipos(self) -> List[Dict[str, Any]]:
        try:
            resp = self.session.get(INVESTORGAIN_API_URL, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            table_data = data.get("reportTableData", [])
            
            # Filter strictly for Mainboard IPOs (NO SMEs!)
            mainboard = [
                x for x in table_data 
                if str(x.get("~ipo_category1", "")).strip().upper() == "IPO"
            ]
            return mainboard
        except Exception as e:
            print(f"Error fetching live IPOs from API: {e}")
            return []

    def _process_single_ipo(self, raw: Dict[str, Any]) -> Optional[IPODetail]:
        ipo_id = int(raw.get("~id", 0))
        if not ipo_id:
            return None

        raw_name = raw.get("~ipo_name", "")
        if not raw_name:
            # Fallback parse from Name html
            m = re.search(r'>([^<]+)</a>', raw.get("Name", ""))
            raw_name = m.group(1).strip() if m else "Unknown IPO"

        slug = raw.get("~urlrewrite_folder_name", "")
        
        # Price parsing
        price_val = None
        price_str = str(raw.get("Price (₹)", "")).strip()
        m_price = re.search(r'(\d+(?:\.\d+)?)', price_str)
        if m_price:
            try:
                price_val = float(m_price.group(1))
            except ValueError:
                pass

        # GMP parsing
        gmp_pct_val = None
        gmp_pct_str = str(raw.get("~gmp_percent_calc", "")).strip()
        if gmp_pct_str:
            try:
                gmp_pct_val = float(gmp_pct_str)
            except ValueError:
                pass

        gmp_rs_val = None
        max_gmp_str = str(raw.get("~max_gmp1", "")).strip()
        if max_gmp_str and max_gmp_str != "0":
            try:
                gmp_rs_val = float(max_gmp_str)
            except ValueError:
                pass
        
        # If gmp_rs is still None, try parsing from GMP column
        if gmp_rs_val is None:
            gmp_cell = raw.get("GMP", "")
            m_gmp = re.search(r'&#8377;<b>([0-9.]+)</b>', gmp_cell)
            if m_gmp:
                try:
                    gmp_rs_val = float(m_gmp.group(1))
                except ValueError:
                    pass

        # Calculate GMP percentage if missing or 0 while gmp_rs is positive
        if (gmp_pct_val is None or gmp_pct_val == 0.0) and price_val and price_val > 0 and gmp_rs_val is not None and gmp_rs_val > 0:
            gmp_pct_val = round((gmp_rs_val / price_val) * 100, 2)

        # Lot size
        lot_val = None
        lot_str = str(raw.get("Lot", "")).strip()
        if lot_str and lot_str.isdigit():
            lot_val = int(lot_str)

        # Issue size
        issue_size_str = raw.get("IPO Size", "")
        # Clean HTML symbols like &#8377;
        issue_size_clean = re.sub(r'&#8377;', '₹', issue_size_str).strip()

        # Dates & Status
        open_date_str = raw.get("~Srt_Open") or raw.get("Open")
        close_date_str = raw.get("~Srt_Close") or raw.get("Close")
        allotment_date = raw.get("~Srt_BoA_Dt") or raw.get("BoA Dt")
        listing_date = raw.get("~Str_Listing") or raw.get("Listing")

        status_code = str(raw.get("~ipo_status1", "")).strip().upper()
        status = self._derive_status(status_code, open_date_str, close_date_str)

        # P/E from listing table as initial baseline
        pe_val = None
        pe_str = str(raw.get("~P/E", "")).strip()
        if pe_str and pe_str != "--":
            try:
                pe_val = float(pe_str)
            except ValueError:
                pass

        # Now enrich with DRHP financials from Chittorgarh or detail search
        financials, kpis, detail_pe, eps_val, fresh_cr, ofs_cr = self._scrape_chittorgarh_details(raw_name, slug)
        if detail_pe is not None:
            pe_val = detail_pe

        roe_val = kpis.get("roe")
        roce_val = kpis.get("roce")
        de_val = kpis.get("debt_to_equity")

        # Compute OFS Ratio
        ofs_ratio_val = None
        if fresh_cr is not None and ofs_cr is not None:
            tot = fresh_cr + ofs_cr
            if tot > 0:
                ofs_ratio_val = round((ofs_cr / tot) * 100, 1)
        elif ofs_cr is not None and fresh_cr == 0:
            ofs_ratio_val = 100.0

        # Evaluate Fundamentals
        fundamentals = DecisionEngine.evaluate_fundamentals(
            roe=roe_val,
            roce=roce_val,
            debt_to_equity=de_val,
            pe=pe_val,
            eps=eps_val,
            financials=financials
        )

        # Evaluate Hype
        trend_str = "Stable"
        if raw.get("GMP") and "↑" in raw.get("GMP"):
            trend_str = "Upward"
        elif raw.get("GMP") and "↓" in raw.get("GMP"):
            trend_str = "Downward"

        sub_str = raw.get("Sub", "").replace("x", "").strip()
        sub_val = None
        try:
            if sub_str and sub_str != "-":
                sub_val = float(sub_str)
        except ValueError:
            pass

        hype = DecisionEngine.evaluate_hype(
            gmp_rs=gmp_rs_val,
            gmp_pct=gmp_pct_val,
            price=price_val,
            trend=trend_str,
            subscription=sub_val
        )

        # Resolve Final Decision with Book Wisdom
        decision = DecisionEngine.resolve_decision(
            fundamentals=fundamentals,
            hype=hype,
            company_name=raw_name,
            fresh_issue_cr=fresh_cr,
            ofs_cr=ofs_cr,
            ofs_ratio_pct=ofs_ratio_val
        )

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return IPODetail(
            id=ipo_id,
            name=raw_name,
            slug=slug,
            category="IPO",
            status=status,
            price=price_val,
            price_band=f"₹{price_val}" if price_val else "TBD",
            lot_size=lot_val,
            issue_size_cr=issue_size_clean if issue_size_clean != "-" else "TBD",
            fresh_issue_cr=fresh_cr,
            ofs_cr=ofs_cr,
            ofs_ratio_pct=ofs_ratio_val,
            open_date=open_date_str if open_date_str else "TBD",
            close_date=close_date_str if close_date_str else "TBD",
            allotment_date=allotment_date if allotment_date else "TBD",
            listing_date=listing_date if listing_date else "TBD",
            fundamentals=fundamentals,
            financials=financials,
            hype=hype,
            decision=decision,
            book_wisdom=decision.book_wisdom,
            updated_at=now_str,
            source_url=f"https://www.investorgain.com{slug}" if slug else None
        )

    def _derive_status(
        self,
        status_code: str,
        open_dt: Optional[str],
        close_dt: Optional[str]
    ) -> StatusType:
        # Check explicit code first
        if status_code in ["O", "CT"]:
            return StatusType.OPEN
        elif status_code in ["C", "LT"]:
            return StatusType.CLOSED
        elif status_code in ["LP", "LN", "L"]:
            return StatusType.LISTED
        elif status_code == "U":
            # Cross-verify with date if available
            today = datetime.date.today()
            if open_dt and close_dt:
                try:
                    o_date = datetime.datetime.strptime(open_dt[:10], "%Y-%m-%d").date()
                    c_date = datetime.datetime.strptime(close_dt[:10], "%Y-%m-%d").date()
                    if o_date <= today <= c_date:
                        return StatusType.OPEN
                    elif today > c_date:
                        return StatusType.CLOSED
                    elif today < o_date:
                        return StatusType.UPCOMING
                except Exception:
                    pass
            return StatusType.UPCOMING

        return StatusType.UPCOMING

    def _scrape_chittorgarh_details(
        self,
        company_name: str,
        investorgain_slug: str
    ) -> Tuple[List[FinancialYearItem], Dict[str, Optional[float]], Optional[float], Optional[float], Optional[float], Optional[float]]:
        financials: List[FinancialYearItem] = []
        kpis: Dict[str, Optional[float]] = {"roe": None, "roce": None, "debt_to_equity": None}
        pe_val = None
        eps_val = None
        fresh_cr = None
        ofs_cr = None

        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', company_name).strip().lower()
        slug_tokens = clean_name.replace(" ", "-")

        urls_to_try = []

        # 1. Check exact or partial match in preloaded Chittorgarh map
        for k, v in self._chittorgarh_map.items():
            if k in clean_name or clean_name in k or (len(k) > 4 and k[:6] in clean_name):
                urls_to_try.append(v)
                break

        # 2. Add fallback slug heuristics
        urls_to_try.append(f"{CHITTORGARH_BASE_URL}/ipo/{slug_tokens}-ipo/")
        if investorgain_slug.startswith("/ipo/"):
            urls_to_try.append(f"{CHITTORGARH_BASE_URL}{investorgain_slug}")

        for url in filter(None, urls_to_try):
            try:
                resp = self.session.get(url, timeout=10)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 0. Scrape Fresh Issue vs OFS
                for row in soup.find_all('tr'):
                    txt = row.get_text()
                    if "Fresh Issue" in txt:
                        m = re.search(r'₹\s*([0-9.,]+)\s*Cr', txt, re.IGNORECASE)
                        if m:
                            try:
                                fresh_cr = float(m.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    if "Offer for Sale" in txt or "OFS" in txt:
                        m = re.search(r'₹\s*([0-9.,]+)\s*Cr', txt, re.IGNORECASE)
                        if m:
                            try:
                                ofs_cr = float(m.group(1).replace(',', ''))
                            except ValueError:
                                pass

                # 1. Scrape Financials Table
                fin_table = None
                for t in soup.find_all('table'):
                    txt = t.get_text()
                    if "Period Ended" in txt and ("Assets" in txt or "Total Income" in txt or "Profit After Tax" in txt):
                        fin_table = t
                        break

                if fin_table:
                    financials = self._parse_financial_table(fin_table)

                # 2. Scrape KPI Table
                for t in soup.find_all('table'):
                    txt = t.get_text()
                    if "KPI" in txt or "ROE" in txt:
                        for row in t.find_all('tr'):
                            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                            if len(cells) >= 2:
                                metric = cells[0].upper()
                                val_clean = cells[1].replace('%', '').replace(',', '').strip()
                                try:
                                    num = float(val_clean)
                                    if "ROE" in metric and kpis["roe"] is None:
                                        kpis["roe"] = num
                                    elif "ROCE" in metric and kpis["roce"] is None:
                                        kpis["roce"] = num
                                    elif ("DEBT/EQUITY" in metric or "DEBT TO EQUITY" in metric) and kpis["debt_to_equity"] is None:
                                        kpis["debt_to_equity"] = num
                                except ValueError:
                                    pass

                # 3. Scrape Valuation Table
                for t in soup.find_all('table'):
                    txt = t.get_text()
                    if "Valuation Metric" in txt or "P/E" in txt:
                        for row in t.find_all('tr'):
                            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                            if len(cells) >= 2:
                                metric = cells[0].upper()
                                target_val = cells[-1] if len(cells) > 2 else cells[1]
                                val_clean = target_val.replace(',', '').strip()
                                try:
                                    num = float(val_clean)
                                    if "P/E" in metric and pe_val is None:
                                        pe_val = num
                                    elif "EPS" in metric and eps_val is None:
                                        eps_val = num
                                except ValueError:
                                    pass

                if financials or kpis["roe"] is not None:
                    break

            except Exception as e:
                pass

        return financials, kpis, pe_val, eps_val, fresh_cr, ofs_cr

    def _parse_financial_table(self, table) -> List[FinancialYearItem]:
        rows = table.find_all('tr')
        if not rows:
            return []

        header_cells = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
        periods = header_cells[1:]
        if not periods:
            return []

        # Map metric rows
        metrics: Dict[str, List[Optional[float]]] = {}
        for r in rows[1:]:
            cells = [td.get_text(strip=True) for td in r.find_all(['td', 'th'])]
            if len(cells) < 2:
                continue
            name = cells[0].lower()
            vals = []
            for c in cells[1:]:
                clean_num = c.replace(',', '').replace('₹', '').strip()
                try:
                    vals.append(float(clean_num))
                except ValueError:
                    vals.append(None)
            
            if "asset" in name:
                metrics["assets"] = vals
            elif "total income" in name or "revenue" in name:
                metrics["revenue"] = vals
            elif "profit after tax" in name or "pat" in name:
                metrics["pat"] = vals
            elif "net worth" in name:
                metrics["net_worth"] = vals
            elif "borrowing" in name:
                metrics["borrowing"] = vals

        items: List[FinancialYearItem] = []
        for idx, period in enumerate(periods):
            items.append(FinancialYearItem(
                period=period,
                assets_cr=metrics.get("assets", [None]*len(periods))[idx] if idx < len(metrics.get("assets", [])) else None,
                revenue_cr=metrics.get("revenue", [None]*len(periods))[idx] if idx < len(metrics.get("revenue", [])) else None,
                pat_cr=metrics.get("pat", [None]*len(periods))[idx] if idx < len(metrics.get("pat", [])) else None,
                net_worth_cr=metrics.get("net_worth", [None]*len(periods))[idx] if idx < len(metrics.get("net_worth", [])) else None,
                borrowing_cr=metrics.get("borrowing", [None]*len(periods))[idx] if idx < len(metrics.get("borrowing", [])) else None
            ))

        return items
