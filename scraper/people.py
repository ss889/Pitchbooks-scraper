"""
People scraper.

Extracts key people (founders, CEOs, partners, board members) from
AI company and investor profile pages found on PitchBook.
"""

import sys
from pathlib import Path
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from models.schemas import Person
from scraper.base import BaseScraper


PEOPLE_SEARCH_TERMS = [
    "AI CEO founder",
    "artificial intelligence investor partner",
    "machine learning executive",
    "generative AI founder",
    "AI venture capital partner",
]


class PeopleScraper(BaseScraper):
    """Scrape key people from PitchBook's public pages."""

    async def run(self, search_terms: list[str] | None = None) -> list[Person]:
        """
        Search for AI-related people and scrape their public profiles.
        Returns a list of Person records.
        """
        terms = search_terms or PEOPLE_SEARCH_TERMS
        all_people: list[Person] = []
        seen_names: set[str] = set()

        for term in terms:
            self.log.info(f"[SEARCH] Searching people: \"{term}\"")
            profile_links = await self._search_people(term)

            for link in profile_links:
                person = await self._scrape_person_profile(link)
                if person and person.name:
                    key = f"{person.name}|{person.company}".lower()
                    if key not in seen_names:
                        seen_names.add(key)
                        all_people.append(person)
                        self.log.info(f"  [OK] {person.name} - {person.title} @ {person.company}")

        # Also extract people from company/investor pages we visit
        self.log.info("Extracting people from AI company search results ...")
        company_people = await self._extract_people_from_entity_search("companies")
        for p in company_people:
            key = f"{p.name}|{p.company}".lower()
            if key not in seen_names:
                seen_names.add(key)
                all_people.append(p)

        self.log.info(f"📦 Total people scraped: {len(all_people)}")
        return all_people

    async def _search_people(self, term: str) -> list[str]:
        """Search PitchBook for people profile URLs."""
        profile_links = []

        for page_num in range(1, config.MAX_SEARCH_PAGES + 1):
            url = f"{config.SEARCH_URL}?q={quote_plus(term)}&type=people&page={page_num}"
            success = await self.goto(url)
            if not success:
                break

            html = await self.get_page_html()
            soup = BeautifulSoup(html, "lxml")

            links = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/profiles/person/" in href:
                    full_url = href if href.startswith("http") else f"{config.BASE_URL}{href}"
                    links.add(full_url)

            if not links:
                break

            profile_links.extend(links)
            self.log.info(f"  Found {len(links)} people on page {page_num}")

        return list(set(profile_links))

    async def _scrape_person_profile(self, url: str) -> Person | None:
        """Scrape a single person profile page."""
        success = await self.goto(url)
        if not success:
            return None

        html = await self.get_page_html()
        soup = BeautifulSoup(html, "lxml")

        person = Person()

        # Name
        person.name = self._extract_text(soup, [
            "h1", "[data-test='entity-name']", ".profile-header h1"
        ])

        # Title
        person.title = self._extract_text(soup, [
            ".current-title", "[data-test='current-title']", "h2",
            ".person-title"
        ])
        if not person.title:
            person.title = self._extract_field(soup, ["Title", "Current Title", "Position"])

        # Company
        person.company = self._extract_text(soup, [
            ".current-company a", "[data-test='current-company']"
        ])
        if not person.company:
            person.company = self._extract_field(soup, [
                "Current Company", "Company", "Organization", "Primary Affiliation"
            ])

        # Company type (try to infer)
        person.company_type = self._infer_company_type(soup)

        # Location
        person.location = self._extract_field(soup, ["Location", "HQ Location"])

        # LinkedIn
        for a in soup.find_all("a", href=True):
            if "linkedin.com" in a["href"]:
                person.linkedin = a["href"]
                break

        # Bio
        person.bio = self._extract_text(soup, [
            ".biography", "[data-test='biography']", ".person-bio",
            ".description-text"
        ])

        return person

    async def _extract_people_from_entity_search(self, entity_type: str) -> list[Person]:
        """
        Search for AI companies/investors and extract key people listed
        on their profile pages (management team, board, etc.).
        """
        people = []

        for term in config.AI_SEARCH_TERMS[:3]:  # Limit to first 3 terms
            url = f"{config.SEARCH_URL}?q={quote_plus(term)}&type={entity_type}&page=1"
            success = await self.goto(url)
            if not success:
                continue

            html = await self.get_page_html()
            soup = BeautifulSoup(html, "lxml")

            # Get first few profile links
            profile_links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if f"/profiles/company/" in href or "/profiles/investor/" in href:
                    full_url = href if href.startswith("http") else f"{config.BASE_URL}{href}"
                    profile_links.append(full_url)

            # Visit each profile and extract people
            for link in list(set(profile_links))[:5]:  # Max 5 per term
                success = await self.goto(link)
                if not success:
                    continue

                page_html = await self.get_page_html()
                page_soup = BeautifulSoup(page_html, "lxml")

                # Get entity name for company field
                entity_name = self._extract_text(page_soup, [
                    "h1", "[data-test='entity-name']"
                ])

                # Look for team/management sections
                extracted = self._extract_team_members(page_soup, entity_name)
                people.extend(extracted)

        return people

    def _extract_team_members(self, soup: BeautifulSoup, company_name: str) -> list[Person]:
        """Extract team members from a company/investor profile page."""
        people = []

        # Look for team sections
        team_sections = soup.find_all(["section", "div"], class_=lambda c: c and any(
            kw in str(c).lower() for kw in ["team", "people", "management", "board"]
        ))

        for section in team_sections:
            # Look for person cards/rows
            for card in section.find_all(["div", "tr", "li"]):
                name_el = card.find(["a", "span", "h3", "h4", "strong"])
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if not name or len(name) < 3 or len(name) > 80:
                    continue

                person = Person()
                person.name = name
                person.company = company_name

                # Try to find title
                title_el = card.find(["span", "p", "div"], class_=lambda c: c and "title" in str(c).lower())
                if title_el:
                    person.title = title_el.get_text(strip=True)

                # LinkedIn link
                for a in card.find_all("a", href=True):
                    if "linkedin.com" in a["href"]:
                        person.linkedin = a["href"]
                        break

                if person.name:
                    people.append(person)

        return people

    def _infer_company_type(self, soup: BeautifulSoup) -> str:
        """Try to infer if the person works at a startup, investor, or accelerator."""
        page_text = soup.get_text().lower()
        if any(kw in page_text for kw in ["venture capital", "vc firm", "investment firm"]):
            return "investor"
        elif any(kw in page_text for kw in ["accelerator", "incubator"]):
            return "accelerator"
        return "startup"

    # ── Parsing helpers ──────────────────────────────────────────────────

    def _extract_text(self, soup: BeautifulSoup, selectors: list[str]) -> str:
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return ""

    def _extract_field(self, soup: BeautifulSoup, labels: list[str]) -> str:
        for label in labels:
            for dt in soup.find_all("dt"):
                if label.lower() in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        return dd.get_text(strip=True)
            for th in soup.find_all("th"):
                if label.lower() in th.get_text(strip=True).lower():
                    td = th.find_next_sibling("td")
                    if td:
                        return td.get_text(strip=True)
            for span in soup.find_all("span"):
                if label.lower() in span.get_text(strip=True).lower():
                    sibling = span.find_next_sibling(["span", "div"])
                    if sibling:
                        return sibling.get_text(strip=True)
        return ""
