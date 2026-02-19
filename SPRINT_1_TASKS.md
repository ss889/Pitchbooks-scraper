# Sprint 1: Foundation & Testing Infrastructure
## Detailed Task Breakdown

**Sprint Duration:** 5 days  
**Methodology:** Test-Driven Development (Red-Green-Refactor)  
**Priority:** P0 - Critical Foundation  

---

## Day 1: Project Setup & Test Infrastructure

### Task 1.1: Project Restructure (2 hours)
**Goal:** Modern Python project layout

```
Files to create:
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

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
]
```

**Acceptance Criteria:**
- [ ] `pytest` runs without errors
- [ ] Coverage report generates
- [ ] Test discovery works

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

**Acceptance Criteria:**
- [ ] Fixtures importable in tests
- [ ] Database cleanup works
- [ ] No test pollution between tests

---

## Day 2: Database Unit Tests (TDD)

### Task 2.1: Write Database Tests FIRST (3 hours)

**File:** `tests/unit/test_database.py`

```python
"""
Database layer unit tests.
TDD: These tests are written BEFORE implementation changes.
"""
import pytest


class TestDatabaseInit:
    """Database initialization tests."""
    
    def test_init_creates_tables(self, fresh_db):
        """Tables should be created on init."""
        tables = fresh_db.get_table_names()
        assert "news_articles" in tables
        assert "deals" in tables
        assert "ai_categories" in tables
        assert "article_categories" in tables
    
    def test_init_is_idempotent(self, fresh_db):
        """Multiple inits should not fail or duplicate tables."""
        fresh_db.init_db()
        fresh_db.init_db()
        # Should not raise


class TestArticleOperations:
    """Article CRUD tests."""
    
    def test_insert_article_success(self, fresh_db, sample_article):
        """Should insert article and return ID."""
        article_id = fresh_db.insert_article(**sample_article)
        assert article_id is not None
        assert article_id > 0
    
    def test_insert_article_generates_url_hash(self, fresh_db, sample_article):
        """URL hash should be auto-generated."""
        article_id = fresh_db.insert_article(**sample_article)
        # Verify hash exists (implementation detail, may need adjustment)
        assert fresh_db.article_exists(sample_article["url"])
    
    def test_insert_duplicate_url_rejected(self, fresh_db, sample_article):
        """Duplicate URLs should be rejected."""
        fresh_db.insert_article(**sample_article)
        result = fresh_db.insert_article(**sample_article)
        assert result is None  # Duplicate rejected
    
    def test_article_exists_true(self, populated_db, sample_article):
        """Should return True for existing article."""
        assert populated_db.article_exists(sample_article["url"]) is True
    
    def test_article_exists_false(self, fresh_db):
        """Should return False for non-existent article."""
        assert fresh_db.article_exists("https://nonexistent.com") is False
    
    def test_get_articles_returns_list(self, populated_db):
        """Should return list of articles."""
        articles = populated_db.get_articles(limit=10)
        assert isinstance(articles, list)
        assert len(articles) >= 1
    
    def test_get_articles_pagination_limit(self, populated_db):
        """Limit should restrict results."""
        articles = populated_db.get_articles(limit=1)
        assert len(articles) == 1
    
    def test_get_articles_filter_by_relevance(self, populated_db):
        """Should filter by minimum relevance."""
        articles = populated_db.get_articles(min_relevance=0.9)
        for article in articles:
            assert article["ai_relevance_score"] >= 0.9


class TestDealOperations:
    """Deal CRUD tests."""
    
    def test_insert_deal_success(self, populated_db, sample_deal):
        """Should insert deal with article reference."""
        # Get existing article
        articles = populated_db.get_articles(limit=1)
        article_id = articles[0]["id"]
        
        deal_id = populated_db.insert_deal(article_id=article_id, **sample_deal)
        assert deal_id is not None
    
    def test_get_deals_returns_list(self, populated_db):
        """Should return list of deals."""
        deals = populated_db.get_deals(limit=10)
        assert isinstance(deals, list)


class TestCategoryOperations:
    """Category management tests."""
    
    def test_add_article_category_success(self, populated_db):
        """Should add category to article."""
        articles = populated_db.get_articles(limit=1)
        result = populated_db.add_article_category(articles[0]["id"], "machine_learning")
        assert result is True
    
    def test_add_article_category_creates_if_missing(self, populated_db):
        """Should create category if it doesn't exist."""
        articles = populated_db.get_articles(limit=1)
        result = populated_db.add_article_category(articles[0]["id"], "new_category_xyz")
        assert result is True
    
    def test_get_categories_returns_list(self, populated_db):
        """Should return list of categories."""
        categories = populated_db.get_categories()
        assert isinstance(categories, list)


class TestStatistics:
    """Statistics query tests."""
    
    def test_get_statistics_returns_dict(self, populated_db):
        """Should return statistics dictionary."""
        stats = populated_db.get_statistics()
        assert isinstance(stats, dict)
        assert "total_articles" in stats
        assert "total_deals" in stats
    
    def test_get_statistics_counts_accurate(self, populated_db):
        """Statistics should reflect actual data."""
        stats = populated_db.get_statistics()
        assert stats["total_articles"] >= 1


class TestConfiguration:
    """Database configuration tests."""
    
    def test_custom_db_path(self, temp_db_path):
        """Should accept custom database path."""
        from pitchbook.core.database import DatabaseManager
        db = DatabaseManager(db_path=temp_db_path)
        assert db.db_path == temp_db_path
```

