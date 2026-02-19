# AI Investment Newsletter Platform
## Planning Sprint Documentation

**Version:** 1.0  
**Date:** 2026-02-19  
**Status:** Planning Phase  

---

## 1. Codebase Audit Summary

### Current Architecture

```
pitchbooks/
├── api.py              # FastAPI REST server (427 lines)
├── db.py               # SQLite database layer (498 lines)
├── config.py           # Configuration constants
├── scheduler.py        # APScheduler for cron jobs (130 lines)
├── simple_viewer.py    # HTML dashboard generator
├── run_service.py      # Combined API + scheduler runner
├── scraper/
│   ├── base.py         # Playwright browser automation (167 lines)
│   ├── news.py         # News article scraper
│   ├── ai_parser.py    # AI relevance scoring (385 lines)
│   ├── companies.py    # Company scraper
│   ├── people.py       # People scraper
│   └── accelerators.py # Accelerator scraper
├── models/
│   └── schemas.py      # Dataclass schemas (127 lines)
└── output/             # JSON exports
```

### Component Assessment

| Component | Status | Quality | Notes |
|-----------|--------|---------|-------|
| Database Layer | ✅ Functional | Medium | No migrations, hardcoded path |
| REST API | ✅ Functional | Medium | No auth, no rate limiting |
| Scraper | ⚠️ Partial | Low | PitchBook blocking, no fallback |
| AI Parser | ✅ Functional | High | Good categorization |
| Scheduler | ✅ Functional | Medium | No error recovery |
| Dashboard | ✅ Functional | Medium | Static HTML generation |
| Tests | ❌ Missing | Critical | Only smoke test exists |
| CLI | ❌ Missing | Critical | No command-line interface |
| Config | ⚠️ Basic | Low | No env vars, no validation |

---

## 2. Technical Debt Inventory

### Critical Issues

1. **No Test Suite** (Priority: P0)
   - Only `test_api.py` smoke test exists
   - No unit tests for parser, db, scrapers
   - No integration tests
   - No mocking infrastructure

2. **No CLI Interface** (Priority: P0)
   - No unified entry point
   - Multiple ad-hoc scripts (demo_scraper.py, quick_scrape.py, etc.)
   - No argument parsing

3. **Hardcoded Configuration** (Priority: P1)
   - Database path hardcoded in db.py
   - No environment variable support
   - No .env file loading

4. **Scraper Reliability** (Priority: P1)
   - PitchBook returns 404 errors
   - No alternative data sources
   - No graceful degradation

### Moderate Issues

5. **No Database Migrations** (Priority: P2)
   - Schema changes require manual handling
   - No versioning

6. **No API Authentication** (Priority: P2)
   - Open endpoints
   - No rate limiting

7. **Error Handling Gaps** (Priority: P2)
   - Inconsistent exception handling
   - Some errors silently swallowed

8. **Logging Inconsistency** (Priority: P3)
   - Multiple logger configurations
   - No structured logging

### Low Priority

9. **Code Organization** (Priority: P3)
   - Utility scripts cluttering root
   - No clear src/ layout

10. **Documentation** (Priority: P3)
    - Multiple README files
    - No docstring coverage reporting

---

## 3. Sprint Roadmap

### Sprint 1: Foundation & Testing Infrastructure
**Duration:** 1 week  
**Goal:** Establish TDD infrastructure and CLI skeleton

#### Deliverables:
- [ ] pytest setup with fixtures
- [ ] Test directory structure
- [ ] Database mocking utilities
- [ ] CLI skeleton with Click
- [ ] Configuration via environment variables
- [ ] Basic unit tests for db.py
- [ ] Basic unit tests for ai_parser.py

#### Success Metrics:
- pytest runs with >50% coverage on core modules
- CLI `--help` displays all commands
- All tests pass in CI environment

---

### Sprint 2: Scraper Reliability & Data Sources
**Duration:** 1 week  
**Goal:** Multiple data sources, retry logic, fallback behavior

#### Deliverables:
- [ ] RSS feed scraper (TechCrunch, VentureBeat, etc.)
- [ ] Enhanced retry/backoff logic
- [ ] Proxy rotation support
- [ ] Scraper health monitoring
- [ ] Data source priority system
- [ ] Unit tests for all scrapers

#### Success Metrics:
- At least 2 working data sources
- 95% success rate on scrape attempts
- Automatic fallback when primary source fails

---

### Sprint 3: Newsletter Generation
**Duration:** 1 week  
**Goal:** Automated newsletter content generation

#### Deliverables:
- [ ] Newsletter template engine
- [ ] Content curation logic
- [ ] Markdown/HTML export
- [ ] Geographic distribution analysis
- [ ] Investor activity tracking
- [ ] CLI commands: `generate-newsletter`, `preview`

