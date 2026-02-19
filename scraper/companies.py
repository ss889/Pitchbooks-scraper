"""
AI Company profile scraper.

Searches PitchBook for AI-related companies and extracts public profile data
including name, funding, industry, location, and investors.
"""

import sys
from pathlib import Path
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from models.schemas import Company, Location
from scraper.base import BaseScraper


class CompanyScraper(BaseScraper):
    """Scrape AI company profiles from PitchBook's public search and profile pages."""

    async def run(self, search_terms: list[str] | None = None) -> list[Company]:
        """
        Search for AI companies and scrape their public profiles.
        Returns a list of Company records.
        """
        terms = search_terms or config.AI_SEARCH_TERMS
        all_companies: list[Company] = []
        seen_ids: set[str] = set()

        for term in terms:
            self.log.info(f"[SEARCH] Searching companies: \"{term}\"")
            profile_links = await self._search_companies(term)

            for link in profile_links:
                # Deduplicate by profile URL
                pid = link.split("/")[-1] if "/" in link else link
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)

                company = await self._scrape_profile(link)
                if company and company.name:
                    all_companies.append(company)
                    self.log.info(f"  [OK] {company.name} ({company.status}) - {company.location.city or 'Unknown location'}")

        self.log.info(f"[TOTAL] Total companies scraped: {len(all_companies)}")
        return all_companies

    async def _search_companies(self, term: str) -> list[str]:
        """Search PitchBook and return a list of company profile URLs."""
        profile_links = []

        for page_num in range(1, config.MAX_SEARCH_PAGES + 1):
            url = f"{config.SEARCH_URL}?q={quote_plus(term)}&type=companies&page={page_num}"
            success = await self.goto(url)
            if not success:
                break

            html = await self.get_page_html()
            soup = BeautifulSoup(html, "lxml")

            # Look for profile links in search results
            links = set()
            for a in soup.select("a[href*='/profiles/company/']"):
                href = a.get("href", "")
                if href and "/profiles/company/" in href:
                    full_url = href if href.startswith("http") else f"{config.BASE_URL}{href}"
                    links.add(full_url)

            if not links:
                # Also try alternate selectors for search result items
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/profiles/company/" in href:
                        full_url = href if href.startswith("http") else f"{config.BASE_URL}{href}"
                        links.add(full_url)

            if not links:
                self.log.info(f"  No more results on page {page_num}")
                break

            profile_links.extend(links)
            self.log.info(f"  Found {len(links)} companies on page {page_num}")

        return profile_links

    async def _scrape_profile(self, url: str) -> Company | None:
        """Scrape a single company profile page."""
        success = await self.goto(url)
        if not success:
            return None

        html = await self.get_page_html()
        soup = BeautifulSoup(html, "lxml")

        company = Company(url=url)
        company.pitchbook_id = url.split("/")[-1] if "/" in url else ""

        # ── Name ─────────────────────────────────────────────────────
        company.name = self._extract_text(soup, [
            "h1", "[data-test='entity-name']", ".profile-header h1",
            ".company-name", "h1.header-title"
        ])

        # ── Description ──────────────────────────────────────────────
        company.description = self._extract_text(soup, [
            "[data-test='description']", ".description-text",
            ".entity-description", "p.description"
        ])

        # ── Status / Founded ─────────────────────────────────────────
        company.status = self._extract_field(soup, ["Status", "Ownership Status"])
        company.founded = self._extract_field(soup, ["Year Founded", "Founded"])

        # ── Industry / Sector ────────────────────────────────────────
        company.industry = self._extract_field(soup, ["Primary Industry", "Industry"])
        company.sector = self._extract_field(soup, ["Primary Sector", "Sector", "Vertical"])

        # ── Employees ────────────────────────────────────────────────
        company.employees = self._extract_field(soup, ["Employees", "Employee Count", "Number of Employees"])

        # ── Location ─────────────────────────────────────────────────
        location_text = self._extract_field(soup, ["HQ Location", "Headquarters", "Location"])
        company.location = self._parse_location(location_text)

        # ── Funding ──────────────────────────────────────────────────
        company.total_funding = self._extract_field(soup, [
            "Total Raised", "Total Funding", "Financing Status"
        ])
        company.last_funding_round = self._extract_field(soup, [
            "Last Financing Round", "Last Round", "Latest Round"
        ])
        company.last_funding_date = self._extract_field(soup, [
            "Last Financing Date", "Last Round Date"
        ])

        # ── Investors ────────────────────────────────────────────────
        company.investors = self._extract_list(soup, ["Investors", "Active Investors"])

        return company

    # ── Parsing helpers ──────────────────────────────────────────────────

    def _extract_text(self, soup: BeautifulSoup, selectors: list[str]) -> str:
        """Try multiple CSS selectors, return first match text."""
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return ""

    def _extract_field(self, soup: BeautifulSoup, labels: list[str]) -> str:
        """
        Find a labelled field in profile (e.g. "Year Founded: 2015").
        Looks for label text in <dt>, <th>, <span>, <div> and returns the adjacent value.
        """
        # "Poison pills" - if the value contains these, it's likely a captured section, not a value
        bad_substrings = ["Status", "Employees", "Deal Type", "Financing Rounds", "investors"]

        for label in labels:
            # Pattern 1: <dt>Label</dt><dd>Value</dd>
            for dt in soup.find_all("dt"):
                if label.lower() in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        val = dd.get_text(strip=True)
                        if len(val) < 100: return val

            # Pattern 2: <th>Label</th><td>Value</td>
            for th in soup.find_all("th"):
                if label.lower() in th.get_text(strip=True).lower():
                    td = th.find_next_sibling("td")
                    if td:
                        val = td.get_text(strip=True)
                        if len(val) < 100: return val

            # Pattern 3: <span class="label">Label</span> <span class="value">Value</span>
            for span in soup.find_all("span"):
                if label.lower() in span.get_text(strip=True).lower():
                    # Try next sibling span
                    next_span = span.find_next_sibling("span")
                    if next_span:
                        val = next_span.get_text(strip=True)
                        if len(val) < 100 and not any(b in val for b in bad_substrings):
                            return val
                    # Try next sibling div
                    next_div = span.find_next_sibling("div")
                    if next_div:
                        val = next_div.get_text(strip=True)
                        if len(val) < 100 and not any(b in val for b in bad_substrings):
                            return val

            # Pattern 4: Generic divs where text starts with label (e.g. "Founded: 2020")
            # We must be careful not to grab a parent container
            for div in soup.find_all("div"):
                text = div.get_text(strip=True)
                if text.lower().startswith(label.lower()):
                    # Potential match, but check if it's just the label + value
                    value = text[len(label):].strip().lstrip(":").strip()
                    
                    # Heuristic 1: Length check
                    if len(value) > 100:
                        continue
                        
                    # Heuristic 2: Poison pill check (does it contain other labels?)
                    if any(b in value for b in bad_substrings):
                        continue

                    # Heuristic 3: Check immediate child strings only (avoid grabbing nested children text)
                    child_text = "".join([c.strip() for c in div.find_all(string=True, recursive=False)])
                    if label.lower() in child_text.lower():
                         # This div *directly* contains the text, not just via children
                         pass
                    
                    if value:
                        return value

        return ""

    def _extract_list(self, soup: BeautifulSoup, labels: list[str]) -> list[str]:
        """Extract a list of items from a labelled section, avoiding navigation menus."""
        bad_containers = ["nav", "header", "footer", "menu"]
        bad_link_text = ["Log in", "Sign up", "Products", "Careers", "Contact", "Terms", "Privacy"]

        for label in labels:
            for el in soup.find_all(["dt", "th", "span", "div", "h3", "h4"]):
                if label.lower() == el.get_text(strip=True).lower().rstrip(":"):
                    parent = el.parent
                    if not parent:
                        continue
                        
                    # Check if parent looks like a main nav or footer
                    parent_classes = " ".join(parent.get("class", [])).lower()
                    if any(cls in parent_classes for cls in bad_containers):
                        continue
                        
                    parent_tag = parent.name
                    if parent_tag in bad_containers:
                        continue

                    # Extract links
                    items = []
                    for a in parent.find_all("a"):
                        text = a.get_text(strip=True)
                        href = a.get("href", "")
                        
                        # Filter out navigation links
                        if not text or len(text) < 2: continue
                        if any(bad in text for bad in bad_link_text): continue
                        if "pitchbook.com" in href or "mailto:" in href: continue
                        
                        items.append(text)

                    if items and len(items) < 50: # If > 50, it's probably a site map
                        return items
        return []

    def _parse_location(self, location_str: str) -> Location:
        """Parse a location string like 'San Francisco, CA, US' into a Location."""
        loc = Location()
        if not location_str:
            return loc
        parts = [p.strip() for p in location_str.split(",")]
        if len(parts) >= 3:
            loc.city = parts[0]
            loc.state = parts[1]
            loc.country = parts[2]
        elif len(parts) == 2:
            loc.city = parts[0]
            loc.country = parts[1]
        elif len(parts) == 1:
            loc.city = parts[0]
        return loc
