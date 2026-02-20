# PitchBook AI News Intelligence Platform - Strategy Document

## Project Overview

A professional-grade data pipeline that scrapes AI investment news and generates curated content for newsletters tracking AI funding trends, investor activity, and market intelligence.

**Live Dashboard**: https://ss889.github.io/Pitchbooks-scraper/  
**Repository**: https://github.com/ss889/Pitchbooks-scraper  
**Last Verified**: February 19, 2026

---

## Implementation Status

### ✅ Fully Implemented & Tested
- SQLite database with 7 tables (news_articles, deals, companies, investors, ai_categories, article_categories, scrape_runs)
- RSS feed scraping (TechCrunch, VentureBeat, MIT Tech Review)
- URL validation (async/sync with status tracking)
- AI relevance scoring with 9 categories
- FastAPI REST endpoints with pagination
- Docker deployment (single-command)
- Test suite: **50 tests passing**
- GitHub Pages dashboard

### 🚧 Partially Implemented
- PitchBook scraper (code exists, may be blocked by site)
- Newsletter auto-generation (manual via simple_viewer.py)

### 📋 Planned
- Real-time Slack/Discord alerts
- Trend analysis charts
- Investor profile database

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    PITCHBOOK AI INTELLIGENCE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  PitchBook   │    │  RSS Feeds   │    │  URL         │       │
│  │  Scraper     │    │  Scraper     │    │  Validator   │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                    │               │
│         ▼                   ▼                    ▼               │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                  AI NEWS PARSER                       │       │
│  │  • Relevance scoring (0-1)                            │       │
│  │  • Category extraction (9 AI categories)              │       │
│  │  • Deal detection & extraction                        │       │
│  │  • Company/Investor identification                    │       │
│  └──────────────────────────────────────────────────────┘       │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                  SQLite DATABASE                      │       │
│  │  • news_articles (URL dedup, status tracking)         │       │
│  │  • deals (funding amounts, round types)               │       │
│  │  • companies & investors                              │       │
│  │  • ai_categories & mappings                           │       │
│  └──────────────────────────────────────────────────────┘       │
│                            │                                     │
│         ┌──────────────────┼──────────────────┐                 │
│         ▼                  ▼                  ▼                 │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐             │
│  │  REST API  │    │  Dashboard │    │  Scheduler │             │
│  │  (FastAPI) │    │  (HTML)    │    │  (2 AM)    │             │
│  └────────────┘    └────────────┘    └────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### Primary Source: PitchBook
- **Status:** 🚧 May require authentication/may be blocked
- **Goal:** Primary deal data source when accessible
- **Content:** Deal data, company profiles, investor info
- **Scraper:** `scraper/news.py`, `scraper/companies.py`
- **Fallback:** Automatically switches to RSS feeds if blocked

### Secondary Sources: RSS Feeds (Always Available)
| Source | Feed URL | Priority | Focus |
|--------|----------|----------|-------|
| TechCrunch AI | techcrunch.com/category/artificial-intelligence/feed/ | 1 | Breaking news |
| TechCrunch Startups | techcrunch.com/category/startups/feed/ | 2 | Funding rounds |
| VentureBeat AI | venturebeat.com/category/ai/feed/ | 3 | Industry analysis |
| MIT Tech Review | technologyreview.com/feed/ | 4 | Research/technical |

---

## AI Categories

The system automatically categorizes articles into 9 AI domains:

| Category | Keywords | Weight |
|----------|----------|--------|
| `generative_ai` | GPT, Claude, LLM, diffusion, transformer | 1.0 |
| `ai_infrastructure` | GPU, inference, MLops, vector database | 1.0 |
| `ai_agents` | autonomous agent, agentic, workflow automation | 1.0 |
| `machine_learning` | ML, neural network, training, deep learning | 0.9 |
| `ai_safety` | alignment, bias detection, responsible AI | 0.9 |
| `computer_vision` | object detection, image recognition | 0.85 |
| `nlp` | language model, sentiment analysis, speech | 0.85 |
| `enterprise_ai` | B2B, SaaS, productivity, copilot | 0.85 |
| `robotics` | embodied AI, robot learning | 0.8 |

---

## Database Schema

### news_articles
```sql
id, url, url_hash, title, summary, content,
published_date, scraped_date, source,
ai_relevance_score (0-1), is_deal_news (0/1),
url_status (accessible/preview_only/inaccessible/unchecked),
url_last_checked
```

### deals
```sql
id, article_id, company_name,
funding_amount (USD), funding_currency,
round_type (Seed/Series A/B/C/etc),
investors (comma-separated),
announcement_date
```

### ai_categories
```sql
id, name, description, parent_id
```

### article_categories
```sql
article_id, category_id, weight (relevance)
```

---

## API Endpoints

### Health Checks
| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Full health status with stats |
| `GET /health/live` | Liveness probe |
| `GET /health/ready` | Database readiness |

