# 📊 AI News Intelligence Platform

A professional-grade news scraper and intelligence system for tracking AI market developments, deals, and funding. Designed as a **trusted information source for journalists and investors** covering the global AI landscape.

## 🎯 What It Does

This platform intelligently scrapes and analyzes AI-related news from PitchBook, extracting:

- **Funding Deals**: Automatically detects Series A/B/C funding rounds, amounts, and investors
- **Company Intelligence**: Tracks AI companies, their funding status, and market positioning  
- **Investor Activity**: Monitors VC and accelerator investments in AI sector
- **Market Signals**: Categorizes news by AI subcategories (generative AI, ML infrastructure, AI safety, etc.)
- **Deduplication**: Smart URL-based deduplication prevents duplicate reporting
- **Relevance Scoring**: AI-powered relevance scoring (0-1) for each article

## 🏗️ Architecture

### Database-First Design

All news data is stored in **SQLite** (`ai_news.db`) with:

- **News Articles Table**: Full text, URLs, publication dates, AI relevance scores
- **Deals Table**: Extracted funding amounts, company names, round types, investors
- **AI Categories**: 9 curated AI technology categories (Generative AI, ML Infrastructure, NLP, etc.)
- **Company Mentions**: Tracks company co-occurrences and funding
- **Investor Tracking**: VCs and accelerators mentioned in news

### Intelligent Extraction

The `AINewsParser` module:

- Detects **deal news** vs. general articles
- Extracts **funding amounts** in multiple formats ($5M, $1.2B, €50K)
- Identifies **funding rounds** (Seed, Series A/B/C, IPO, Acquisition)
- Scores **AI relevance** (0.0-1.0) based on keywords and context
- Categorizes articles into **9 AI technology areas**
- Deduplicates articles by URL hash

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

Dependencies:
- `playwright>=1.40.0` - Browser automation
- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=5.0.0` - XML/HTML library
- `sqlite3` - Built-in Python database

## 🚀 Quick Start

### 1. Scrape AI News (Primary Feature)

```bash
# Scrape and store in SQLite (recommended)
python main.py --news

# Show database statistics
python main.py --stats

# Scrape all data (companies, investors, people, news)
python main.py --all
```

### 2. View Intelligence Dashboard

```bash
# Open dashboard in browser
python main.py --view
```

The dashboard shows:
- News articles sorted by publication date
- Extracted deals with funding amounts
- AI relevance scores for each article
- Company and investor mentions
- Categorization by AI technology area

### 3. Query Database Directly

```python
from db import get_db

db = get_db()

# Get top deals
deals = db.get_deals(limit=50)
for deal in deals:
    print(f"{deal['company_name']}: ${deal['funding_amount']:,.0f} ({deal['round_type']})")

# Get articles by relevance
articles = db.get_articles(limit=100, min_relevance=0.7)
for article in articles:
    print(f"{article['title']} - Score: {article['ai_relevance_score']:.2f}")

# Show statistics
stats = db.get_statistics()
print(f"Total Funding Tracked: ${stats['total_funding_usd']:,.0f}")
```

## 📋 AI Technology Categories

Articles are automatically categorized into:

1. **Generative AI**: LLMs, text/image generation, transformers, GPT, Claude
2. **Machine Learning**: Neural networks, deep learning, training
3. **Computer Vision**: Object detection, image recognition, visual models
4. **NLP**: Language models, translation, speech recognition
5. **AI Infrastructure**: GPUs, TPUs, inference, model serving, MLOps
6. **AI Agents**: Autonomous agents, reasoning, task automation
7. **Robotics**: Robot learning, embodied AI
8. **AI Safety**: Alignment, fairness, interpretability, ethics
9. **Enterprise AI**: Business AI, SaaS, workplace automation

## 🔍 Advanced Usage

### Custom Search Terms

Edit `config.py` to add custom search terms:

```python
AI_SEARCH_TERMS = [
    "artificial intelligence",
    "generative AI",
    "AI startup funding",
    "your custom term here",
]
```

### Rate Limiting

Control scraping speed to avoid detection:

```python
# Adjust in config.py
MIN_DELAY_SECONDS = 3
MAX_DELAY_SECONDS = 6
MAX_RETRIES = 3
```

### Command-Line Options

```bash
# Run with custom delay (seconds)
python main.py --news --delay 5

# Scrape specific categories
python main.py --companies --investors

# Set max pages to scrape per term
python main.py --news --max-pages 3

# Specify output directory
python main.py --news --output-dir ./data
```

### Filtering Articles by Relevance

```python
from db import get_db

db = get_db()

