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
        """
        Insert a news article, returns article_id if successful.
        
        For newsletter creators: This stores validated article data
        ready for content curation.
        
        Args:
            url: Article URL (will be validated)
            title: Article headline
            summary: Brief summary/excerpt
            content: Full article text
            published_date: When article was published
            ai_relevance_score: AI relevance score (0-1)
            is_deal_news: 1 if article contains deal info
            url_status: 'accessible', 'preview_only', 'inaccessible', 'unchecked'
            source: Data source (pitchbook, techcrunch_rss, etc.)
        """
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
        """
        Update URL accessibility status for an article.
        
        For newsletter creators: Ensures broken links are flagged
        so they can be filtered from newsletter content.
        
        Args:
            article_id: ID of the article to update
            url_status: 'accessible', 'preview_only', 'inaccessible'
        """
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
        """
        Retrieve articles with pagination, filtering, and search.
        
        Args:
            limit: Number of articles per page
            offset: Number of articles to skip
            category: Filter by AI category name
            min_relevance: Minimum relevance score (0-1)
            search: Search in title and content
            sort_by: "published_date" or "relevance" or "recent"
        """
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
                else:  # published_date (default)
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
        else:  # published_date (default)
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
            
            cursor.execute("""
                SELECT AVG(ai_relevance_score) FROM news_articles
            """)
            avg_relevance = cursor.fetchone()[0] or 0
            
            cursor.execute("""
                SELECT COUNT(*) FROM ai_categories
            """)
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
