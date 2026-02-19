"""
Test fixtures and configuration for pytest.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = DatabaseManager(db_path)
    yield db
    
    # Cleanup
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture
def sample_article():
    """Sample article data for testing."""
    return {
        'url': 'https://example.com/article-1',
        'title': 'OpenAI Raises $500M in Series B',
        'summary': 'AI company announces major funding round',
        'content': 'Full article content here about generative AI...',
        'published_date': '2024-01-15',
        'ai_relevance_score': 0.95,
        'is_deal_news': True,
        'source': 'test_source'
    }


@pytest.fixture
def sample_deal():
    """Sample deal data for testing."""
    return {
        'company_name': 'OpenAI',
        'funding_amount': 500000000,
        'funding_currency': 'USD',
        'round_type': 'Series B',
        'investors': 'Microsoft, Sequoia Capital',
        'announcement_date': '2024-01-15'
    }


@pytest.fixture
def populated_db(temp_db, sample_article, sample_deal):
    """Database pre-populated with test data."""
    # Insert a test article
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
    
    # Insert a test deal
    if article_id:
        temp_db.insert_deal(
            article_id=article_id,
            company_name=sample_deal['company_name'],
            funding_amount=sample_deal['funding_amount'],
            funding_currency=sample_deal['funding_currency'],
            round_type=sample_deal['round_type'],
            investors=sample_deal['investors'],
            announcement_date=sample_deal['announcement_date']
        )
    
    return temp_db
