# FastAPI Guide - AI News Intelligence Platform

## Fast Start

```bash
# Install FastAPI (if not already installed)
pip install -r requirements.txt

# Start the API server
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

Server runs at: `http://localhost:8000`

---

## API Documentation

### Interactive Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Base URL
```
http://localhost:8000
```

---

## Endpoints Overview

### 📰 Articles (with Pagination & Filtering)

#### Get Paginated Articles
```
GET /articles?page=1&page_size=20&category=generative_ai&min_relevance=0.7&sort_by=published_date
```

**Parameters:**
- `page` (int, default=1): Page number
- `page_size` (int, default=20, max=100): Items per page
- `category` (string): Filter by AI category
- `min_relevance` (float 0-1): Minimum relevance score
- `search` (string): Search in title/content
- `sort_by` (string): "published_date" | "relevance" | "recent"

**Response:**
```json
{
  "total": 245,
  "page": 1,
  "page_size": 20,
  "total_pages": 13,
  "items": [
    {
      "id": 1,
      "url": "https://...",
      "title": "Article Title",
      "summary": "...",
      "ai_relevance_score": 0.85,
      "is_deal_news": 1,
      "published_date": "2026-02-15",
      "scraped_date": "2026-02-17T10:00:00"
    }
  ]
}
```

#### Search Articles
```
GET /search/articles?q=funding&page=1&page_size=20
```

#### Get Article by ID
```
GET /articles/{id}
```

#### Get Articles by Category
```
GET /articles/by-category/generative_ai?page=1&page_size=20
```

---

### 💰 Deals (with Pagination & Filtering)

#### Get Paginated Deals
```
GET /deals?page=1&page_size=20&min_amount=10000000
```

**Parameters:**
- `page` (int, default=1): Page number
- `page_size` (int, default=20, max=100): Items per page
- `min_amount` (float): Minimum funding amount (USD)
- `search` (string): Search company name or title

**Response:**
```json
{
  "total": 456,
  "page": 1,
  "page_size": 20,
  "total_pages": 23,
  "items": [
    {
      "id": 1,
      "company_name": "Anthropic",
      "funding_amount": 750000000,
      "funding_currency": "USD",
      "round_type": "Series C",
      "investors": "Google, Salesforce, etc.",
      "title": "Article about the funding",
      "url": "article-url"
    }
  ]
}
```

#### Search Deals
```
GET /search/deals?q=anthropic&page=1
```

#### Get Deal by ID
```
GET /deals/{id}
```

---

### 🏷️ Categories

#### Get All Categories
```
GET /categories
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "generative_ai",
    "article_count": 156
  },
  {
    "id": 2,
    "name": "machine_learning",
    "article_count": 98
  }
]
```

---

### 📊 Statistics

#### Get Overall Statistics
```
GET /statistics
```

**Response:**
```json
{
  "total_articles": 1245,
  "total_deals": 456,
  "total_companies": 789,
  "total_investors": 234,
  "total_funding_usd": 45600000000,
  "avg_relevance_score": 0.82,
  "total_categories": 9
}
```

---

### 🏥 Health Check

#### Check API Health
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "articles": 1245,
  "deals": 456
}
```

---

## Common Examples

### Example 1: Get Recent High-Relevance Articles
```bash
curl "http://localhost:8000/articles?page=1&page_size=20&min_relevance=0.8&sort_by=recent"
```

### Example 2: Get Generative AI News
```bash
curl "http://localhost:8000/articles/by-category/generative_ai?page=1&page_size=25"
```

### Example 3: Find Large Funding Deals
```bash
curl "http://localhost:8000/deals?page=1&page_size=50&min_amount=100000000"
```

### Example 4: Search for Specific Company
```bash
curl "http://localhost:8000/search/deals?q=OpenAI&page=1"
```

### Example 5: Get AI Infrastructure Articles
```bash
curl "http://localhost:8000/articles/by-category/ai_infrastructure?page=1&page_size=20&sort_by=relevance"
```

---

## Python Client Example

```python
import requests

API_URL = "http://localhost:8000"

