"""
Accelerator, Investor & Principal Investor scraper.

Searches PitchBook for AI-focused accelerators, VCs, PE firms, corporate VCs,
and principal investors, then extracts public profile data.
"""

import sys
from pathlib import Path
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from models.schemas import Investor, Investment, Location
from scraper.base import BaseScraper


# Additional search terms specifically for finding investors/accelerators
INVESTOR_SEARCH_TERMS = [
    "AI venture capital",
    "artificial intelligence investor",
    "AI accelerator",
    "machine learning fund",
    "AI incubator",
    "generative AI venture",
    "AI corporate venture",
    "AI principal investor",
    "AI growth equity",
]


class AcceleratorScraper(BaseScraper):
    """Scrape AI-focused accelerators, investors, and principal investors."""

    async def run(self, search_terms: list[str] | None = None) -> list[Investor]:
        """
        Search for AI investors/accelerators and scrape their public profiles.
        Returns a list of Investor records.
        """
        terms = search_terms or INVESTOR_SEARCH_TERMS
        all_investors: list[Investor] = []
        seen_ids: set[str] = set()

        for term in terms:
            self.log.info(f"[SEARCH] Searching investors: \"{term}\"")
            profile_links = await self._search_investors(term)

            for link in profile_links:
                pid = link.split("/")[-1] if "/" in link else link
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)

                investor = await self._scrape_profile(link)
                if investor and investor.name:
                    all_investors.append(investor)
                    label = "[PRINCIPAL]" if investor.is_principal_investor else investor.investor_type
                    self.log.info(f"  [OK] {investor.name} ({label}) - {investor.location.city or 'Unknown'}")

        self.log.info(f"[TOTAL] Total investors/accelerators scraped: {len(all_investors)}")
        return all_investors

    async def _search_investors(self, term: str) -> list[str]:
        """Search PitchBook for investor profile URLs."""
        profile_links = []

        for page_num in range(1, config.MAX_SEARCH_PAGES + 1):
            # Try both 'investors' and 'limited-partners' type filters
            for search_type in ["investors", "limited-partners"]:
                url = f"{config.SEARCH_URL}?q={quote_plus(term)}&type={search_type}&page={page_num}"
                success = await self.goto(url)
                if not success:
                    continue

                html = await self.get_page_html()
                soup = BeautifulSoup(html, "lxml")

                links = set()
                # Look for investor profile links
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if any(p in href for p in ["/profiles/investor/", "/profiles/limited-partner/", "/profiles/advisor/"]):
                        full_url = href if href.startswith("http") else f"{config.BASE_URL}{href}"
                        links.add(full_url)

                if links:
                    profile_links.extend(links)
                    self.log.info(f"  Found {len(links)} investors on page {page_num} ({search_type})")

            if not profile_links:
                break

        return list(set(profile_links))

    async def _scrape_profile(self, url: str) -> Investor | None:
        """Scrape a single investor/accelerator profile page."""
        success = await self.goto(url)
        if not success:
            return None

        html = await self.get_page_html()
        soup = BeautifulSoup(html, "lxml")

        investor = Investor(url=url)
        investor.pitchbook_id = url.split("/")[-1] if "/" in url else ""

        # ── Name ─────────────────────────────────────────────────────
        investor.name = self._extract_text(soup, [
            "h1", "[data-test='entity-name']", ".profile-header h1",
            ".investor-name"
        ])

        # ── Description ──────────────────────────────────────────────
        investor.description = self._extract_text(soup, [
            "[data-test='description']", ".description-text",
            ".entity-description", "p.description"
        ])

        # ── Investor Type ────────────────────────────────────────────
        raw_type = self._extract_field(soup, [
            "Investor Type", "Type", "Organization Type", "Primary Type"
        ]).lower()

        investor.investor_type = self._classify_investor_type(raw_type)

        # ── Principal Investor Detection ─────────────────────────────
        investor.is_principal_investor = self._detect_principal_investor(soup, raw_type)

        # ── Location ─────────────────────────────────────────────────
        location_text = self._extract_field(soup, ["HQ Location", "Headquarters", "Location"])
        investor.location = self._parse_location(location_text)

        # ── AUM ──────────────────────────────────────────────────────
        investor.aum = self._extract_field(soup, [
            "AUM", "Assets Under Management", "Capital Under Management",
            "Total Fund Size", "Fund Size"
        ])

        # ── Focus Areas ──────────────────────────────────────────────
        focus_text = self._extract_field(soup, [
            "Investment Focus", "Sector Focus", "Industry Preferences", "Preferences"
        ])
        if focus_text:
            investor.focus_areas = [f.strip() for f in focus_text.split(",") if f.strip()]

        # ── Portfolio Companies ───────────────────────────────────────
        investor.portfolio_companies = self._extract_link_list(soup, [
            "Portfolio Companies", "Investments", "Active Portfolio"
        ])

        # ── Recent Investments ───────────────────────────────────────
        investor.recent_investments = await self._extract_investments(soup)

        return investor

    def _detect_principal_investor(self, soup: BeautifulSoup, raw_type: str) -> bool:
        """
        Detect if this is a principal investor.
        Principal investors are entities that invest their own capital
        (family offices, sovereign wealth funds, corporate investors, HNWIs).
        """
        principal_keywords = [
            "principal", "family office", "sovereign wealth",
            "corporate investor", "individual", "angel",
            "endowment", "pension", "insurance company",
            "limited partner"
        ]

        # Check type field
        if any(kw in raw_type for kw in principal_keywords):
            return True

        # Check page text for principal investor indicators
        page_text = soup.get_text().lower()
        principal_phrases = [
            "principal investor", "invests its own capital",
            "family office", "sovereign wealth fund",
            "direct investment", "balance sheet investor"
        ]
        return any(phrase in page_text for phrase in principal_phrases)

    def _classify_investor_type(self, raw_type: str) -> str:
        """Classify the investor into a standard type."""
        if any(t in raw_type for t in ["accelerator", "incubator"]):
            return "accelerator"
        elif "corporate" in raw_type or "cvc" in raw_type:
            return "cvc"
        elif "angel" in raw_type or "individual" in raw_type:
            return "angel"
        elif any(t in raw_type for t in ["private equity", "buyout", "pe "]):
            return "pe"
        elif any(t in raw_type for t in ["venture", "vc", "seed"]):
            return "vc"
        elif any(t in raw_type for t in ["family office", "sovereign", "pension", "endowment"]):
            return "principal"
        elif "growth" in raw_type:
            return "growth_equity"
        return raw_type or "unknown"

    async def _extract_investments(self, soup: BeautifulSoup) -> list[Investment]:
        """Extract recent investments from the profile page."""
        investments = []

        # Look for investment/deal tables
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows[1:6]:  # First 5 data rows
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    inv = Investment()
                    inv.company = cells[0].get_text(strip=True)
                    if len(cells) >= 2:
                        inv.amount = cells[1].get_text(strip=True)
                    if len(cells) >= 3:
                        inv.round_type = cells[2].get_text(strip=True)
                    if len(cells) >= 4:
                        inv.date = cells[3].get_text(strip=True)
                    if inv.company:
                        investments.append(inv)

        return investments

    # ── Parsing helpers (same as CompanyScraper) ─────────────────────────

    def _extract_text(self, soup: BeautifulSoup, selectors: list[str]) -> str:
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return ""

    def _extract_field(self, soup: BeautifulSoup, labels: list[str]) -> str:
        # "Poison pills" - if the value contains these, it's likely a captured section, not a value
        bad_substrings = ["Status", "Employees", "Deal Type", "Financing Rounds", "investors", "AUM", "Focus"]

        for label in labels:
            for dt in soup.find_all("dt"):
                if label.lower() in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        val = dd.get_text(strip=True)
                        if len(val) < 100: return val
            for th in soup.find_all("th"):
                if label.lower() in th.get_text(strip=True).lower():
                    td = th.find_next_sibling("td")
                    if td:
                        val = td.get_text(strip=True)
                        if len(val) < 100: return val
            for span in soup.find_all("span"):
                if label.lower() in span.get_text(strip=True).lower():
                    sibling = span.find_next_sibling(["span", "div"])
                    if sibling:
                        val = sibling.get_text(strip=True)
                        if len(val) < 100 and not any(b in val for b in bad_substrings):
                            return val
            for div in soup.find_all("div"):
                text = div.get_text(strip=True)
                if text.lower().startswith(label.lower()):
                    value = text[len(label):].strip().lstrip(":").strip()
                    if len(value) > 100: continue
                    if any(b in value for b in bad_substrings): continue
                    
                    # Heuristic: Check direct child text
                    child_text = "".join([c.strip() for c in div.find_all(string=True, recursive=False)])
                    if label.lower() in child_text.lower() and value:
                        return value
        return ""

    def _extract_link_list(self, soup: BeautifulSoup, labels: list[str]) -> list[str]:
        bad_containers = ["nav", "header", "footer", "menu"]
        bad_link_text = ["Log in", "Sign up", "Products", "Careers", "Contact", "Terms", "Privacy"]

        for label in labels:
            for el in soup.find_all(["dt", "th", "span", "div", "h3", "h4"]):
                if label.lower() == el.get_text(strip=True).lower().rstrip(":"):
                    parent = el.parent
                    if not parent: continue
                    
                    # Filter bad containers
                    parent_classes = " ".join(parent.get("class", [])).lower()
                    if any(cls in parent_classes for cls in bad_containers): continue
                    if parent.name in bad_containers: continue

                    items = []
                    for a in parent.find_all("a"):
                        text = a.get_text(strip=True)
                        href = a.get("href", "")
                        if not text or len(text) < 2: continue
                        if any(bad in text for bad in bad_link_text): continue
                        if "pitchbook.com" in href or "mailto:" in href: continue
                        items.append(text)

                    if items and len(items) < 50:
                        return items[:20]
        return []

    def _parse_location(self, location_str: str) -> Location:
        loc = Location()
        if not location_str:
            return loc
        parts = [p.strip() for p in location_str.split(",")]
        if len(parts) >= 3:
            loc.city, loc.state, loc.country = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            loc.city, loc.country = parts[0], parts[1]
        elif len(parts) == 1:
            loc.city = parts[0]
        return loc
