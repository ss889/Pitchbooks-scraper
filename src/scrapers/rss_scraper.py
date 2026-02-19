"""
RSS Feed Scraper for AI Investment News.

Provides reliable, working data sources to complement PitchBook.
RSS feeds are publicly accessible and don't require authentication,
making them ideal for consistent newsletter content.

Selected Sources (complementing PitchBook, not duplicating):
1. TechCrunch AI/Startups - Breaking funding news
2. VentureBeat AI - Industry analysis and deals
3. The Information (free summaries) - Exclusive scoops

These sources focus on ACTUAL funding announcements that
PitchBook tracks, providing narrative context for the numbers.
"""

import feedparser
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_db
from scraper.ai_parser import AINewsParser

logger = logging.getLogger(__name__)


@dataclass
class RSSSource:
    """Configuration for an RSS feed source."""
    name: str
    feed_url: str
    priority: int  # Lower = higher priority
    enabled: bool = True
    category_filter: Optional[str] = None  # Only include items matching this


# RSS Sources ranked by newsletter value
# These complement PitchBook's deal data with narrative journalism
RSS_SOURCES = [
    RSSSource(
        name="techcrunch_ai",
        feed_url="https://techcrunch.com/category/artificial-intelligence/feed/",
        priority=1,
        enabled=True,
    ),
    RSSSource(
        name="techcrunch_startups",
        feed_url="https://techcrunch.com/category/startups/feed/",
        priority=2,
        enabled=True,
    ),
    RSSSource(
        name="venturebeat_ai",
        feed_url="https://venturebeat.com/category/ai/feed/",
        priority=3,
        enabled=True,
    ),
    # MIT Tech Review - For research-focused AI news
    RSSSource(
        name="mit_tech_review",
        feed_url="https://www.technologyreview.com/feed/",
        priority=4,
        enabled=True,
        category_filter="ai|artificial intelligence|machine learning",
    ),
]


