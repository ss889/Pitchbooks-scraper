# PitchBook AI News Intelligence Platform

A professional-grade data pipeline that scrapes AI investment news and generates curated content for newsletters tracking AI funding trends, investor activity, and market intelligence.

**Built for newsletter creators who need reliable, comprehensive, and accessible data.**

## Features

- **Multi-Source Scraping**: PitchBook (primary) + RSS feeds (TechCrunch, VentureBeat, MIT Tech Review)
- **URL Validation**: Every article link is verified before storage
- **AI Relevance Scoring**: Automatic categorization and relevance scoring for AI content
- **Deal Extraction**: Automatic extraction of funding amounts, round types, and investors
- **Daily Automation**: Scheduled scraping at 2 AM with health monitoring
- **REST API**: FastAPI endpoints with pagination, filtering, and search
- **Docker Ready**: One-command deployment with docker-compose

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/ss889/Pitchbooks-scraper.git
cd Pitchbooks-scraper

# Start services
docker-compose up -d

# API is now available at http://localhost:8000
# Dashboard at http://localhost:8000/health
```

### Option 2: Local Development

```bash
# Clone and setup
git clone https://github.com/ss889/Pitchbooks-scraper.git
cd Pitchbooks-scraper

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Initialize database and run scraper
python scheduler.py --run-now

# Start API server
uvicorn api:app --reload
```

## API Documentation

### Health Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Full health status with scrape results |
| `GET /health/live` | Liveness check (is API running?) |
| `GET /health/ready` | Readiness check (is database connected?) |

### Articles Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /articles` | List articles with pagination |
| `GET /articles?category=generative_ai` | Filter by AI category |
| `GET /articles?min_relevance=0.8` | Filter by relevance score |
| `GET /articles?search=openai` | Search in title/content |

### Deals Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /deals` | List funding deals |
| `GET /deals?min_amount=1000000` | Filter by minimum amount |

### Statistics

| Endpoint | Description |
|----------|-------------|
| `GET /statistics` | Database statistics |
| `GET /categories` | List AI categories with counts |

## Project Structure

```
Pitchbooks-scraper/
├── README.md               # This file
├── Dockerfile              # Production container
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .gitignore
├── .dockerignore
│
├── api.py                  # FastAPI REST server
├── db.py                   # SQLite database layer
├── scheduler.py            # Daily scraper automation
├── simple_viewer.py        # HTML dashboard generator
│
├── scraper/                # PitchBook scrapers
│   ├── base.py             # Browser automation
│   ├── news.py             # News article scraper
│   ├── ai_parser.py        # AI relevance scoring
│   └── ...
│
├── src/
│   ├── scrapers/           # RSS feed scrapers
│   │   └── rss_scraper.py  # TechCrunch, VentureBeat
│   └── utils/
│       └── url_validator.py # URL verification
│
├── tests/                  # Test suite
│
└── data/                   # SQLite database (gitignored)
```

## Data Schema

### Articles Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `url` | TEXT | Article URL (unique) |
| `title` | TEXT | Article headline |
| `summary` | TEXT | Brief summary |
| `content` | TEXT | Full article text |
| `published_date` | TEXT | Publication date |
| `ai_relevance_score` | REAL | 0.0-1.0 relevance score |
| `is_deal_news` | INTEGER | 1 if contains funding info |
| `url_status` | TEXT | 'accessible', 'preview_only', 'inaccessible' |
| `source` | TEXT | Data source (pitchbook, techcrunch_ai, etc.) |

### Deals Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `article_id` | INTEGER | Foreign key to articles |
| `company_name` | TEXT | Company receiving funding |
| `funding_amount` | REAL | Amount in USD |
| `round_type` | TEXT | Seed, Series A, etc. |
| `investors` | TEXT | Comma-separated investor names |

### AI Categories

- `generative_ai` - LLMs, image generation, etc.
- `enterprise_ai` - Business applications
- `ai_infrastructure` - MLOps, compute
- `computer_vision` - Image/video AI
- `ai_safety` - Alignment, safety research
- `healthcare_ai` - Medical AI
- `robotics_ai` - Robotics and automation
- `autonomous_vehicles` - Self-driving
- `nlp` - Natural language processing

## Daily Scraping Schedule

The scheduler runs automatically at 2 AM (configurable) and:

1. Attempts PitchBook scraper (may fail due to access restrictions)
2. Runs RSS feed scrapers (always reliable)
3. Validates all new URLs
4. Generates health report

```bash
# Check last scrape status
cat scrape_health.json

# Run manually
python scheduler.py --run-now

# Start scheduler daemon
python scheduler.py
```

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

## Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run scraper manually
docker-compose exec api python scheduler.py --run-now

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

## Development

```bash
# Run tests
pytest tests/ -v

# Check URL validation
python validate_urls.py --fix

# Generate dashboard
python simple_viewer.py

# Start API with reload
uvicorn api:app --reload --port 8000
```

## Troubleshooting

### PitchBook Scraping Fails

PitchBook may block automated access. The scraper automatically falls back to RSS feeds which provide reliable coverage of AI funding news.

### Broken Article Links

Run URL validation to check and update link status:

```bash
python validate_urls.py --fix --remove-broken
```

### No New Articles

Check the scraper health:

```bash
python scheduler.py --status
```

## License

For educational and research purposes. Respect website terms of service.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

---

**Built for newsletter creators who obsess over data quality.**