# Get articles with filtering
response = requests.get(
    f"{API_URL}/articles",
    params={
        "page": 1,
        "page_size": 20,
        "category": "generative_ai",
        "min_relevance": 0.7
    }
)

data = response.json()
print(f"Found {data['total']} articles")
for article in data['items']:
    print(f"- {article['title']} (relevance: {article['ai_relevance_score']:.0%})")

# Get top deals
deals_response = requests.get(
    f"{API_URL}/deals",
    params={
        "page": 1,
        "page_size": 10,
        "min_amount": 50000000  # $50M+
    }
)

deals = deals_response.json()
for deal in deals['items']:
    print(f"{deal['company_name']}: ${deal['funding_amount']:,.0f}")
```

---

## AI Categories

Available categories for filtering:

1. **generative_ai** - LLMs, text/image generation, GPT, Claude
2. **machine_learning** - Neural networks, training, deep learning
3. **computer_vision** - Object detection, image recognition
4. **nlp** - Language models, translation, speech
5. **ai_infrastructure** - GPUs, inference, MLOps, vector databases
6. **ai_agents** - Autonomous agents, reasoning, task automation
7. **robotics** - Robot learning, embodied AI
8. **ai_safety** - Alignment, interpretability, ethics
9. **enterprise_ai** - Business AI, SaaS, workplace automation

---

## Pagination Guide

### How Pagination Works

**Request:**
```bash
GET /articles?page=2&page_size=20
```

**Response Fields:**
- `total`: Total number of items in database
- `page`: Current page number
- `page_size`: Items per page
- `total_pages`: Total pages available
- `items`: Array of items on current page

### Calculating Next Page

```python
response = requests.get("http://localhost:8000/articles", params={"page": 1, "page_size": 20})
data = response.json()

# Check if more pages exist
if data['page'] < data['total_pages']:
    next_page = requests.get("http://localhost:8000/articles", params={"page": 2, "page_size": 20})
```

### Getting All Items

```python
all_items = []
page = 1

while True:
    response = requests.get(
        "http://localhost:8000/articles",
        params={"page": page, "page_size": 100}
    )
    data = response.json()
    all_items.extend(data['items'])
    
    if page >= data['total_pages']:
        break
    
    page += 1
```

---

## Filtering by Relevance

Articles are scored 0-1 for AI relevance:

- `0.0-0.3`: Low relevance (barely AI-related)
- `0.3-0.6`: Medium relevance (some AI content)
- `0.6-0.8`: High relevance (core AI topics)
- `0.8-1.0`: Very high relevance (essential AI news)

**Get only core AI articles:**
```bash
curl "http://localhost:8000/articles?min_relevance=0.7&page_size=50"
```

---

## Sorting Options

### published_date (Default)
Articles sorted by publication date (newest first)
```
sort_by=published_date
```

### relevance
Articles sorted by AI relevance score (highest first)
```
sort_by=relevance
```

### recent
Articles sorted by when we scraped them (newest scrape first)
```
sort_by=recent
```

---

## Error Handling

### 404 - Not Found
```json
{
  "detail": "Page not found"
}
```

### 403 - Forbidden
Invalid parameters or access denied

### 500 - Server Error
Database or server issue

---

## Performance Tips

1. **Use `page_size` limit of 100** - Smaller pages load faster
2. **Filter by `category`** - Narrows down results significantly
3. **Set `min_relevance`** - Filters out noise
4. **Use `search`** - More specific than large result sets
5. **Cache results** - Store responses to avoid repeated requests

---

## Deployment

### Production Server
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Troubleshooting

### Port Already in Use
```bash
# Use a different port
python -m uvicorn api:app --port 8001
```

### Database Locked
- Only one process can write at a time
- Close other instances of: main.py, export.py

### Slow Queries
- Reduce `page_size`
- Add `category` filter
- Set `min_relevance` to filter noise

---

## Monitoring

### Check Server Status
```bash
curl http://localhost:8000/health
```

### Monitor Request Logs
Uvicorn will show all requests in terminal:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     GET /articles - 200 OK
INFO:     GET /deals?min_amount=10000000 - 200 OK
```

---

**API Version**: 2.0  
**Status**: Production-ready  
**Last Updated**: February 2026