**Acceptance Criteria:**
- [ ] All tests written (RED phase)
- [ ] Tests run and fail as expected
- [ ] Coverage target identified

### Task 2.2: Refactor db.py to Pass Tests (2 hours)

**Changes needed:**
1. Add `get_table_names()` method
2. Accept `db_path` parameter consistently
3. Ensure all methods return expected types

**Acceptance Criteria:**
- [ ] All database tests pass (GREEN phase)
- [ ] No regressions in existing functionality

---

## Day 3: AI Parser Unit Tests (TDD)

### Task 3.1: Write Parser Tests FIRST (3 hours)

**File:** `tests/unit/test_ai_parser.py`

```python
"""
AI Parser unit tests.
TDD: Tests written before implementation changes.
"""
import pytest
from pitchbook.parsers.ai_parser import AINewsParser


@pytest.fixture
def parser():
    """Parser instance."""
    return AINewsParser()


class TestRelevanceScoring:
    """Relevance calculation tests."""
    
    def test_high_relevance_for_ai_funding(self, parser):
        """AI funding articles should score high."""
        result = parser.parse_article(
            title="OpenAI Raises $6.6B in Series C Funding",
            content="OpenAI announced a $6.6 billion funding round for AI development...",
            url="https://example.com/test"
        )
        assert result["ai_relevance_score"] >= 0.8
    
    def test_low_relevance_for_non_ai(self, parser):
        """Non-AI articles should score low."""
        result = parser.parse_article(
            title="Restaurant Chain Expands to New Markets",
            content="The restaurant company plans to open 50 new locations...",
            url="https://example.com/test"
        )
        assert result["ai_relevance_score"] < 0.3
    
    def test_relevance_range_valid(self, parser):
        """Score should be between 0 and 1."""
        result = parser.parse_article(
            title="Test Article",
            content="Some content here",
            url="https://example.com/test"
        )
        assert 0.0 <= result["ai_relevance_score"] <= 1.0


class TestCategoryExtraction:
    """Category extraction tests."""
    
    def test_extract_generative_ai(self, parser):
        """Should detect generative AI category."""
        result = parser.parse_article(
            title="New LLM Breakthrough",
            content="The large language model demonstrates GPT-4 level performance...",
            url="https://example.com/test"
        )
        assert "generative_ai" in result["ai_categories"]
    
    def test_extract_multiple_categories(self, parser):
        """Should detect multiple categories."""
        result = parser.parse_article(
            title="AI Safety Startup Raises Seed Round",
            content="The company focuses on alignment and safety for large language models...",
            url="https://example.com/test"
        )
        categories = result["ai_categories"]
        assert len(categories) >= 1
    
    def test_no_categories_for_irrelevant(self, parser):
        """Non-AI articles should have no categories."""
        result = parser.parse_article(
            title="Weather Report for Monday",
            content="Sunny skies expected throughout the week...",
            url="https://example.com/test"
        )
        assert len(result["ai_categories"]) == 0


class TestDealDetection:
    """Deal extraction tests."""
    
    def test_detect_deal_news(self, parser):
        """Should detect when article is about a deal."""
        result = parser.parse_article(
            title="Startup Raises $50M Series A",
            content="The AI startup announced a $50 million Series A round...",
            url="https://example.com/test"
        )
        assert result["is_deal_news"] is True
    
    def test_extract_funding_amount(self, parser):
        """Should extract funding amount."""
        result = parser.parse_article(
            title="Company Raises $100M",
            content="The company secured $100 million in funding...",
            url="https://example.com/test"
        )
        assert len(result["deals"]) >= 1
        assert result["deals"][0]["amount_usd"] == 100_000_000
    
    def test_extract_funding_billions(self, parser):
        """Should handle billion-dollar amounts."""
        result = parser.parse_article(
            title="OpenAI Raises $6.6B",
            content="OpenAI announced $6.6 billion in new funding...",
            url="https://example.com/test"
        )
        deals = result["deals"]
        assert any(d["amount_usd"] == 6_600_000_000 for d in deals)
    
    def test_extract_round_type(self, parser):
        """Should extract round type."""
        result = parser.parse_article(
            title="Series B Funding Announced",
            content="The company closed a Series B round...",
            url="https://example.com/test"
        )
        deals = result["deals"]
        assert any("series_b" in str(d.get("round_type", "")).lower() for d in deals)


class TestEntityExtraction:
    """Company and investor extraction tests."""
    
    def test_extract_known_companies(self, parser):
        """Should extract known AI companies."""
        result = parser.parse_article(
            title="OpenAI and Anthropic Partnership",
            content="OpenAI and Anthropic announced a joint research initiative...",
            url="https://example.com/test"
        )
        companies = [c.lower() for c in result["companies"]]
        assert "openai" in companies or "anthropic" in companies
    
    def test_extract_known_investors(self, parser):
        """Should extract known investors."""
        result = parser.parse_article(
            title="Sequoia Leads New Round",
            content="Sequoia Capital led the funding round alongside Andreessen Horowitz...",
            url="https://example.com/test"
        )
        investors = [i.lower() for i in result["investors"]]
        assert any("sequoia" in inv for inv in investors)


class TestSummaryGeneration:
    """Summary generation tests."""
    
    def test_summary_not_empty(self, parser):
        """Summary should be generated."""
        result = parser.parse_article(
            title="Test Article Title",
            content="This is the article content with multiple sentences.",
            url="https://example.com/test"
        )
        assert result["summary"] is not None
        assert len(result["summary"]) > 0
    
    def test_summary_reasonable_length(self, parser):
        """Summary should not be too long."""
        long_content = "AI startup news. " * 100
        result = parser.parse_article(
            title="Long Article",
            content=long_content,
            url="https://example.com/test"
        )
        assert len(result["summary"]) < 500
```

