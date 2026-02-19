# Sprint 1: Foundation & Testing Infrastructure

**Duration:** 5 days (~24 hours)  
**Status:** Planning  
**Methodology:** Test-Driven Development (Red-Green-Refactor)  
**Priority:** P0 - Critical Foundation  

---

## Sprint Goal

Establish TDD infrastructure and CLI skeleton

## Deliverables

- [ ] pytest setup with fixtures
- [ ] Test directory structure
- [ ] Database mocking utilities
- [ ] CLI skeleton with Click
- [ ] Configuration via environment variables
- [ ] Basic unit tests for db.py
- [ ] Basic unit tests for ai_parser.py

## Success Metrics

- pytest runs with >50% coverage on core modules
- CLI `--help` displays all commands
- All tests pass in CI environment

---

## Day 1: Project Setup & Test Infrastructure

### Task 1.1: Project Restructure (2 hours)

**Files to create:**
```
├── pyproject.toml           # Modern packaging
├── .env.example             # Environment template
├── src/pitchbook/__init__.py
└── tests/
    ├── __init__.py
    └── conftest.py          # Shared fixtures
```

**Acceptance Criteria:**
- [ ] `pip install -e .` works
- [ ] `pytest` discovers tests
- [ ] Import `from pitchbook import ...` works

### Task 1.2: pytest Configuration (1 hour)

**pyproject.toml additions:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-v --tb=short --cov=pitchbook --cov-report=term-missing"

