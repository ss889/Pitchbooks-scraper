# AI Investment Newsletter Platform - Consolidated Sprint Planning

**Version:** 1.0  
**Date:** 2026-02-19  
**Repository:** https://github.com/ss889/Pitchbooks-scraper  
**Live Dashboard:** https://ss889.github.io/Pitchbooks-scraper/

---

## Executive Summary

A professional-grade data pipeline that scrapes AI investment news and generates curated content for newsletters tracking AI funding trends, investor activity, and market intelligence.

**Built for newsletter creators who need reliable, comprehensive, and accessible data.**

---

## 1. Current Architecture

```
pitchbooks/
├── api.py              # FastAPI REST server (503 lines)
├── db.py               # SQLite database layer (579 lines)
├── scheduler.py        # APScheduler for cron jobs (400 lines)
├── simple_viewer.py    # HTML dashboard generator
├── scraper/
│   ├── base.py         # Playwright browser automation
│   ├── news.py         # News article scraper
│   ├── ai_parser.py    # AI relevance scoring (385 lines)
│   ├── companies.py    # Company scraper
│   └── accelerators.py # Accelerator scraper
├── src/
│   ├── scrapers/
│   │   └── rss_scraper.py    # RSS feed scraper (306 lines)
│   └── utils/
│       └── url_validator.py  # URL validation (192 lines)
├── tests/              # Test suite (50 tests)
├── docs/               # GitHub Pages dashboard
├── Dockerfile          # Multi-stage production build
└── docker-compose.yml  # API + Scheduler services
```

---

## 2. Features Implemented

### Core Features
- **Multi-Source Scraping**: PitchBook (primary) + RSS feeds (TechCrunch, VentureBeat, MIT Tech Review)
- **URL Validation**: Every article link is verified before storage
- **AI Relevance Scoring**: Automatic categorization and relevance scoring for AI content
- **Deal Extraction**: Automatic extraction of funding amounts, round types, and investors
- **Daily Automation**: Scheduled scraping at 2 AM with health monitoring
- **REST API**: FastAPI endpoints with pagination, filtering, and search
- **Docker Ready**: One-command deployment with docker-compose
- **GitHub Pages**: Live dashboard at https://ss889.github.io/Pitchbooks-scraper/

### Data Sources
| Source | Type | Status | Priority |
|--------|------|--------|----------|
| PitchBook | Browser scraping | May block | Primary |
| TechCrunch AI | RSS feed | ✅ Reliable | Secondary |
| TechCrunch Startups | RSS feed | ✅ Reliable | Secondary |
| VentureBeat AI | RSS feed | ✅ Reliable | Secondary |
| MIT Tech Review | RSS feed | ✅ Reliable | Secondary |

### AI Categories Tracked
- `generative_ai` - LLMs, image generation, diffusion models
- `enterprise_ai` - Business applications, SaaS, B2B
- `ai_infrastructure` - MLOps, compute, vector databases
- `computer_vision` - Image/video AI
- `ai_safety` - Alignment, safety research
- `ai_agents` - Autonomous agents, task automation
- `robotics` - Robotics and embodied AI
- `nlp` - Natural language processing

---

## 3. Database Schema

### Tables

**news_articles** - Core article storage
```sql
id INTEGER PRIMARY KEY
url TEXT UNIQUE NOT NULL
url_hash TEXT UNIQUE NOT NULL
title TEXT NOT NULL
summary TEXT
content TEXT
published_date TEXT
scraped_date TEXT NOT NULL
source TEXT
ai_relevance_score REAL
is_deal_news INTEGER DEFAULT 0
url_status TEXT DEFAULT 'unchecked'
url_last_checked TEXT
```

**deals** - Funding deal information
```sql
id INTEGER PRIMARY KEY
article_id INTEGER (FK)
company_name TEXT
funding_amount REAL
funding_currency TEXT DEFAULT 'USD'
round_type TEXT
investors TEXT
announcement_date TEXT
```

**ai_categories** - AI technology categories
```sql
id INTEGER PRIMARY KEY
name TEXT UNIQUE NOT NULL
description TEXT
```