### Content
| Endpoint | Parameters |
|----------|------------|
| `GET /articles` | page, page_size, category, min_relevance, search, sort_by |
| `GET /articles/{id}` | Single article |
| `GET /deals` | page, page_size, min_amount, search |
| `GET /deals/{id}` | Single deal |
| `GET /categories` | All categories with counts |
| `GET /statistics` | Total articles, deals, funding |

### Search
| Endpoint | Parameters |
|----------|------------|
| `GET /search/articles` | q, page, page_size, min_relevance |
| `GET /search/deals` | q, page, page_size |

### Sample API Responses

```json
// GET /articles?min_relevance=0.8&page_size=2
{
  "total": 127,
  "page": 1,
  "page_size": 2,
  "items": [
    {
      "id": 45,
      "title": "Anthropic Raises $500M Series D",
      "ai_relevance_score": 0.95,
      "url_status": "accessible",
      "source": "techcrunch_ai"
    }
  ]
}

// GET /statistics
{
  "total_articles": 523,
  "total_deals": 89,
  "total_funding_usd": 4250000000,
  "avg_relevance_score": 0.72
}
```

---

## Automation Schedule

The scheduler runs daily at **2:00 AM** (configurable):

1. **PitchBook Scraper** - Attempts primary source (may fail)
2. **RSS Scraper** - Always reliable fallback
3. **URL Validator** - Checks all unchecked article links
4. **Health Report** - Saves to `scrape_health.json`

```bash
# Manual trigger
python scheduler.py --run-now

# Check status
python scheduler.py --status

# Run scheduler daemon
python scheduler.py
```

---

## Key Features

### URL Validation
Every article URL is verified before display:
- `accessible` - Full content available
- `preview_only` - Paywall/login required
- `inaccessible` - 404 or broken
- `unchecked` - Not yet validated

### Deduplication
- URLs are hashed (MD5) for fast duplicate detection
- Prevents duplicate articles across scrapers
- Maintains data integrity

### AI Relevance Scoring
Articles receive a 0-1 relevance score based on:
- Core AI keywords in title (+0.5)
- AI keywords in content (+0.3)
- Category matches (+0.2)
- Deal/funding mentions (+0.25)

---

## Docker Deployment

```bash
# Start all services
docker-compose up -d

# Services:
# - api: FastAPI on port 8000
# - scheduler: Runs daily scrape at 2 AM

# View logs
docker-compose logs -f

# Manual scrape
docker-compose exec api python scheduler.py --run-now
```

---

## Environment Variables

```bash
# Database
PITCHBOOK_DB_PATH=./data/ai_news.db

# API
PITCHBOOK_API_HOST=0.0.0.0
PITCHBOOK_API_PORT=8000

# Scheduler
PITCHBOOK_SCRAPE_HOUR=2
PITCHBOOK_SCRAPE_MINUTE=0

# Logging
PITCHBOOK_LOG_LEVEL=INFO
```

---

## Troubleshooting

### Problem: PitchBook scraper returns no articles
**Cause:** PitchBook may block automated access
**Solution:** System automatically falls back to RSS feeds. Check `scrape_health.json` for details:
```bash
python scheduler.py --status
```

### Problem: Broken article links in dashboard
**Cause:** News sites remove or paywall content
**Solution:** Run URL validation to update link status:
```bash
python validate_urls.py --fix --remove-broken
```

### Problem: Scheduler not running
**Cause:** Process stopped or container restarted
**Solution:** Check scheduler status and restart:
```bash
docker-compose ps
docker-compose restart scheduler
```

---

## Test Coverage

50 tests covering:
- URL validation (async/sync)
- Database operations (CRUD, deduplication)
- API endpoints (health, articles, deals, search)
- RSS scraper (feed parsing, AI relevance)

```bash
pytest tests/ -v
```

---

## Commands Quick Reference

```bash
# Run scraper manually
python scheduler.py --run-now

# Start API server
uvicorn api:app --reload --port 8000

# Generate dashboard
python simple_viewer.py

# Validate URLs
python validate_urls.py --fix

# Run tests
pytest tests/ -v

# Docker
docker-compose up -d
docker-compose logs -f
```

---

## Success Metrics

| Metric | Target | Status | Verified |
|--------|--------|--------|----------|
| Article link reliability | 100% clickable | ✅ URL validation active | Feb 19, 2026 |
| Daily automation | 2 AM reliable | ✅ Multi-source fallback | Feb 19, 2026 |
| API response time | <500ms | ✅ SQLite indexed | Feb 19, 2026 |
| Test coverage | 80%+ | ✅ **50 tests passing** | Feb 19, 2026 |
| Docker deployment | One-command | ✅ docker-compose.yml | Feb 19, 2026 |
| Dashboard live | URL accessible | ✅ GitHub Pages | Feb 19, 2026 |

---

## Future Enhancements

1. **Real-time alerts** - Slack/Discord notifications for major deals
2. **Newsletter generation** - Auto-compose weekly AI funding digest
3. **Trend analysis** - Track funding by category over time
4. **Investor tracking** - Build investor profile database
5. **Company watchlists** - Alert on specific company news

---

*Built for newsletter creators who obsess over data quality.*
