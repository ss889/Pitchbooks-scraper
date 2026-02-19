"""
Tests for database operations.

These tests verify the database layer works correctly for
storing and retrieving AI news articles and deals.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import DatabaseManager


class TestDatabaseInit:
    """Test database initialization."""
    
    def test_creates_tables(self, temp_db):
        """Database should create all required tables."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'news_articles' in tables
            assert 'deals' in tables
            assert 'companies' in tables
            assert 'investors' in tables
    
    def test_news_articles_has_url_status(self, temp_db):
        """news_articles table should have url_status column."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(news_articles)")
            columns = [row[1] for row in cursor.fetchall()]
            
            assert 'url_status' in columns
            assert 'url_last_checked' in columns


class TestArticleOperations:
    """Test article CRUD operations."""
    
    def test_insert_article(self, temp_db, sample_article):
        """Should insert a new article and return its ID."""
        article_id = temp_db.insert_article(
            url=sample_article['url'],
            title=sample_article['title'],
            summary=sample_article['summary'],
            content=sample_article['content'],
            published_date=sample_article['published_date'],
            ai_relevance_score=sample_article['ai_relevance_score'],
            is_deal_news=sample_article['is_deal_news'],
            source=sample_article['source']
        )
        
        assert article_id is not None
        assert article_id > 0
    
    def test_insert_duplicate_url_fails(self, temp_db, sample_article):
        """Duplicate URLs should be rejected."""
        # First insert
        first_id = temp_db.insert_article(
            url=sample_article['url'],
            title=sample_article['title'],
            summary=sample_article['summary']
        )
        
        # Second insert with same URL
        second_id = temp_db.insert_article(
            url=sample_article['url'],
            title="Different Title",
            summary="Different Summary"
        )
        
        assert first_id is not None
        assert second_id is None  # Duplicate rejected
    
    def test_get_articles(self, populated_db):
        """Should return paginated results."""
        articles = populated_db.get_articles(limit=10, offset=0)
        
        assert len(articles) >= 1
    
    def test_get_articles_with_search(self, populated_db, sample_article):
        """Should filter articles by search query."""
        articles = populated_db.get_articles(
            limit=10, 
            offset=0,
            search="OpenAI"
        )
        
        # Should find the sample article
        assert len(articles) >= 1


class TestURLStatusTracking:
    """Test URL status tracking for newsletter quality."""
    
    def test_default_status_is_unchecked(self, temp_db, sample_article):
        """New articles should have 'unchecked' status."""
        temp_db.insert_article(
            url=sample_article['url'],
            title=sample_article['title'],
            summary=sample_article['summary']
        )
        
        # Get article via raw query
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url_status FROM news_articles WHERE url = ?", 
                         (sample_article['url'],))
            row = cursor.fetchone()
            assert row[0] == 'unchecked' or row[0] is None
    
    def test_update_url_status(self, temp_db, sample_article):
        """Should update URL status."""
        article_id = temp_db.insert_article(
            url=sample_article['url'],
            title=sample_article['title'],
            summary=sample_article['summary']
        )
        
        result = temp_db.update_url_status(article_id, 'accessible')
        assert result is True
        
        # Verify update
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url_status FROM news_articles WHERE id = ?", 
                         (article_id,))
            row = cursor.fetchone()
            assert row[0] == 'accessible'
    
    def test_get_unchecked_articles(self, temp_db, sample_article):
        """Should return only unchecked articles."""
        # Insert article with default unchecked status
        article_id = temp_db.insert_article(
            url=sample_article['url'],
            title=sample_article['title'],
            summary=sample_article['summary']
        )
        
        unchecked = temp_db.get_unchecked_articles()
        assert len(unchecked) >= 1
    
    def test_get_articles_by_url_status(self, temp_db, sample_article):
        """Should filter by URL status."""
        article_id = temp_db.insert_article(
            url=sample_article['url'],
            title=sample_article['title'],
            summary=sample_article['summary']
        )
        temp_db.update_url_status(article_id, 'preview_only')
        
        preview_articles = temp_db.get_articles_by_url_status('preview_only')
        assert len(preview_articles) >= 1
        assert all(a['url_status'] == 'preview_only' for a in preview_articles)


class TestDealOperations:
    """Test deal CRUD operations."""
    
    def test_insert_deal(self, populated_db, sample_deal):
        """Deal insertion is handled in populated_db fixture."""
        deals = populated_db.get_deals(limit=10)
        
        assert len(deals) >= 1
        deal = deals[0]
        assert deal['company_name'] == sample_deal['company_name']


class TestStatistics:
    """Test statistics generation."""
    
    def test_get_statistics(self, populated_db):
        """Should return database statistics."""
        stats = populated_db.get_statistics()
        
        assert 'total_articles' in stats
        assert 'total_deals' in stats
        assert stats['total_articles'] >= 1