#### Success Metrics:
- Reproducible newsletter output
- Template customization working
- Export to HTML/Markdown/PDF

---

### Sprint 4: API Hardening & Dashboard
**Duration:** 1 week  
**Goal:** Production-ready API and improved dashboard

#### Deliverables:
- [ ] API key authentication
- [ ] Rate limiting middleware
- [ ] Request validation improvements
- [ ] Interactive dashboard (not static HTML)
- [ ] Real-time data refresh
- [ ] API integration tests

#### Success Metrics:
- API passes security checklist
- Dashboard loads in <2s
- 100% API endpoint coverage in tests

---

### Sprint 5: Deployment & Operations
**Duration:** 1 week  
**Goal:** Production deployment ready

#### Deliverables:
- [ ] Docker containerization
- [ ] docker-compose for local dev
- [ ] Health check endpoints
- [ ] Logging aggregation
- [ ] Error alerting
- [ ] Backup/restore procedures
- [ ] Runbook documentation

#### Success Metrics:
- One-command deployment
- Automated health monitoring
- <5 min recovery time from failures

---

## 4. Test Specifications

### Unit Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_db.py           # Database layer tests
│   ├── test_ai_parser.py    # Parser tests
│   ├── test_config.py       # Configuration tests
│   └── test_schemas.py      # Data model tests
├── integration/
│   ├── __init__.py
│   ├── test_api.py          # API endpoint tests
│   ├── test_scraper.py      # Scraper integration tests
│   └── test_scheduler.py    # Scheduler tests
└── e2e/
    ├── __init__.py
    └── test_newsletter.py   # End-to-end newsletter tests
```

### Test Categories

#### Database Tests (test_db.py)
```python
# Fixtures needed:
- fresh_db: Empty database for each test
- populated_db: Database with sample data

# Test cases:
- test_init_creates_tables
- test_insert_article_success
- test_insert_article_duplicate_rejected
- test_article_exists_true
- test_article_exists_false
- test_get_articles_pagination
- test_get_articles_filter_by_category
- test_get_articles_filter_by_relevance
- test_get_articles_search
- test_insert_deal_success
- test_get_deals_pagination
- test_get_statistics_accuracy
- test_add_article_category
- test_url_hash_generation
```

#### AI Parser Tests (test_ai_parser.py)
```python
# Fixtures needed:
- parser: AINewsParser instance
- sample_articles: Test article content

# Test cases:
- test_calculate_relevance_high_score
- test_calculate_relevance_low_score
- test_calculate_relevance_edge_cases
- test_extract_categories_single
- test_extract_categories_multiple
- test_extract_categories_none
- test_is_deal_news_positive
- test_is_deal_news_negative
- test_extract_deals_with_amount
- test_extract_deals_various_formats
- test_extract_companies
- test_extract_investors
- test_parse_article_comprehensive
```

#### API Tests (test_api.py)
```python
# Fixtures needed:
- client: TestClient for FastAPI
- db_with_data: Populated test database

# Test cases:
- test_get_articles_success
- test_get_articles_pagination
- test_get_articles_category_filter
- test_get_articles_search
- test_get_articles_invalid_page
- test_get_deals_success
- test_get_deals_min_amount_filter
- test_get_categories_success
- test_get_statistics_success
- test_search_articles_success
- test_search_deals_success
- test_health_check
- test_cors_headers
```

### Test Data

```python
# Sample article for testing
SAMPLE_ARTICLE_HIGH_RELEVANCE = {
    "title": "OpenAI Raises $6.6B in Largest AI Funding Round",
    "content": "OpenAI announced a $6.6 billion Series C funding round led by...",
    "url": "https://example.com/openai-funding",
    "expected_relevance": 0.9,
    "expected_categories": ["generative_ai", "enterprise_ai"],
    "expected_deal_amount": 6600000000,
}

SAMPLE_ARTICLE_LOW_RELEVANCE = {
    "title": "Tech Company Reports Q4 Earnings",
    "content": "The company reported revenue growth in cloud services...",
    "url": "https://example.com/earnings",
    "expected_relevance": 0.2,
    "expected_categories": [],
}
```

---

## 5. CLI Design Specification

### Command Structure

```
pitchbook [OPTIONS] COMMAND [ARGS]

Options:
  --verbose, -v    Increase verbosity
  --quiet, -q      Suppress output
  --config FILE    Configuration file path
  --version        Show version

Commands:
  scrape           Run scrapers to fetch new articles
  generate         Generate newsletter content
  serve            Start the API server
  dashboard        Generate/open HTML dashboard
  db               Database management commands
  schedule         Scheduler management
