# AI Investment Newsletter Platform - Master Plan

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

### Critical Issues (P0)

1. **No Test Suite**
   - Only `test_api.py` smoke test exists
   - No unit tests for parser, db, scrapers
   - No integration tests
   - No mocking infrastructure

2. **No CLI Interface**
   - No unified entry point
   - Multiple ad-hoc scripts
   - No argument parsing

### High Priority (P1)

3. **Hardcoded Configuration**
   - Database path hardcoded in db.py
   - No environment variable support
   - No .env file loading

4. **Scraper Reliability**
   - PitchBook returns 404 errors
   - No alternative data sources
   - No graceful degradation

### Moderate Issues (P2)

5. **No Database Migrations**
   - Schema changes require manual handling
   - No versioning

6. **No API Authentication**
   - Open endpoints
   - No rate limiting

7. **Error Handling Gaps**
   - Inconsistent exception handling
   - Some errors silently swallowed

### Low Priority (P3)

8. **Logging Inconsistency**
   - Multiple logger configurations
   - No structured logging

9. **Code Organization**
   - Utility scripts cluttering root
   - No clear src/ layout

10. **Documentation**
    - Multiple README files
    - No docstring coverage reporting

---

## 3. Sprint Roadmap Overview

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 1 | Foundation & Testing | 1 week | Planning |
| 2 | Scraper Reliability | 1 week | Planning |
| 3 | Newsletter Generation | 1 week | Planning |
| 4 | API Hardening | 1 week | Planning |
| 5 | Docker Deployment | 1 week | Planning |

---

## 4. Test Specifications

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_db.py           # Database layer tests
│   ├── test_ai_parser.py    # Parser tests
│   ├── test_config.py       # Configuration tests
│   └── test_schemas.py      # Data model tests
├── integration/
│   ├── test_api.py          # API endpoint tests
│   ├── test_scraper.py      # Scraper integration tests
│   └── test_scheduler.py    # Scheduler tests
└── e2e/
    └── test_newsletter.py   # End-to-end newsletter tests
```

### Test Coverage Targets

| Module | Target | Priority |
|--------|--------|----------|
| core.database | 80% | Sprint 1 |
| parsers.ai_parser | 80% | Sprint 1 |
| cli | 70% | Sprint 1 |
| config | 90% | Sprint 1 |
| scrapers.* | 60% | Sprint 2 |
| api.* | 80% | Sprint 4 |

---

## 5. CLI Design Overview

```
pitchbook [OPTIONS] COMMAND [ARGS]

Commands:
  scrape      Run scrapers to fetch new articles
  generate    Generate newsletter content
  serve       Start the API server
  dashboard   Generate/open HTML dashboard
  db          Database management commands
  schedule    Scheduler management
```

See [sprint_1_foundation.md](sprint_1_foundation.md) for detailed CLI specification.

---

## 6. Configuration System

### Environment Variables

```bash
PITCHBOOK_DB_PATH=./data/ai_news.db
PITCHBOOK_API_HOST=127.0.0.1
PITCHBOOK_API_PORT=8000
PITCHBOOK_API_KEY=your-api-key-here
PITCHBOOK_HEADLESS=true
PITCHBOOK_LOG_LEVEL=INFO
```

### Configuration File (config.yaml)

```yaml
database:
  path: ./data/ai_news.db
  backup_enabled: true

api:
  host: 127.0.0.1
  port: 8000

scraping:
  headless: true
  max_retries: 3

scheduler:
  cron: "0 2 * * *"
```

---

## 7. Architecture Target

### Proposed Directory Structure

```
pitchbooks/
├── src/
│   └── pitchbook/
│       ├── cli.py              # Click CLI entry point
│       ├── config.py           # Pydantic settings
│       ├── core/
│       │   ├── database.py
│       │   ├── models.py
│       │   └── exceptions.py
│       ├── scrapers/
│       ├── parsers/
│       ├── api/
│       ├── newsletter/
│       └── scheduler/
├── tests/
├── data/
├── docs/
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 8. Deployment

**Target:** Docker containerization

See [sprint_5_deployment.md](sprint_5_deployment.md) for Docker configuration.

---

**Individual sprint details in separate files:**
- [sprint_1_foundation.md](sprint_1_foundation.md)
- [sprint_2_scrapers.md](sprint_2_scrapers.md)
- [sprint_3_newsletter.md](sprint_3_newsletter.md)
- [sprint_4_api.md](sprint_4_api.md)
- [sprint_5_deployment.md](sprint_5_deployment.md)
