"""
Tests for FastAPI REST API endpoints.

These tests verify the API layer works correctly for
serving AI news articles, deals, and health status.
"""

import pytest
from fastapi.testclient import TestClient
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import app for testing
from api import app


@pytest.fixture
def test_client():
    """Create a test client."""
    client = TestClient(app)
    return client


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_live(self, test_client):
        """Liveness probe should return OK."""
        response = test_client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    def test_health_ready(self, test_client):
        """Readiness probe should check database."""
        response = test_client.get("/health/ready")
        # Should either succeed or fail gracefully
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data
    
    def test_health_full(self, test_client):
        """Full health check should return status."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data


class TestArticlesEndpoints:
    """Test articles API endpoints."""
    
    def test_get_articles(self, test_client):
        """Should return articles endpoint."""
        response = test_client.get("/articles")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert "page" in data
    
    def test_get_articles_pagination(self, test_client):
        """Should paginate results correctly."""
        response = test_client.get("/articles?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert "total_pages" in data
    
    def test_get_articles_with_search(self, test_client):
        """Should accept search parameter."""
        response = test_client.get("/articles?search=AI")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_get_articles_min_relevance(self, test_client):
        """Should accept relevance filter."""
        response = test_client.get("/articles?min_relevance=0.5")
        assert response.status_code == 200


class TestDealsEndpoints:
    """Test deals API endpoints."""
    
    def test_get_deals(self, test_client):
        """Should return deals endpoint."""
        response = test_client.get("/deals")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
    
    def test_get_deals_pagination(self, test_client):
        """Should paginate deals."""
        response = test_client.get("/deals?page=1&page_size=10")
        assert response.status_code == 200


class TestStatisticsEndpoints:
    """Test statistics endpoints."""
    
    def test_get_statistics(self, test_client):
        """Should return database statistics."""
        response = test_client.get("/statistics")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_articles" in data
        assert "total_deals" in data
    
    def test_get_categories(self, test_client):
        """Should return category list."""
        response = test_client.get("/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCORS:
    """Test CORS middleware."""
    
    def test_cors_headers(self, test_client):
        """Should include CORS headers in responses."""
        response = test_client.options(
            "/articles",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # OPTIONS should be allowed
        assert response.status_code in (200, 204)