class RSSNewsScraper:
    """
    Scrapes AI investment news from curated RSS feeds.
    
    For newsletter creators: These sources provide reliable,
    always-accessible articles that complement PitchBook's
    structured deal data with narrative journalism.
    """
    
    def __init__(self):
        self.db = get_db()
        self.parser = AINewsParser()
        self.sources = [s for s in RSS_SOURCES if s.enabled]
        self.log = logging.getLogger(self.__class__.__name__)
    
    async def run(self, max_per_source: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape all enabled RSS sources for AI news.
        
        Args:
            max_per_source: Maximum articles to process per feed
            
        Returns:
            List of inserted article records
        """
        all_articles = []
        
        # Sort by priority (lower = higher priority)
        sorted_sources = sorted(self.sources, key=lambda s: s.priority)
        
        for source in sorted_sources:
            self.log.info(f"[RSS] Fetching: {source.name}")
            try:
                articles = await self._scrape_feed(source, max_per_source)
                all_articles.extend(articles)
                self.log.info(f"  -> Got {len(articles)} new articles from {source.name}")
            except Exception as e:
                self.log.error(f"  Error scraping {source.name}: {e}")
        
        return all_articles
    
    async def _scrape_feed(self, source: RSSSource, max_items: int) -> List[Dict[str, Any]]:
        """Scrape a single RSS feed."""
        articles = []
        
        try:
            # Parse the feed
            feed = feedparser.parse(source.feed_url)
            
            if feed.bozo:
                self.log.warning(f"  Feed parsing issue: {feed.bozo_exception}")
            
            entries = feed.entries[:max_items]
            
            for entry in entries:
                try:
                    article = await self._process_entry(entry, source)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.log.debug(f"  Skip entry: {e}")
                    continue
                    
        except Exception as e:
            self.log.error(f"  Feed fetch error: {e}")
        
        return articles
    
    async def _process_entry(self, entry: Dict, source: RSSSource) -> Optional[Dict[str, Any]]:
        """
        Process a single RSS entry into an article.
        
        Filters for AI-relevance and validates URLs before storage.
        """
        # Extract basic info
        url = entry.get('link', '')
        title = entry.get('title', '')
        
        if not url or not title:
            return None
        
        # Check if already exists
        if self.db.article_exists(url):
            return None
        
        # Apply category filter if specified
        if source.category_filter:
            pattern = re.compile(source.category_filter, re.IGNORECASE)
            text_to_check = f"{title} {entry.get('summary', '')}"
            if not pattern.search(text_to_check):
                return None
        
        # Extract content
        summary = self._clean_html(entry.get('summary', ''))
        content = self._extract_content(entry)
        
        # Parse publication date
        pub_date = self._parse_date(entry)
        
        # Run through AI parser for relevance scoring
        parsed = self.parser.parse_article(title, content or summary, url)
        
        # Filter out low-relevance articles
        relevance = parsed.get('ai_relevance_score', 0)
        if relevance < 0.3:  # Threshold for AI relevance
            self.log.debug(f"  Low relevance ({relevance:.2f}): {title[:50]}")
            return None
        
        # Validate URL accessibility
        url_status = await self._validate_url(url)
        
        # Insert into database
        article_id = self.db.insert_article(
            url=url,
            title=title,
            summary=parsed.get('summary', summary[:500]),
            content=content,
            published_date=pub_date,
            ai_relevance_score=relevance,
            is_deal_news=int(parsed.get('is_deal_news', False)),
            url_status=url_status,
            source=source.name
        )
        
        if not article_id:
            return None
        
        # Add categories
        for category in parsed.get('ai_categories', []):
            self.db.add_article_category(article_id, category)
        
        # Insert deals if found
        for deal in parsed.get('deals', []):
            self.db.insert_deal(
                article_id=article_id,
                company_name=deal.get('company'),
                funding_amount=deal.get('amount_usd'),
                round_type=deal.get('round_type'),
                investors=', '.join(deal.get('investors', [])) if deal.get('investors') else None,
                announcement_date=deal.get('date') or pub_date
            )
        
        self.log.info(f"  [+] {title[:60]} (relevance: {relevance:.2f})")
        
        return {
            'id': article_id,
            'url': url,
            'title': title,
            'relevance': relevance,
            'source': source.name,
            'url_status': url_status
        }
    
    async def _validate_url(self, url: str, timeout: int = 10) -> str:
        """Validate URL accessibility and return status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=True,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0'}
                ) as response:
                    if response.status == 200:
                        return 'accessible'
                    elif response.status in (401, 402, 403):
                        return 'preview_only'
                    else:
                        return 'inaccessible'
        except Exception:
            return 'unchecked'
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from content."""
        if not html:
            return ""
        soup = BeautifulSoup(html, 'lxml')
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_content(self, entry: Dict) -> str:
        """Extract full content from RSS entry."""
        # Try content:encoded first (full article)
        if 'content' in entry and entry['content']:
            content = entry['content'][0].get('value', '')
            return self._clean_html(content)
        
        # Fall back to summary
        return self._clean_html(entry.get('summary', ''))
    
    def _parse_date(self, entry: Dict) -> Optional[str]:
        """Parse publication date from RSS entry."""
        for field in ['published_parsed', 'updated_parsed']:
            if field in entry and entry[field]:
                try:
                    dt = datetime(*entry[field][:6])
                    return dt.isoformat()
                except Exception:
                    continue
        
        # Try string dates
        for field in ['published', 'updated']:
            if field in entry:
                return entry[field]
        
        return datetime.now().isoformat()


async def main():
    """Run RSS scraper standalone."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    
    scraper = RSSNewsScraper()
    articles = await scraper.run(max_per_source=10)
    
    print(f"\n=== RSS Scrape Complete ===")
    print(f"New articles: {len(articles)}")
    
    for article in articles[:5]:
        print(f"  - {article['title'][:50]}... ({article['source']})")


if __name__ == "__main__":
    asyncio.run(main())