**Acceptance Criteria:**
- [ ] All parser tests written
- [ ] Tests cover edge cases
- [ ] Clear test names

### Task 3.2: Adjust Parser Implementation (2 hours)

**Acceptance Criteria:**
- [ ] All parser tests pass
- [ ] No performance regressions

---

## Day 4: CLI Foundation

### Task 4.1: Install Click & Create CLI Skeleton (2 hours)

**Add to requirements:**
```
click>=8.1.0
python-dotenv>=1.0.0
```

**File:** `src/pitchbook/cli.py`

```python
"""
Pitchbook CLI - Command-line interface for AI news intelligence.
"""
import click
from pathlib import Path


@click.group()
@click.version_option(version="2.0.0", prog_name="pitchbook")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress output")
@click.option("--config", type=click.Path(), help="Config file path")
@click.pass_context
def cli(ctx, verbose, quiet, config):
    """Pitchbook - AI Investment News Intelligence Platform."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["config"] = config


@cli.command()
@click.option("--source", default="all", help="Data source (pitchbook, rss, all)")
@click.option("--limit", default=100, help="Maximum articles to fetch")
@click.option("--dry-run", is_flag=True, help="Show what would be scraped")
@click.pass_context
def scrape(ctx, source, limit, dry_run):
    """Run scrapers to fetch new articles."""
    if dry_run:
        click.echo(f"[DRY RUN] Would scrape from: {source}, limit: {limit}")
        return
    
    click.echo(f"Scraping from {source}...")
    # TODO: Implement scraper invocation


@cli.command()
@click.option("--format", "output_format", default="html", 
              type=click.Choice(["html", "markdown", "pdf"]))
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--days", default=7, help="Include articles from last N days")
@click.option("--preview", is_flag=True, help="Preview without saving")
@click.pass_context
def generate(ctx, output_format, output, days, preview):
    """Generate newsletter content."""
    click.echo(f"Generating {output_format} newsletter for last {days} days...")
    # TODO: Implement newsletter generation


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.pass_context
def serve(ctx, host, port, reload):
    """Start the API server."""
    click.echo(f"Starting API server on {host}:{port}...")
    # TODO: Implement server startup


@cli.command()
@click.option("--open", "open_browser", is_flag=True, help="Open in browser")
@click.option("--output", type=click.Path(), default="dashboard.html")
@click.pass_context
def dashboard(ctx, open_browser, output):
    """Generate HTML dashboard."""
    click.echo(f"Generating dashboard: {output}")
    # TODO: Implement dashboard generation


@cli.group()
def db():
    """Database management commands."""
    pass


@db.command()
def init():
    """Initialize database schema."""
    click.echo("Initializing database...")
    from pitchbook.core.database import get_db
    db = get_db()
    click.echo("✓ Database initialized")


@db.command()
def stats():
    """Show database statistics."""
    from pitchbook.core.database import get_db
    db = get_db()
    statistics = db.get_statistics()
    
    click.echo("\n📊 Database Statistics")
    click.echo("=" * 40)
    click.echo(f"  Articles:    {statistics['total_articles']}")
    click.echo(f"  Deals:       {statistics['total_deals']}")
    click.echo(f"  Companies:   {statistics['total_companies']}")
    click.echo(f"  Categories:  {statistics['total_categories']}")
    click.echo(f"  Total Funding: ${statistics['total_funding_usd']:,.0f}")


@db.command()
@click.confirmation_option(prompt="Are you sure you want to clear all data?")
def clear():
    """Clear all data from database."""
    click.echo("Clearing database...")
    # TODO: Implement clear
    click.echo("✓ Database cleared")


@cli.group()
def schedule():
    """Scheduler management commands."""
    pass


@schedule.command()
def start():
    """Start the scheduler daemon."""
    click.echo("Starting scheduler...")
    # TODO: Implement scheduler start


@schedule.command()
def status():
    """Show scheduler status."""
    click.echo("Scheduler status: Not running")
    # TODO: Implement status check


@schedule.command("run-now")
def run_now():
    """Trigger immediate scrape."""
    click.echo("Triggering immediate scrape...")
    # TODO: Implement immediate scrape


if __name__ == "__main__":
    cli()
```

