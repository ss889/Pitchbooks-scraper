"""
================================================================================
AI INVESTMENT NEWSLETTER PLATFORM - CONSOLIDATED CODEBASE
================================================================================

Repository: https://github.com/ss889/Pitchbooks-scraper
Dashboard: https://ss889.github.io/Pitchbooks-scraper/

This file contains all core Python code concatenated for reference/upload.
Files included:
1. db.py - SQLite database layer
2. api.py - FastAPI REST server
3. scheduler.py - APScheduler task automation
4. src/utils/url_validator.py - URL validation utilities
5. src/scrapers/rss_scraper.py - RSS feed scraper
6. scraper/ai_parser.py - AI relevance scoring

================================================================================
"""


# ==============================================================================
# FILE: db.py
# Description: SQLite Database module for AI news intelligence platform
# ==============================================================================

"""
SQLite Database module for AI news intelligence platform.

Handles all database operations including initialization, schema creation,
and CRUD operations for news, companies, deals, and investors.
"""

import sqlite3
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger("database")

# Database path
DB_PATH = Path(__file__).parent / "ai_news.db"


class DatabaseManager:
    """Manages SQLite database for AI news intelligence."""
    
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database with schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # News Articles table (deduplicated by URL hash)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    url_hash TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT,
                    content TEXT,
                    published_date TEXT,
                    scraped_date TEXT NOT NULL,
                    source TEXT,
                    ai_relevance_score REAL,
                    is_deal_news INTEGER DEFAULT 0,
                    url_status TEXT DEFAULT 'unchecked',
                    url_last_checked TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add url_status column if it doesn't exist (migration)
            try:
                cursor.execute("ALTER TABLE news_articles ADD COLUMN url_status TEXT DEFAULT 'unchecked'")
            except sqlite3.OperationalError:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE news_articles ADD COLUMN url_last_checked TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Deals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    company_name TEXT,
                    funding_amount REAL,
                    funding_currency TEXT DEFAULT 'USD',
                    round_type TEXT,
                    investors TEXT,
                    announcement_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES news_articles(id)
                )
            """)
            
            # AI Tags/Categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    parent_id INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES ai_categories(id)
                )
            """)
            
            # Article to AI Category mapping
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS article_categories (
                    article_id INTEGER,
                    category_id INTEGER,
                    weight REAL DEFAULT 1.0,
                    PRIMARY KEY (article_id, category_id),
                    FOREIGN KEY (article_id) REFERENCES news_articles(id),
                    FOREIGN KEY (category_id) REFERENCES ai_categories(id)
                )
            """)
            
            # Companies extracted from news
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    funding_amount REAL,
                    location TEXT,
                    status TEXT,
                    website TEXT,
                    first_mentioned TEXT,
                    last_mentioned TEXT,
                    mention_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Investors/VCs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    investor_type TEXT,
                    location TEXT,
                    portfolio_companies TEXT,
                    recent_investments TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Article mentions mapping
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS article_mentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    entity_type TEXT,
                    entity_name TEXT,
                    entity_id INTEGER,
                    FOREIGN KEY (article_id) REFERENCES news_articles(id)
                )
            """)
            
            # Create indices for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_hash ON news_articles(url_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_date ON news_articles(published_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraped_date ON news_articles(scraped_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_relevance ON news_articles(ai_relevance_score DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deal_news ON news_articles(is_deal_news)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_categories ON article_categories(article_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_mentions ON article_mentions(article_id, entity_type)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def _get_url_hash(self, url: str) -> str:
        """Generate hash of URL for deduplication."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def article_exists(self, url: str) -> bool:
        """Check if article already exists by URL."""
        url_hash = self._get_url_hash(url)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM news_articles WHERE url_hash = ?", (url_hash,))
            return cursor.fetchone() is not None
    
    def insert_article(self, 
                      url: str,
                      title: str,
                      summary: str = "",
                      content: str = "",
                      published_date: Optional[str] = None,
                      ai_relevance_score: float = 0.0,
                      is_deal_news: int = 0,
                      url_status: str = "unchecked",
                      source: str = None) -> Optional[int]:
        """Insert a news article, returns article_id if successful."""
        if self.article_exists(url):
            logger.debug(f"Article already exists: {url}")
            return None
        
        url_hash = self._get_url_hash(url)
        scraped_date = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO news_articles 
                    (url, url_hash, title, summary, content, published_date, 
                     scraped_date, ai_relevance_score, is_deal_news, url_status, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (url, url_hash, title, summary, content, published_date,
                      scraped_date, ai_relevance_score, is_deal_news, url_status, source))
                
                conn.commit()
                article_id = cursor.lastrowid
                logger.info(f"Inserted article: {title[:60]} (ID: {article_id})")
                return article_id
            except sqlite3.IntegrityError as e:
                logger.warning(f"Integrity error inserting article: {e}")
                return None
    
    def insert_deal(self, article_id: int, company_name: str, 
                   funding_amount: Optional[float] = None,
                   funding_currency: str = "USD",
                   round_type: Optional[str] = None,
                   investors: Optional[str] = None,
                   announcement_date: Optional[str] = None) -> Optional[int]:
        """Insert deal information. Returns deal_id if successful."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO deals
                    (article_id, company_name, funding_amount, funding_currency, 
                     round_type, investors, announcement_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (article_id, company_name, funding_amount, funding_currency,
                      round_type, investors, announcement_date))
                
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                logger.error(f"Error inserting deal: {e}")
                return None
    
    def update_url_status(self, article_id: int, url_status: str) -> bool:
        """Update URL accessibility status for an article."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE news_articles 
                    SET url_status = ?, url_last_checked = ?
                    WHERE id = ?
                """, (url_status, datetime.now().isoformat(), article_id))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Error updating URL status: {e}")
                return False
    
    def get_articles_by_url_status(self, url_status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get articles filtered by URL status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM news_articles 
                WHERE url_status = ?
                ORDER BY published_date DESC
                LIMIT ?
            """, (url_status, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_unchecked_articles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get articles that need URL validation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM news_articles 
                WHERE url_status = 'unchecked' OR url_status IS NULL
                ORDER BY scraped_date DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def add_article_category(self, article_id: int, category_name: str, weight: float = 1.0) -> bool:
        """Add category to article. Creates category if doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get or create category
            cursor.execute("SELECT id FROM ai_categories WHERE name = ?", (category_name,))
            cat_row = cursor.fetchone()
            if cat_row:
                category_id = cat_row[0]
            else:
                cursor.execute("INSERT INTO ai_categories (name) VALUES (?)", (category_name,))
                conn.commit()
                category_id = cursor.lastrowid
            
            # Add article-category mapping
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO article_categories (article_id, category_id, weight)
                    VALUES (?, ?, ?)
                """, (article_id, category_id, weight))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error adding category: {e}")
                return False
    
    def get_articles_count(self, category: Optional[str] = None,
                          min_relevance: float = 0.0) -> int:
        """Get total count of articles with optional filters."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if category:
                cursor.execute("""
                    SELECT COUNT(DISTINCT a.id) FROM news_articles a
                    JOIN article_categories ac ON a.id = ac.article_id
                    JOIN ai_categories c ON ac.category_id = c.id
                    WHERE c.name = ? AND a.ai_relevance_score >= ?
                """, (category, min_relevance))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM news_articles
                    WHERE ai_relevance_score >= ?
                """, (min_relevance,))
            
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def get_articles(self, limit: int = 100, offset: int = 0, 
                    category: Optional[str] = None,
                    min_relevance: float = 0.0,
                    search: Optional[str] = None,
                    sort_by: str = "published_date") -> List[Dict[str, Any]]:
        """Retrieve articles with pagination, filtering, and search."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            order_by = self._get_order_by(sort_by)
            
            if category:
                sql = """
                    SELECT DISTINCT a.* FROM news_articles a
                    JOIN article_categories ac ON a.id = ac.article_id
                    JOIN ai_categories c ON ac.category_id = c.id
                    WHERE c.name = ? AND a.ai_relevance_score >= ?
                """
                params = [category, min_relevance]
                
                if search:
                    sql += " AND (a.title LIKE ? OR a.content LIKE ?)"
                    search_term = f"%{search}%"
                    params.extend([search_term, search_term])
                
                sql += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                cursor.execute(sql, params)
            else:
                sql = "SELECT * FROM news_articles WHERE ai_relevance_score >= ?"
                params = [min_relevance]
                
                if search:
                    sql += " AND (title LIKE ? OR content LIKE ?)"
                    search_term = f"%{search}%"
                    params.extend([search_term, search_term])
                
                sql += " ORDER BY "
                if sort_by == "relevance":
                    sql += "ai_relevance_score DESC, published_date DESC"
                elif sort_by == "recent":
                    sql += "scraped_date DESC, published_date DESC"
                else:
                    sql += "published_date DESC, scraped_date DESC"
                
                sql += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                cursor.execute(sql, params)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def _get_order_by(self, sort_by: str) -> str:
        """Get ORDER BY clause based on sort parameter."""
        if sort_by == "relevance":
            return "a.ai_relevance_score DESC, a.published_date DESC"
        elif sort_by == "recent":
            return "a.scraped_date DESC, a.published_date DESC"
        else:
            return "a.published_date DESC, a.scraped_date DESC"
    
    def get_deals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent deals with article info."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*, a.title, a.published_date, a.url
                FROM deals d
                JOIN news_articles a ON d.article_id = a.id
                WHERE d.funding_amount IS NOT NULL
                ORDER BY d.announcement_date DESC, a.published_date DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_deals_paginated(self, limit: int = 50, offset: int = 0,
                           min_amount: Optional[float] = None,
                           search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get paginated deals with optional filtering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            where_clauses = ["d.funding_amount IS NOT NULL"]
            params = []
            
            if min_amount:
                where_clauses.append("d.funding_amount >= ?")
                params.append(min_amount)
            
            if search:
                where_clauses.append("(d.company_name LIKE ? OR a.title LIKE ?)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            where_sql = " AND ".join(where_clauses)
            params.extend([limit, offset])
            
            cursor.execute(f"""
                SELECT d.*, a.title, a.published_date, a.url
                FROM deals d
                JOIN news_articles a ON d.article_id = a.id
                WHERE {where_sql}
                ORDER BY d.announcement_date DESC, a.published_date DESC
                LIMIT ? OFFSET ?
            """, params)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_deals_count(self, min_amount: Optional[float] = None,
                       search: Optional[str] = None) -> int:
        """Get total count of deals."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            where_clauses = ["d.funding_amount IS NOT NULL"]
            params = []
            
            if min_amount:
                where_clauses.append("d.funding_amount >= ?")
                params.append(min_amount)
            
            if search:
                where_clauses.append("(d.company_name LIKE ? OR a.title LIKE ?)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            where_sql = " AND ".join(where_clauses)
            
            cursor.execute(f"""
                SELECT COUNT(DISTINCT d.id)
                FROM deals d
                JOIN news_articles a ON d.article_id = a.id
                WHERE {where_sql}
            """, params)
            
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all AI categories with article counts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name, COUNT(DISTINCT ac.article_id) as article_count
                FROM ai_categories c
                LEFT JOIN article_categories ac ON c.id = ac.category_id
                GROUP BY c.id, c.name
                ORDER BY article_count DESC, c.name
            """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM news_articles")
            total_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM deals WHERE funding_amount IS NOT NULL")
            total_deals = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM companies")
            total_companies = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM investors")
            total_investors = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(funding_amount) FROM deals WHERE funding_amount IS NOT NULL")
            total_funding = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(ai_relevance_score) FROM news_articles")
            avg_relevance = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM ai_categories")
            total_categories = cursor.fetchone()[0] or 0
            
            return {
                "total_articles": total_articles,
                "total_deals": total_deals,
                "total_companies": total_companies,
                "total_investors": total_investors,
                "total_funding_usd": total_funding,
                "avg_relevance_score": avg_relevance,
                "total_categories": total_categories
            }


# Singleton instance
_db: Optional[DatabaseManager] = None

def get_db() -> DatabaseManager:
    """Get or create database connection."""
    global _db
    if _db is None:
        _db = DatabaseManager()
    return _db


# ==============================================================================
# FILE: src/utils/url_validator.py
# Description: URL Validation Utilities for PitchBook Scraper
# ==============================================================================

"""
URL Validation Utilities for PitchBook Scraper.

Ensures every article URL is verified before storage,
supporting the newsletter workflow where broken links
are unacceptable.
"""

import asyncio
import logging
import aiohttp
from typing import Optional, Tuple
from urllib.parse import urlparse
from enum import Enum

logger = logging.getLogger(__name__)


class URLStatus(Enum):
    """URL accessibility status for newsletter content tracking."""
    ACCESSIBLE = "accessible"       # Full content available
    PREVIEW_ONLY = "preview_only"   # Paywall/login required
    INACCESSIBLE = "inaccessible"   # 404, timeout, or error
    UNCHECKED = "unchecked"         # Not yet validated


async def validate_url(
    url: str,
    timeout: int = 10,
    follow_redirects: bool = True
) -> Tuple[URLStatus, Optional[int], Optional[str]]:
    """
    Validate a URL and determine its accessibility status.
    
    Returns:
        Tuple of (URLStatus, status_code, final_url after redirects)
    """
    if not url or not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL format: {url}")
        return URLStatus.INACCESSIBLE, None, None
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=follow_redirects,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            ) as response:
                status_code = response.status
                final_url = str(response.url)
                
                if status_code == 200:
                    return URLStatus.ACCESSIBLE, status_code, final_url
                elif status_code in (401, 402, 403):
                    return URLStatus.PREVIEW_ONLY, status_code, final_url
                elif status_code == 404:
                    return URLStatus.INACCESSIBLE, status_code, final_url
                elif status_code in (301, 302, 307, 308):
                    return URLStatus.ACCESSIBLE, status_code, final_url
                else:
                    logger.warning(f"Unexpected status {status_code} for {url}")
                    return URLStatus.INACCESSIBLE, status_code, final_url
                    
    except asyncio.TimeoutError:
        logger.warning(f"Timeout validating URL: {url}")
        return URLStatus.INACCESSIBLE, None, None
    except aiohttp.ClientError as e:
        logger.warning(f"Client error validating {url}: {e}")
        return URLStatus.INACCESSIBLE, None, None
    except Exception as e:
        logger.error(f"Unexpected error validating {url}: {e}")
        return URLStatus.INACCESSIBLE, None, None


def validate_url_sync(url: str, timeout: int = 10) -> Tuple[URLStatus, Optional[int], Optional[str]]:
    """Synchronous wrapper for URL validation."""
    import requests
    
    if not url or not url.startswith(('http://', 'https://')):
        return URLStatus.INACCESSIBLE, None, None
    
    try:
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        status_code = response.status_code
        final_url = response.url
        
        if status_code == 200:
            return URLStatus.ACCESSIBLE, status_code, str(final_url)
        elif status_code in (401, 402, 403):
            return URLStatus.PREVIEW_ONLY, status_code, str(final_url)
        else:
            return URLStatus.INACCESSIBLE, status_code, str(final_url)
            
    except requests.Timeout:
        return URLStatus.INACCESSIBLE, None, None
    except requests.RequestException:
        return URLStatus.INACCESSIBLE, None, None


def is_valid_url_format(url: str) -> bool:
    """Check if URL has valid format (doesn't verify accessibility)."""
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """Normalize URL for consistent storage and deduplication."""
    if not url:
        return url
        
    parsed = urlparse(url)
    
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    if netloc.endswith(':80') and scheme == 'http':
        netloc = netloc[:-3]
    elif netloc.endswith(':443') and scheme == 'https':
        netloc = netloc[:-4]
    
    path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
    
    normalized = f"{scheme}://{netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized


async def batch_validate_urls(urls: list, max_concurrent: int = 5) -> dict:
    """Validate multiple URLs concurrently."""
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}
    
    async def validate_with_semaphore(url: str):
        async with semaphore:
            status, _, _ = await validate_url(url)
            return url, status
    
    tasks = [validate_with_semaphore(url) for url in urls]
    completed = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in completed:
        if isinstance(result, Exception):
            continue
        url, status = result
        results[url] = status
    
    return results


# ==============================================================================
# FILE: src/scrapers/rss_scraper.py
# Description: RSS Feed Scraper for AI Investment News
# ==============================================================================

"""
RSS Feed Scraper for AI Investment News.

Provides reliable, working data sources to complement PitchBook.
RSS feeds are publicly accessible and don't require authentication.
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

logger = logging.getLogger(__name__)


@dataclass
class RSSSource:
    """Configuration for an RSS feed source."""
    name: str
    feed_url: str
    priority: int
    enabled: bool = True
    category_filter: Optional[str] = None


# RSS Sources ranked by newsletter value
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
    RSSSource(
        name="mit_tech_review",
        feed_url="https://www.technologyreview.com/feed/",
        priority=4,
        enabled=True,
        category_filter="ai|artificial intelligence|machine learning",
    ),
]


class RSSNewsScraper:
    """Scrapes AI investment news from curated RSS feeds."""
    
    def __init__(self):
        # Note: In actual usage, import from db module
        # self.db = get_db()
        # self.parser = AINewsParser()
        self.sources = [s for s in RSS_SOURCES if s.enabled]
        self.log = logging.getLogger(self.__class__.__name__)
    
    async def run(self, max_per_source: int = 20) -> List[Dict[str, Any]]:
        """Scrape all enabled RSS sources for AI news."""
        all_articles = []
        
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
        """Process a single RSS entry into an article."""
        url = entry.get('link', '')
        title = entry.get('title', '')
        
        if not url or not title:
            return None
        
        # Apply category filter if specified
        if source.category_filter:
            pattern = re.compile(source.category_filter, re.IGNORECASE)
            text_to_check = f"{title} {entry.get('summary', '')}"
            if not pattern.search(text_to_check):
                return None
        
        summary = self._clean_html(entry.get('summary', ''))
        content = self._extract_content(entry)
        pub_date = self._parse_date(entry)
        url_status = await self._validate_url(url)
        
        return {
            'url': url,
            'title': title,
            'summary': summary[:500],
            'content': content,
            'published_date': pub_date,
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
        if 'content' in entry and entry['content']:
            content = entry['content'][0].get('value', '')
            return self._clean_html(content)
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
        
        for field in ['published', 'updated']:
            if field in entry:
                return entry[field]
        
        return datetime.now().isoformat()


# ==============================================================================
# FILE: scraper/ai_parser.py
# Description: AI News Parser - Intelligent extraction and relevance scoring
# ==============================================================================

"""
AI News Parser – Intelligent extraction of deal information,
companies, investors, and relevance scoring from news articles.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("ai_parser")


class AINewsParser:
    """Parse news articles for AI-specific deal and company information."""
    
    # AI Technology Categories
    AI_CATEGORIES = {
        "generative_ai": {
            "keywords": ["generative ai", "gpt", "claude", "gemini", "grok", "llm", "large language model",
                        "text generation", "image generation", "diffusion", "transformer"],
            "weight": 1.0
        },
        "machine_learning": {
            "keywords": ["machine learning", "ml", "neural network", "deep learning", "training data",
                        "model training", "supervised learning", "unsupervised learning"],
            "weight": 0.9
        },
        "computer_vision": {
            "keywords": ["computer vision", "object detection", "image recognition", "video analysis",
                        "visual", "cv model", "vision transformer"],
            "weight": 0.85
        },
        "nlp": {
            "keywords": ["natural language", "nlp", "language model", "text analysis", "sentiment analysis",
                        "voice", "speech recognition", "transcription"],
            "weight": 0.85
        },
        "ai_infrastructure": {
            "keywords": ["gpu", "tpu", "accelerator", "inference", "model serving", "mlops", "computational",
                        "cloud compute", "distributed training", "vector database", "embedding"],
            "weight": 1.0
        },
        "ai_agents": {
            "keywords": ["ai agent", "autonomous agent", "reasoning", "multi-step", "agentic", "agent engineering",
                        "task automation", "workflow automation"],
            "weight": 1.0
        },
        "robotics": {
            "keywords": ["robotics", "robot", "autonomous robot", "robot learning", "embodied ai"],
            "weight": 0.8
        },
        "ai_safety": {
            "keywords": ["ai safety", "alignment", "bias detection", "safety", "fairness", "interpretability",
                        "explainability", "responsible ai", "ethics"],
            "weight": 0.9
        },
        "enterprise_ai": {
            "keywords": ["enterprise ai", "business ai", "enterprise software", "saas", "b2b", "copilot",
                        "workplace", "productivity", "workflow"],
            "weight": 0.85
        }
    }
    
    # Funding patterns
    FUNDING_PATTERNS = [
        r'\$(\d+\.?\d*)\s*(?:million|m|bn|b|k)',
        r'(?:raises?|secured?|closed|obtained?|announced?)\s+\$(\d+\.?\d*)\s*(?:million|m|bn|b|k)',
        r'(?:series|round)\s*[a-z]\s*(?:of|worth)?\s*\$(\d+\.?\d*)\s*(?:million|m|bn|b|k)',
    ]
    
    FUNDING_MULTIPLIERS = {
        'k': 1_000,
        'm': 1_000_000,
        'million': 1_000_000,
        'b': 1_000_000_000,
        'bn': 1_000_000_000,
    }
    
    # Round types
    ROUND_PATTERNS = {
        'seed': r'(?:seed\s*round|seed\s*funding)',
        'series_a': r'(?:series\s*a|\$series\s*a)',
        'series_b': r'(?:series\s*b)',
        'series_c': r'(?:series\s*c)',
        'series_d': r'(?:series\s*d)',
        'ipo': r'(?:ipo|initial\s*public\s*offering|goes?\s*public)',
        'acquisition': r'(?:acquired?|acquisition|taken\s*over)',
        'merger': r'(?:merged?|merger)',
    }
    
    # Major AI companies and investors to track
    MAJOR_AI_COMPANIES = {
        "openai", "anthropic", "google", "meta", "microsoft", "tesla", "nvidia",
        "groq", "together", "cohere", "stability", "hugging face", "mistral",
        "aleph alpha", "adept", "jasper", "copy.ai", "perplexity", "scale ai",
        "databricks", "modal", "vllm", "fireworks", "novita", "sam altman",
    }
    
    MAJOR_INVESTORS = {
        "sequoia", "a16z", "andreessen horowitz", "benchmark", "greylock", "khosla",
        "redpoint", "menlo", "spark", "vertex", "bessemer", "lightspeed", "insight",
        "accel", "fb fund", "google ventures", "microsoft venture", "openai startup",
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def parse_article(self, title: str, content: str, url: str = "") -> Dict:
        """Comprehensive parse of a news article."""
        text = f"{title} {content}".lower()
        
        relevance_score = self._calculate_relevance(title, text)
        categories = self._extract_categories(text)
        is_deal_news = self._is_deal_news(text)
        deals = self._extract_deals(text, title) if is_deal_news else []
        companies = self._extract_companies(text)
        investors = self._extract_investors(text)
        summary = self._create_summary(title, content, deals, companies)
        
        return {
            'ai_relevance_score': relevance_score,
            'ai_categories': categories,
            'is_deal_news': is_deal_news,
            'deals': deals,
            'companies': companies,
            'investors': investors,
            'summary': summary
        }
    
    def _calculate_relevance(self, title: str, text: str) -> float:
        """Calculate AI relevance score (0-1)."""
        score = 0.0
        text_lower = text.lower()
        title_lower = title.lower()
        
        ai_core = ["artificial intelligence", "ai", "machine learning", "neural", "deep learning"]
        if any(kw in title_lower for kw in ai_core):
            score += 0.5
        if any(kw in text_lower for kw in ai_core):
            score += 0.3
        
        category_weighted_score = 0.0
        for category, data in self.AI_CATEGORIES.items():
            keywords = data['keywords']
            weight = data['weight']
            
            if any(kw in text_lower for kw in keywords):
                category_weighted_score = max(category_weighted_score, weight)
        
        if category_weighted_score > 0:
            score += (category_weighted_score / 1.0) * 0.2
        
        if self._is_deal_news(text):
            score += 0.15
        
        if self._extract_funding_amount(text):
            score += 0.1
        
        return min(1.0, score)
    
    def _extract_categories(self, text: str) -> List[str]:
        """Extract relevant AI categories from text."""
        categories = []
        text_lower = text.lower()
        
        for category, data in self.AI_CATEGORIES.items():
            keywords = data['keywords']
            if any(kw in text_lower for kw in keywords):
                categories.append(category)
        
        return categories
    
    def _is_deal_news(self, text: str) -> bool:
        """Determine if this is deal/funding news."""
        deal_keywords = [
            "raises", "raised", "funding", "investment", "funded", "acquir",
            "merger", "ipo", "series", "seed round", "venture capital",
            "round of funding", "million", "billion", "acquisition",
        ]
        
        return any(kw in text for kw in deal_keywords)
    
    def _extract_funding_amount(self, text: str) -> Optional[Tuple[float, str]]:
        """Extract funding amount. Returns (amount_usd, original_text)."""
        for pattern in self.FUNDING_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.group(1))
                    multiplier_text = match.group(0).lower()
                    
                    multiplier = 1
                    for key, mult in self.FUNDING_MULTIPLIERS.items():
                        if key in multiplier_text:
                            multiplier = mult
                            break
                    
                    amount_usd = amount * multiplier
                    return (amount_usd, match.group(0))
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def _extract_deals(self, text: str, title: str) -> List[Dict]:
        """Extract deal information from article."""
        deals = []
        
        funding = self._extract_funding_amount(text)
        if not funding:
            return deals
        
        amount_usd, amount_text = funding
        company = self._extract_primary_company(text)
        if not company:
            company = self._extract_company_from_title(title)
        
        round_type = self._extract_round_type(text)
        investors = self._extract_investors(text)
        date = self._extract_date(text)
        
        if company:
            deals.append({
                'company': company,
                'amount_usd': amount_usd,
                'amount_text': amount_text,
                'round_type': round_type,
                'investors': investors,
                'date': date,
                'confidence': 0.8 if company and amount_usd else 0.5
            })
        
        return deals
    
    def _extract_companies(self, text: str) -> List[str]:
        """Extract mentioned companies."""
        companies = []
        
        for company in self.MAJOR_AI_COMPANIES:
            pattern = r'\b' + company + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                companies.append(company.title())
        
        capitalized = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\b', text)
        for cap in capitalized[:10]:
            if len(cap) > 2 and cap not in companies and cap not in ["The", "And", "For"]:
                if cap not in text[:100]:
                    companies.append(cap)
        
        return list(set(companies))[:15]
    
    def _extract_investors(self, text: str) -> List[str]:
        """Extract mentioned investors."""
        investors = []
        
        for investor in self.MAJOR_INVESTORS:
            pattern = r'\b' + investor + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                investors.append(investor.title())
        
        return list(set(investors))
    
    def _extract_round_type(self, text: str) -> Optional[str]:
        """Identify funding round type."""
        for round_name, pattern in self.ROUND_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return round_name
        return None
    
    def _extract_primary_company(self, text: str) -> Optional[str]:
        """Extract the main company being discussed."""
        patterns = [
            r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:raises?|announces?|secured?)',
            r'(?:startup|company)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_company_from_title(self, title: str) -> Optional[str]:
        """Extract company name from article title."""
        patterns = [
            r'^\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                name = match.group(1)
                if len(name) > 2:
                    return name
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Try to extract publication/announcement date."""
        patterns = [
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _create_summary(self, title: str, content: str, deals: List[Dict], companies: List[str]) -> str:
        """Create a concise summary highlighting key information."""
        summary_parts = [title]
        
        if deals:
            for deal in deals:
                if deal.get('company') and deal.get('amount_usd'):
                    summary_parts.append(
                        f"{deal['company']} raised {deal['amount_text']} "
                        f"({deal.get('round_type', 'funding')})"
                    )
        
        if companies:
            summary_parts.append(f"Key companies: {', '.join(companies[:5])}")
        
        return " | ".join(summary_parts[:3])


# ==============================================================================
# END OF CONSOLIDATED CODE
# ==============================================================================
"""
Usage:
- Import specific classes/functions as needed
- DatabaseManager, get_db() for database operations
- URLStatus, validate_url(), batch_validate_urls() for URL validation
- RSSNewsScraper for RSS feed scraping
- AINewsParser for article analysis

Example:
    from consolidated_code import DatabaseManager, AINewsParser, RSSNewsScraper
    
    db = DatabaseManager()
    parser = AINewsParser()
    
    result = parser.parse_article(title, content, url)
    article_id = db.insert_article(url=url, title=title, ...)
"""