[tool.coverage.run]
source = ["src/pitchbook"]
branch = true
```

### Task 1.3: Test Fixtures (2 hours)

**File:** `tests/conftest.py`

```python
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_db_path():
    """Temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    Path(f.name).unlink(missing_ok=True)

@pytest.fixture
def fresh_db(temp_db_path):
    """Fresh database instance for each test."""
    from pitchbook.core.database import DatabaseManager
    db = DatabaseManager(db_path=temp_db_path)
    yield db

@pytest.fixture
def sample_article():
    """Sample high-relevance article data."""
    return {
        "url": "https://example.com/openai-funding",
        "title": "OpenAI Raises $6.6B in Largest AI Funding Round",
        "summary": "OpenAI closed Series C at $80B valuation",
        "content": "OpenAI announced a $6.6 billion Series C...",
        "published_date": "2026-02-15",
        "ai_relevance_score": 0.92,
        "is_deal_news": 1,
    }

@pytest.fixture
def sample_deal():
    """Sample deal data."""
    return {
        "company_name": "OpenAI",
        "funding_amount": 6_600_000_000,
        "round_type": "Series C",
        "investors": "Thrive Capital, Microsoft",
    }

@pytest.fixture
def populated_db(fresh_db, sample_article, sample_deal):
    """Database with sample data."""
    article_id = fresh_db.insert_article(**sample_article)
    fresh_db.insert_deal(article_id=article_id, **sample_deal)
    fresh_db.add_article_category(article_id, "generative_ai")
    yield fresh_db
```

---

## Day 2: Database Unit Tests (TDD)

### Task 2.1: Write Database Tests FIRST (3 hours)

**File:** `tests/unit/test_database.py`

Test classes:
- `TestDatabaseInit` - Table creation, idempotency
- `TestArticleOperations` - CRUD, deduplication, pagination
- `TestDealOperations` - Deal insertion, retrieval
- `TestCategoryOperations` - Category management
- `TestStatistics` - Aggregation queries
- `TestConfiguration` - Custom paths

**Target:** 15+ test cases

### Task 2.2: Refactor db.py to Pass Tests (2 hours)

**Changes needed:**
1. Add `get_table_names()` method
2. Accept `db_path` parameter consistently
3. Ensure all methods return expected types

---

## Day 3: AI Parser Unit Tests (TDD)

### Task 3.1: Write Parser Tests FIRST (3 hours)

**File:** `tests/unit/test_ai_parser.py`

Test classes:
- `TestRelevanceScoring` - High/low/edge cases
- `TestCategoryExtraction` - Single/multiple/none
- `TestDealDetection` - Amounts, round types
- `TestEntityExtraction` - Companies, investors
- `TestSummaryGeneration` - Length, content

**Target:** 15+ test cases

### Task 3.2: Adjust Parser Implementation (2 hours)

Ensure all tests pass without regressions.

---

## Day 4: CLI Foundation

### Task 4.1: Install Click & Create CLI Skeleton (2 hours)

**Dependencies:**
```
click>=8.1.0
python-dotenv>=1.0.0
```

**File:** `src/pitchbook/cli.py`

Commands to implement:
- `pitchbook --help/--version`
- `pitchbook scrape [--source] [--limit] [--dry-run]`
- `pitchbook generate [--format] [--output] [--days] [--preview]`
- `pitchbook serve [--host] [--port] [--reload]`
- `pitchbook dashboard [--open] [--output]`
- `pitchbook db init|migrate|export|import|stats|clear`
- `pitchbook schedule start|stop|status|run-now`

### Task 4.2: CLI Tests (2 hours)

**File:** `tests/unit/test_cli.py`

```python
from click.testing import CliRunner
from pitchbook.cli import cli

def test_help_displays(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Pitchbook" in result.output

def test_scrape_dry_run(runner):
    result = runner.invoke(cli, ["scrape", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
```

---

## Day 5: Configuration & Integration

### Task 5.1: Environment-based Configuration (2 hours)

**File:** `src/pitchbook/config.py`

```python
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    db_path: Path = Field(default=Path("./data/ai_news.db"), env="PITCHBOOK_DB_PATH")
    api_host: str = Field(default="127.0.0.1", env="PITCHBOOK_API_HOST")
    api_port: int = Field(default=8000, env="PITCHBOOK_API_PORT")
    headless: bool = Field(default=True, env="PITCHBOOK_HEADLESS")
    log_level: str = Field(default="INFO", env="PITCHBOOK_LOG_LEVEL")
    
    class Config:
        env_file = ".env"
```

**File:** `.env.example`

```bash
PITCHBOOK_DB_PATH=./data/ai_news.db
PITCHBOOK_API_HOST=127.0.0.1
PITCHBOOK_API_PORT=8000
PITCHBOOK_HEADLESS=true
PITCHBOOK_LOG_LEVEL=INFO
```

### Task 5.2: Configuration Tests (1 hour)

```python
def test_default_values():
    settings = Settings()
    assert settings.api_port == 8000

def test_env_override(monkeypatch):
    monkeypatch.setenv("PITCHBOOK_API_PORT", "9000")
    settings = Settings()
    assert settings.api_port == 9000
```

### Task 5.3: Integration Checklist (2 hours)

- [ ] Run full test suite
- [ ] Verify coverage > 50%
- [ ] Test CLI end-to-end
- [ ] Document any issues found

---

## Sprint Completion Checklist

### Code Deliverables
- [ ] `pyproject.toml` with modern packaging
- [ ] `tests/conftest.py` with fixtures
- [ ] `tests/unit/test_database.py` (15+ tests)
- [ ] `tests/unit/test_ai_parser.py` (15+ tests)
- [ ] `tests/unit/test_cli.py` (5+ tests)
- [ ] `src/pitchbook/cli.py` with Click
- [ ] `src/pitchbook/config.py` with pydantic-settings
- [ ] `.env.example` template

### Quality Metrics
- [ ] pytest passes: 100%
- [ ] Coverage: >50%
- [ ] CLI `--help` works

---

## Time Summary

| Day | Tasks | Hours |
|-----|-------|-------|
| 1 | Project setup, pytest, fixtures | 5 |
| 2 | Database tests (TDD) | 5 |
| 3 | Parser tests (TDD) | 5 |
| 4 | CLI foundation | 4 |
| 5 | Config, integration | 5 |
| **Total** | | **24 hours** |
