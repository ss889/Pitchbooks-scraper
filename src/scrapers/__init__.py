"""
Scrapers package for PitchBook AI News Intelligence.

Data Source Strategy:
---------------------
PRIMARY: PitchBook (90% effort)
- Company funding data
- Deal details
- Investor portfolios
- Geographic data

SECONDARY: RSS Feeds (10% effort, always accessible)
- TechCrunch AI/Startups
- VentureBeat AI
- MIT Technology Review

The RSS feeds provide narrative journalism to complement
PitchBook's structured data, giving newsletter creators
both the numbers AND the story.
"""

from .rss_scraper import RSSNewsScraper, RSS_SOURCES

__all__ = [
    "RSSNewsScraper",
    "RSS_SOURCES",
]