# Get only high-relevance AI articles
articles = db.get_articles(
    limit=50,
    min_relevance=0.7  # Only articles scoring 70%+ relevance
)
```

## 📊 Database Schema

### news_articles

| Column | Type | Description |
|--------|------|-------------|
| id | INT | Primary key |
| url | TEXT | Article URL (unique) |
| url_hash | TEXT | MD5 hash for deduplication |
| title | TEXT | Article title |
| summary | TEXT | AI-generated summary |
| content | TEXT | Full article content |
| published_date | TEXT | Publication date |
| scraped_date | TEXT | When we scraped it |
| ai_relevance_score | REAL | 0.0-1.0 relevance |
| is_deal_news | INT | 1 if funding/acquisition |

### deals

| Column | Type | Description |
|--------|------|-------------|
| article_id | INT | FK to articles |
| company_name | TEXT | Company being funded |
| funding_amount | REAL | USD amount |
| round_type | TEXT | Series A, Seed, IPO, etc. |
| investors | TEXT | Comma-separated investor names |
| announcement_date | TEXT | Deal date |

### ai_categories & article_categories

Links articles to technology categories with relevance weights.

## 🤖 AI Parser Features

The intelligent parser:

- **Extracts Funding**: Finds $5M, $1.2B, €500K patterns
- **Identifies Rounds**: Detects "Series A", "Seed", "IPO", "Acquisition"
- **Scores Relevance**: Weighs keywords, categories, context
- **Finds Entities**: Extracts company and investor names
- **Deduplicates**: MD5 hash on URLs prevents repeats
- **Generates Summaries**: Creates concise news summaries

### Relevance Scoring Logic

```
Base score: 0.0
+ 0.5 if title contains "AI" or "artificial intelligence"
+ 0.3 if body contains core AI keywords
+ 0.2 if relevant AI category detected
+ 0.15 if deal news detected
+ 0.1 if funding amount mentioned
Result: Normalized to 0.0-1.0
```

## 📈 Statistics Available

```python
db.get_statistics()
# Returns:
{
    'total_articles': 245,
    'total_deals': 78,
    'total_companies': 156,
    'total_investors': 42,
    'total_funding_usd': 15000000000,  # $15B tracked
    'avg_relevance_score': 0.82
}
```

## 🔄 Workflow for Reporters

1. **Scrape Fresh Data**
   ```bash
   python main.py --news
   ```

2. **View Dashboard**
   ```bash
   python main.py --view
   ```

3. **Query by Relevance**
   ```bash
   python main.py --stats  # See what's new
   ```

4. **Find Specific Stories**
   - Use dashboard search
   - Filter by AI category
   - Sort by relevance score

5. **Track Funding Trends**
   ```python
   from db import get_db
   db = get_db()
   deals = db.get_deals(limit=50)
   # Analyze emerging companies and investors
   ```

## 🛡️ Deduplication Strategy

- **URL Hash**: MD5 hash of URL stored in DB
- **Prevents**: Same article scraped multiple times
- **Covers**: Different search terms, multiple scrapes
- **Logic**: Check URL hash before inserting

## 📝 Project Structure

```
pitchbooks/
├── main.py              # CLI entry point
├── config.py            # Search terms, rate limiting
├── db.py               # SQLite database module
├── viewer.py           # HTML dashboard generator
├── ai_news.db          # SQLite database (auto-created)
├── requirements.txt
├── README.md
├── models/
│   ├── schemas.py      # Data models
│   └── __init__.py
├── scraper/
│   ├── base.py         # Browser automation base
│   ├── news.py         # News scraper (SQLite-integrated)
│   ├── ai_parser.py    # Intelligent AI news parser
│   ├── companies.py    # Company scraper
│   ├── accelerators.py # Investor scraper
│   ├── people.py       # People scraper
│   └── __init__.py
└── output/
    └── dashboard.html   # Generated dashboard
```

## ⚙️ Configuration

### config.py Settings

```python
# Search terms for news discovery
AI_SEARCH_TERMS = [...]

# Rate limiting
MIN_DELAY_SECONDS = 3
MAX_DELAY_SECONDS = 6

# Pagination
MAX_SEARCH_PAGES = 5
MAX_ARTICLES_PAGES = 10

# Browser settings
HEADLESS = True
TIMEOUT_MS = 30000
```

## 🚨 Troubleshooting

### Database Lock Error
```
sqlite3.OperationalError: database is locked
```
**Solution**: Only one process can write at a time. Close other instances.

### Missing Articles
**Check**:
- Database created (`ai_news.db` exists)
- Run `python main.py --stats` to see current count
- Articles may be filtered by relevance score

### Connection Refused (403)
**Likely cause**: PitchBook blocking the IP. **Solutions**:
- Increase `MIN_DELAY_SECONDS` in config.py
- Use a different network/proxy
- Reduce `MAX_SEARCH_PAGES`

## 📄 License

MIT License - use freely for journalism and investor intelligence.

## 🤝 Contributing

Improvements welcome! Areas for enhancement:
- Additional scraping sources (Crunchbase, TechCrunch, VentureBeat)
- Better NER for company/person extraction
- Sentiment analysis on funding announcements
- Multi-language support
- Real-time news feed integration

---

**Version**: 2.0 (SQLite + AI Parser + Deduplication)  
**Last Updated**: February 2026  
**Status**: Production-ready for AI news intelligence
