"""
FastAPI server for AI News Intelligence Platform

Provides REST API with:
- Pagination (articles, deals)
- Category filtering
- Search functionality
- Sorting options
- Zero duplicates (SQLite-based)
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import math

from db import get_db

# Pydantic models for API responses
class ArticleResponse(BaseModel):
    id: int
    url: str
    title: str
    summary: str
    ai_relevance_score: float
    is_deal_news: int
    published_date: Optional[str] = None
    scraped_date: str

class DealResponse(BaseModel):
    id: int
    company_name: str
    funding_amount: Optional[float] = None
    funding_currency: str
    round_type: Optional[str] = None
    investors: Optional[str] = None
    title: str
    url: str

class CategoryResponse(BaseModel):
    id: int
    name: str
    article_count: int

class PaginatedArticles(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[ArticleResponse]

class PaginatedDeals(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[DealResponse]

class Statistics(BaseModel):
    total_articles: int
    total_deals: int
    total_companies: int
    total_investors: int
    total_funding_usd: float
    avg_relevance_score: float
    total_categories: int

# Initialize FastAPI app
app = FastAPI(
    title="AI News Intelligence Platform API",
    description="REST API for AI market news, deals, and funding intelligence",
    version="2.0"
)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────
# HEALTH CHECK ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    
    For newsletter creators: This tells Docker/Kubernetes if
    the scraper is running and collecting data successfully.
    """
    import json
    from pathlib import Path
    from datetime import datetime
    
    db = get_db()
    stats = db.get_statistics()
    
    # Check last scrape result
    health_file = Path(__file__).parent / "scrape_health.json"
    last_scrape = None
    scrape_healthy = True
    
    if health_file.exists():
        try:
            with open(health_file, 'r') as f:
                last_scrape = json.load(f)
                scrape_healthy = last_scrape.get('success', True)
        except Exception:
            pass
    
    # Determine overall health
    db_healthy = stats.get('total_articles', 0) > 0
    status = "healthy" if (db_healthy and scrape_healthy) else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "checks": {
            "database": "ok" if db_healthy else "empty",
            "last_scrape": "ok" if scrape_healthy else "error",
        },
        "stats": {
            "articles": stats.get('total_articles', 0),
            "deals": stats.get('total_deals', 0),
        },
        "last_scrape": last_scrape
    }


@app.get("/health/live")
async def liveness_check():
    """Simple liveness check - is the API running?"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness check - is the API ready to serve requests?"""
    try:
        db = get_db()
        stats = db.get_statistics()
        return {
            "status": "ready",
            "database_connected": True,
            "articles_available": stats.get('total_articles', 0) > 0
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )


# ──────────────────────────────────────────────────────────────────────────
# ARTICLES ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────

@app.get("/articles", response_model=PaginatedArticles)
async def get_articles(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Articles per page"),
    category: Optional[str] = Query(None, description="Filter by AI category"),
    min_relevance: float = Query(0.0, ge=0.0, le=1.0, description="Minimum relevance score"),
    search: Optional[str] = Query(None, description="Search in title/content"),
    sort_by: str = Query("published_date", description="Sort by: published_date, relevance, recent"),
):
    """
    Get paginated articles with filtering and search.
    
    **Parameters:**
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20, max: 100)
    - `category`: Filter by AI category (e.g., "generative_ai", "machine_learning")
    - `min_relevance`: Minimum AI relevance score (0-1)
    - `search`: Search term for title/content
    - `sort_by`: "published_date", "relevance", or "recent"
    
    **Returns:** Paginated articles with metadata
    """
    db = get_db()
    
    # Get total count
    total = db.get_articles_count(category=category, min_relevance=min_relevance)
    
    if total == 0:
        return PaginatedArticles(
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
            items=[]
        )
    
    # Calculate pagination
    total_pages = math.ceil(total / page_size)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page not found")
    
    offset = (page - 1) * page_size
    
    # Get articles
    articles = db.get_articles(
        limit=page_size,
        offset=offset,
        category=category,
        min_relevance=min_relevance,
        search=search,
        sort_by=sort_by
    )
    
    return PaginatedArticles(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[ArticleResponse(**a) for a in articles]
    )

@app.get("/articles/{article_id}")
async def get_article(article_id: int):
    """Get a specific article by ID."""
    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM news_articles WHERE id = ?", (article_id,))
        article = cursor.fetchone()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return dict(article)

# ──────────────────────────────────────────────────────────────────────────
# DEALS ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────