**article_categories** - Article to category mapping
```sql
article_id INTEGER (FK)
category_id INTEGER (FK)
weight REAL DEFAULT 1.0
```

**companies** - Extracted company data
```sql
id INTEGER PRIMARY KEY
name TEXT UNIQUE NOT NULL
funding_amount REAL
location TEXT
status TEXT
mention_count INTEGER DEFAULT 1
```

**investors** - VC and investor data
```sql
id INTEGER PRIMARY KEY
name TEXT UNIQUE NOT NULL
investor_type TEXT
portfolio_companies TEXT
```

---

## 4. API Endpoints

### Health Checks
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Full health status with scrape results |
| `/health/live` | GET | Liveness probe (is API running?) |
| `/health/ready` | GET | Readiness probe (is database connected?) |

### Articles
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/articles` | GET | List articles with pagination |
| `/articles?category=generative_ai` | GET | Filter by AI category |
| `/articles?min_relevance=0.8` | GET | Filter by relevance score |
| `/articles?search=openai` | GET | Search in title/content |
| `/articles/{id}` | GET | Get specific article |

### Deals
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/deals` | GET | List funding deals |
| `/deals?min_amount=1000000` | GET | Filter by minimum amount |
| `/search/deals?q=anthropic` | GET | Search deals |

### Statistics
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/statistics` | GET | Database statistics |
| `/categories` | GET | List categories with counts |

---

## 5. Scheduler Configuration

### Daily Scrape Strategy

The scheduler runs at 2 AM (configurable) with this strategy:

1. **Try PitchBook scraper** (may fail due to blocking)
2. **Run RSS feed scrapers** (always reliable)
3. **Validate all new URLs**
4. **Generate health report**

### Health Monitoring

Results saved to `scrape_health.json`:
```json
{
  "success": true,
  "articles_total": 15,
  "articles_by_source": {
    "pitchbook": 0,
    "rss": 15
  },
  "urls_validated": 12,
  "errors": [],
  "timestamp": "2026-02-19T02:05:00"
}
```

---

## 6. Docker Deployment

### Quick Start
```bash
docker-compose up -d
# API available at http://localhost:8000
```

### Services
| Service | Port | Command |
|---------|------|---------|
| api | 8000 | `uvicorn api:app` |
| scheduler | - | `python scheduler.py` |

### Volumes
- `./data` → `/app/data` (SQLite database)
- `./logs` → `/app/logs` (Log files)

---

## 7. Test Coverage

### Test Files
- `tests/test_api.py` - API endpoint tests (12 tests)
- `tests/test_database.py` - Database operations (12 tests)
- `tests/test_url_validator.py` - URL validation (18 tests)
- `tests/test_rss_scraper.py` - RSS scraper (8 tests)

### Running Tests
```bash
pytest tests/ -v
# 50 tests passing
```

---

## 8. Environment Variables

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

## 9. Key Commands

```bash
# Start with Docker
docker-compose up -d

# Run tests
pytest tests/ -v

# Manual scrape
python scheduler.py --run-now

# Check scheduler status
python scheduler.py --status

# Generate dashboard
python simple_viewer.py

# Start API locally
uvicorn api:app --reload --port 8000

# Validate URLs
python validate_urls.py --fix
```

---

## 10. Technical Debt & Future Work

### Completed ✅
- [x] URL validation system
- [x] RSS feed scrapers
- [x] Health monitoring
- [x] Docker deployment
- [x] Test suite (50 tests)
- [x] GitHub Pages dashboard

### Remaining Backlog
- [ ] API authentication/rate limiting
- [ ] Database migrations (Alembic)
- [ ] Structured logging
- [ ] Newsletter generation templates
- [ ] Email delivery integration
- [ ] Admin dashboard
- [ ] Webhook notifications

---

## 11. Repository Links

- **GitHub:** https://github.com/ss889/Pitchbooks-scraper
- **Dashboard:** https://ss889.github.io/Pitchbooks-scraper/
- **API Docs:** http://localhost:8000/docs (when running)

---

**Built for newsletter creators who obsess over data quality.**
