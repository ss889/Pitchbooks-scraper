"""
Data schemas for PitchBook scraper output.

Provides dataclass definitions and JSON serialization helpers for all
scraped entity types: Companies, Accelerators/Investors, People, and News.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
import json


# ── Helpers ──────────────────────────────────────────────────────────────

def _now() -> str:
    """ISO timestamp for when a record was scraped."""
    return datetime.now().isoformat()


def to_json(records: list, path: str) -> None:
    """Write a list of dataclass records to a JSON file."""
    data = [asdict(r) for r in records]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Saved {len(data)} records -> {path}")


# ── Location ─────────────────────────────────────────────────────────────

@dataclass
class Location:
    city: str = ""
    state: str = ""
    country: str = ""


# ── Company ──────────────────────────────────────────────────────────────

@dataclass
class Company:
    name: str = ""
    pitchbook_id: str = ""
    url: str = ""
    description: str = ""
    founded: str = ""
    status: str = ""                # private | public | acquired
    industry: str = ""
    sector: str = ""
    location: Location = field(default_factory=Location)
    employees: str = ""
    total_funding: str = ""
    last_funding_round: str = ""
    last_funding_date: str = ""
    investors: list[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=_now)


# ── Investment / Deal ────────────────────────────────────────────────────

@dataclass
class Investment:
    company: str = ""
    amount: str = ""
    round_type: str = ""
    date: str = ""
    co_investors: list[str] = field(default_factory=list)


# ── Accelerator / Investor ───────────────────────────────────────────────

@dataclass
class Investor:
    name: str = ""
    pitchbook_id: str = ""
    url: str = ""
    investor_type: str = ""         # accelerator | vc | pe | cvc | angel | principal
    location: Location = field(default_factory=Location)
    description: str = ""
    focus_areas: list[str] = field(default_factory=list)
    aum: str = ""                   # assets under management
    portfolio_companies: list[str] = field(default_factory=list)
    recent_investments: list[Investment] = field(default_factory=list)
    is_principal_investor: bool = False
    scraped_at: str = field(default_factory=_now)


# ── Person ───────────────────────────────────────────────────────────────

@dataclass
class Person:
    name: str = ""
    title: str = ""
    company: str = ""
    company_type: str = ""          # startup | investor | accelerator
    location: str = ""
    linkedin: str = ""
    bio: str = ""
    scraped_at: str = field(default_factory=_now)


# ── Deal Info (embedded in news articles) ────────────────────────────────

@dataclass
class DealInfo:
    amount: str = ""
    round_type: str = ""
    investors: list[str] = field(default_factory=list)
    company: str = ""
    date: str = ""


# ── News Article ─────────────────────────────────────────────────────────

@dataclass
class NewsArticle:
    title: str = ""
    date: str = ""
    author: str = ""
    url: str = ""
    summary: str = ""
    full_text: str = ""
    companies_mentioned: list[str] = field(default_factory=list)
    deal_info: Optional[DealInfo] = None
    tags: list[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=_now)