@app.get("/deals", response_model=PaginatedDeals)
async def get_deals(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Deals per page"),
    min_amount: Optional[float] = Query(None, description="Minimum funding amount (USD)"),
    search: Optional[str] = Query(None, description="Search company name/title"),
):
    """
    Get paginated funding deals.
    
    **Parameters:**
    - `page`: Page number (default: 1)
    - `page_size`: Deals per page (default: 20, max: 100)
    - `min_amount`: Filter deals above minimum amount (USD)
    - `search`: Search in company name or article title
    
    **Returns:** Paginated deals with funding details
    """
    db = get_db()
    
    # Get total
    total = db.get_deals_count(min_amount=min_amount, search=search)
    
    if total == 0:
        return PaginatedDeals(
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
            items=[]
        )
    
    # Calculate pagination
    total_pages = math.ceil(total / page_size)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page not found")
    
    offset = (page - 1) * page_size
    
    # Get deals
    deals = db.get_deals_paginated(
        limit=page_size,
        offset=offset,
        min_amount=min_amount,
        search=search
    )
    
    return PaginatedDeals(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[DealResponse(**d) for d in deals]
    )

@app.get("/deals/{deal_id}")
async def get_deal(deal_id: int):
    """Get a specific deal by ID."""
    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, a.title, a.published_date, a.url
            FROM deals d
            JOIN news_articles a ON d.article_id = a.id
            WHERE d.id = ?
        """, (deal_id,))
        deal = cursor.fetchone()
        
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        return dict(deal)

# ──────────────────────────────────────────────────────────────────────────
# CATEGORIES ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────

@app.get("/categories", response_model=List[CategoryResponse])
async def get_categories():
    """
    Get all AI technology categories with article counts.
    
    **Returns:** List of categories with their article counts
    """
    db = get_db()
    categories = db.get_categories()
    return [CategoryResponse(**c) for c in categories]

@app.get("/articles/by-category/{category_name}")
async def get_articles_by_category(
    category_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Get articles filtered by specific AI category.
    
    **Categories:**
    - generative_ai
    - machine_learning
    - computer_vision
    - nlp
    - ai_infrastructure
    - ai_agents
    - robotics
    - ai_safety
    - enterprise_ai
    """
    return await get_articles(
        page=page,
        page_size=page_size,
        category=category_name
    )

# ──────────────────────────────────────────────────────────────────────────
# SEARCH ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────

@app.get("/search/articles", response_model=PaginatedArticles)
async def search_articles(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_relevance: float = Query(0.0, ge=0.0, le=1.0),
):
    """
    Search articles by title and content.
    
    **Parameters:**
    - `q`: Search query (required)
    - `page`: Page number
    - `page_size`: Results per page
    - `min_relevance`: Minimum relevance score filter
    """
    return await get_articles(
        page=page,
        page_size=page_size,
        search=q,
        min_relevance=min_relevance
    )

@app.get("/search/deals", response_model=PaginatedDeals)
async def search_deals(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Search deals by company name or article title.
    
    **Parameters:**
    - `q`: Search query (required)
    - `page`: Page number
    - `page_size`: Results per page
    """
    return await get_deals(
        page=page,
        page_size=page_size,
        search=q
    )

# ──────────────────────────────────────────────────────────────────────────
# STATISTICS ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────

@app.get("/statistics", response_model=Statistics)
async def get_statistics():
    """
    Get overall database statistics.
    
    **Returns:**
    - total_articles: Total articles in database
    - total_deals: Total funding deals extracted
    - total_companies: Unique companies mentioned
    - total_investors: Unique investors mentioned
    - total_funding_usd: Total funding tracked ($)
    - avg_relevance_score: Average AI relevance (0-1)
    - total_categories: Number of AI categories
    """
    db = get_db()
    stats = db.get_statistics()
    return Statistics(**stats)

# ──────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ──────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        db = get_db()
        stats = db.get_statistics()
        return {
            "status": "healthy",
            "database": "connected",
            "articles": stats["total_articles"],
            "deals": stats["total_deals"]
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# ──────────────────────────────────────────────────────────────────────────
# ROOT ENDPOINT
# ──────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """API documentation and usage information."""
    return {
        "name": "AI News Intelligence Platform API",
        "version": "2.0",
        "description": "REST API for AI market news, deals, and funding intelligence",
        "endpoints": {
            "articles": {
                "get_articles": "GET /articles?page=1&page_size=20&category=generative_ai&min_relevance=0.7&sort_by=published_date",
                "search_articles": "GET /search/articles?q=funding&page=1",
                "get_article": "GET /articles/{id}",
                "by_category": "GET /articles/by-category/{category_name}"
            },
            "deals": {
                "get_deals": "GET /deals?page=1&page_size=20&min_amount=10000000",
                "search_deals": "GET /search/deals?q=anthropic&page=1",
                "get_deal": "GET /deals/{id}"
            },
            "categories": {
                "list_categories": "GET /categories",
            },
            "statistics": {
                "get_statistics": "GET /statistics"
            },
            "health": "GET /health"
        },
        "categories": [
            "generative_ai",
            "machine_learning",
            "computer_vision",
            "nlp",
            "ai_infrastructure",
            "ai_agents",
            "robotics",
            "ai_safety",
            "enterprise_ai"
        ],
        "docs": "http://localhost:8000/docs",
        "redoc": "http://localhost:8000/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