**Entry point in pyproject.toml:**
```toml
[project.scripts]
pitchbook = "pitchbook.cli:cli"
```

**Acceptance Criteria:**
- [ ] `pitchbook --help` works
- [ ] All subcommands listed
- [ ] `pitchbook db stats` shows data

### Task 4.2: CLI Tests (2 hours)

**File:** `tests/unit/test_cli.py`

```python
"""CLI unit tests."""
import pytest
from click.testing import CliRunner
from pitchbook.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIBasics:
    
    def test_help_displays(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Pitchbook" in result.output
    
    def test_version_displays(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "2.0.0" in result.output


class TestScrapeCommand:
    
    def test_scrape_dry_run(self, runner):
        result = runner.invoke(cli, ["scrape", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output


class TestDBCommands:
    
    def test_db_stats(self, runner):
        result = runner.invoke(cli, ["db", "stats"])
        assert result.exit_code == 0
        assert "Articles" in result.output
```

---

## Day 5: Configuration & Integration

### Task 5.1: Environment-based Configuration (2 hours)

**File:** `src/pitchbook/config.py`

```python
"""
Configuration management using pydantic-settings.
Supports environment variables and .env files.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    db_path: Path = Field(
        default=Path("./data/ai_news.db"),
        env="PITCHBOOK_DB_PATH"
    )
    
    # API
    api_host: str = Field(default="127.0.0.1", env="PITCHBOOK_API_HOST")
    api_port: int = Field(default=8000, env="PITCHBOOK_API_PORT")
    api_key: Optional[str] = Field(default=None, env="PITCHBOOK_API_KEY")
    
    # Scraping
    headless: bool = Field(default=True, env="PITCHBOOK_HEADLESS")
    min_delay: float = Field(default=3.0, env="PITCHBOOK_MIN_DELAY")
    max_delay: float = Field(default=6.0, env="PITCHBOOK_MAX_DELAY")
    max_retries: int = Field(default=3, env="PITCHBOOK_MAX_RETRIES")
    
    # Scheduler
    scrape_hour: int = Field(default=2, env="PITCHBOOK_SCRAPE_HOUR")
    scrape_minute: int = Field(default=0, env="PITCHBOOK_SCRAPE_MINUTE")
    
    # Logging
    log_level: str = Field(default="INFO", env="PITCHBOOK_LOG_LEVEL")
    log_file: Optional[Path] = Field(default=None, env="PITCHBOOK_LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**File:** `.env.example`

```bash
# Pitchbook Configuration
# Copy to .env and customize

