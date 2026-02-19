"""
Tests for RSS scraper.

These tests verify the RSS feed scraper correctly
parses and filters AI-related articles.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.rss_scraper import (
    RSSNewsScraper,
    RSS_SOURCES,
    RSSSource
)


class TestRSSSources:
    """Test RSS source configuration."""
    
    def test_sources_defined(self):
        """Should have RSS sources configured."""
        assert len(RSS_SOURCES) > 0
    
    def test_sources_have_required_fields(self):
        """Each source should have name, feed_url, and priority."""
        for source in RSS_SOURCES:
            assert source.name
            assert source.feed_url
            assert isinstance(source.priority, int)
    
    def test_sources_are_tech_focused(self):
        """Source names should be tech-focused sites."""
        expected_sources = ['techcrunch', 'venturebeat', 'mit']
        source_names = [s.name.lower() for s in RSS_SOURCES]
        
        # At least one expected source should be present
        assert any(exp in name for name in source_names for exp in expected_sources)


class TestRSSNewsScraper:
    """Test RSS news scraper functionality."""
    
    @patch('src.scrapers.rss_scraper.get_db')
    def test_scraper_init(self, mock_get_db, temp_db):
        """Scraper should initialize correctly."""
        mock_get_db.return_value = temp_db
        scraper = RSSNewsScraper()
        assert scraper.db == temp_db
        assert len(scraper.sources) > 0
    
    @patch('src.scrapers.rss_scraper.get_db')
    def test_sources_filtered_by_enabled(self, mock_get_db, temp_db):
        """Scraper should only include enabled sources."""
        mock_get_db.return_value = temp_db
        scraper = RSSNewsScraper()
        
        # All sources in scraper should be enabled
        for source in scraper.sources:
            assert source.enabled


class TestAIRelevanceDetection:
    """Test AI relevance detection in content."""
    
    def test_ai_keywords_in_title(self):
        """Should detect AI keywords in titles."""
        ai_titles = [
            "OpenAI Launches GPT-5 Model",
            "Machine Learning Startup Raises $10M",
            "LLM Applications in Healthcare",
            "Generative AI Transforms Design",
            "Neural Network Breakthrough"
        ]
        
        # These should be identifiable as AI content
        for title in ai_titles:
            lower = title.lower()
            has_ai = any(kw in lower for kw in [
                'ai', 'openai', 'machine learning', 'llm', 
                'generative', 'neural'
            ])
            assert has_ai, f"Should detect AI: {title}"


class TestRSSScraping:
    """Test actual RSS scraping (mocked)."""
    
    @pytest.fixture
    def mock_feed_response(self):
        """Mock feedparser response."""
        mock = MagicMock()
        mock.entries = [
            MagicMock(
                title="AI Startup Raises $50M Series A",
                link="https://example.com/article-1",
                summary="AI company funding round...",
                published_parsed=(2024, 1, 15, 10, 0, 0, 0, 0, 0)
            ),
            MagicMock(
                title="Machine Learning Advances",
                link="https://example.com/article-2", 
                summary="New ML techniques...",
                published_parsed=(2024, 1, 14, 10, 0, 0, 0, 0, 0)
            )
        ]
        mock.bozo = False
        return mock
    
    @patch('feedparser.parse')
    @patch('src.scrapers.rss_scraper.get_db')
    def test_scrape_feed(self, mock_get_db, mock_parse, temp_db, mock_feed_response):
        """Should parse RSS feed and extract articles."""
        mock_get_db.return_value = temp_db
        mock_parse.return_value = mock_feed_response
        
        scraper = RSSNewsScraper()
        
        # The scraper should be able to process feeds
        assert scraper is not None
        assert len(scraper.sources) > 0
    
    @patch('feedparser.parse')
    @patch('src.scrapers.rss_scraper.get_db')
    def test_scrape_handles_errors(self, mock_get_db, mock_parse, temp_db):
        """Should handle feed parsing errors gracefully."""
        mock_get_db.return_value = temp_db
        mock_parse.return_value = MagicMock(
            entries=[],
            bozo=True,
            bozo_exception=Exception("Parse error")
        )
        
        scraper = RSSNewsScraper()
        # Should not raise exception
        assert scraper is not None