```

### Subcommands

```
pitchbook scrape [OPTIONS]
  --source TEXT      Data source (pitchbook, rss, all)
  --limit INT        Maximum articles to fetch
  --since DATE       Only fetch articles since date
  --dry-run          Show what would be scraped

pitchbook generate [OPTIONS]
  --format TEXT      Output format (html, markdown, pdf)
  --output FILE      Output file path
  --days INT         Include articles from last N days
  --category TEXT    Filter by category
  --preview          Preview without saving

pitchbook serve [OPTIONS]
  --host TEXT        Host to bind to [default: 127.0.0.1]
  --port INT         Port to bind to [default: 8000]
  --reload           Enable auto-reload for development

pitchbook dashboard [OPTIONS]
  --open             Open in browser after generation
  --output FILE      Output HTML file path

pitchbook db [COMMAND]
  init               Initialize database schema
  migrate            Run pending migrations
  export             Export database to JSON
  import             Import data from JSON
  stats              Show database statistics
  clear              Clear all data (with confirmation)

pitchbook schedule [COMMAND]
  start              Start the scheduler daemon
  stop               Stop the scheduler daemon
  status             Show scheduler status
  run-now            Trigger immediate scrape
```

---

## 6. Configuration Design

### Environment Variables

```bash
# Database
PITCHBOOK_DB_PATH=./data/ai_news.db

# API
PITCHBOOK_API_HOST=127.0.0.1
PITCHBOOK_API_PORT=8000
PITCHBOOK_API_KEY=your-api-key-here

# Scraping
PITCHBOOK_HEADLESS=true
PITCHBOOK_PROXY_URL=
PITCHBOOK_USER_AGENT=

# Scheduler
PITCHBOOK_SCRAPE_HOUR=2
PITCHBOOK_SCRAPE_MINUTE=0

# Logging
PITCHBOOK_LOG_LEVEL=INFO
PITCHBOOK_LOG_FILE=./logs/pitchbook.log
```

### Configuration File (config.yaml)

```yaml
database:
  path: ./data/ai_news.db
  backup_enabled: true
  backup_dir: ./backups

api:
  host: 127.0.0.1
  port: 8000
  cors_origins:
    - "*"

scraping:
  headless: true
  min_delay: 3
  max_delay: 6
  max_retries: 3
  sources:
    - name: pitchbook
      enabled: true
      priority: 1
    - name: techcrunch_rss
      enabled: true
      priority: 2

scheduler:
  cron: "0 2 * * *"  # Daily at 2 AM
  max_concurrent: 1

logging:
  level: INFO
  format: "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
  file: ./logs/pitchbook.log
```

---

## 7. Architecture Improvements

### Proposed Directory Structure

```
pitchbooks/
├── src/
│   └── pitchbook/
│       ├── __init__.py
│       ├── cli.py              # Click CLI entry point
│       ├── config.py           # Pydantic settings
│       ├── core/
│       │   ├── __init__.py
│       │   ├── database.py     # Database layer
│       │   ├── models.py       # SQLAlchemy/Pydantic models
│       │   └── exceptions.py   # Custom exceptions
│       ├── scrapers/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── pitchbook.py
│       │   ├── rss.py
│       │   └── registry.py     # Scraper registration
│       ├── parsers/
│       │   ├── __init__.py
│       │   └── ai_parser.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── routes/
│       │   │   ├── articles.py
│       │   │   ├── deals.py
│       │   │   └── admin.py
│       │   └── middleware.py
│       ├── newsletter/
│       │   ├── __init__.py
│       │   ├── generator.py
│       │   └── templates/
│       └── scheduler/
│           ├── __init__.py
│           └── jobs.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── data/                       # Database, logs
├── docs/                       # Documentation
├── pyproject.toml              # Modern Python packaging
├── .env.example
└── README.md
```

---

## 8. Next Steps (Immediate)

### Planning Sprint Checklist

- [x] Audit existing codebase
- [x] Identify technical debt
- [x] Propose sprint roadmap
- [x] Create test specifications
- [ ] Review with stakeholder ← **CURRENT**
- [ ] Finalize Sprint 1 scope
- [ ] Create Sprint 1 task breakdown

### Questions for Stakeholder

1. **Data Sources:** Should we prioritize fixing PitchBook scraping or adding alternative sources (RSS feeds)?

2. **Newsletter Features:** What specific elements should the newsletter include?
   - Daily vs. weekly digest?
   - Geographic focus?
   - Investor leaderboards?

3. **Deployment Target:** Local only, or cloud deployment (AWS/GCP/Azure)?

4. **Authentication:** API key only, or full user management?

5. **Budget for External Services:** Any paid APIs acceptable (Diffbot, Crunchbase, etc.)?

---

**End of Planning Document**