# Database
PITCHBOOK_DB_PATH=./data/ai_news.db

# API Server
PITCHBOOK_API_HOST=127.0.0.1
PITCHBOOK_API_PORT=8000
# PITCHBOOK_API_KEY=your-secret-key-here

# Scraping
PITCHBOOK_HEADLESS=true
PITCHBOOK_MIN_DELAY=3
PITCHBOOK_MAX_DELAY=6
PITCHBOOK_MAX_RETRIES=3

# Scheduler
PITCHBOOK_SCRAPE_HOUR=2
PITCHBOOK_SCRAPE_MINUTE=0

# Logging
PITCHBOOK_LOG_LEVEL=INFO
# PITCHBOOK_LOG_FILE=./logs/pitchbook.log
```

### Task 5.2: Configuration Tests (1 hour)

```python
"""Configuration tests."""
import pytest
import os
from pitchbook.config import Settings, get_settings


class TestSettings:
    
    def test_default_values(self):
        settings = Settings()
        assert settings.api_port == 8000
        assert settings.headless is True
    
    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("PITCHBOOK_API_PORT", "9000")
        settings = Settings()
        assert settings.api_port == 9000
    
    def test_db_path_is_path(self):
        settings = Settings()
        from pathlib import Path
        assert isinstance(settings.db_path, Path)
```

### Task 5.3: Integration Checklist (2 hours)

- [ ] Run full test suite
- [ ] Verify coverage > 50%
- [ ] Test CLI end-to-end
- [ ] Document any issues found

---

## Sprint 1 Completion Checklist

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
- [ ] No lint errors (if linter configured)
- [ ] CLI `--help` works

### Documentation
- [ ] Updated README with CLI usage
- [ ] Test coverage report generated

---

## Estimated Time Summary

| Day | Tasks | Hours |
|-----|-------|-------|
| 1 | Project setup, pytest, fixtures | 5 |
| 2 | Database tests (TDD) | 5 |
| 3 | Parser tests (TDD) | 5 |
| 4 | CLI foundation | 4 |
| 5 | Config, integration | 5 |
| **Total** | | **24 hours** |

---

**Ready to proceed to implementation?**
