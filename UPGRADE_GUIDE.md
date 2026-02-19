# Upgrade Guide: AI News Intelligence Platform v2.0

## What's Changed

Your PitchBook scraper has been transformed into a professional **AI News Intelligence Platform** designed for reporters and investors. Here's what's new:

## 🎯 Major Improvements

### 1. **SQLite Database Instead of JSON**
- **Before**: News stored in `news.json`, duplicates possible
- **After**: Centralized SQLite database (`ai_news.db`) with automatic deduplication
- **Benefit**: Faster queries, no duplicates, structured data, better for analysis

### 2. **Intelligent AI News Parser**
- **Before**: Basic text extraction
- **After**: Smart parser that:
  - Extracts funding amounts ($5M, €1.2B, etc.)
  - Identifies funding rounds (Series A, Seed, IPO)
  - Scores AI relevance (0-1 scale)
  - Categorizes into 9 AI technology areas
  - Detects deal news automatically

### 3. **Deduplication**
- **Before**: Same article could be scraped multiple times
- **After**: MD5 hash-based deduplication prevents duplicates across all searches
- **Benefit**: No redundant information, cleaner dataset

### 4. **Better Data Extraction**
News articles now extract:
- ✅ Funding amounts and currencies
- ✅ Company names mentioned
- ✅ Investor/VC names
- ✅ Deal types (Series A, acquisition, IPO)
- ✅ AI technology categories
- ✅ Publication dates
- ✅ Article relevance scores

### 5. **New Tools**

#### `export.py` - Export tools for reporters
```bash
python export.py --deals                 # CSV of all deals
python export.py --articles              # JSON of articles
python export.py --report                # Text funding report
python export.py --stats                 # Database statistics
```

#### `quickstart.py` - Setup verification
```bash
python quickstart.py                     # Check everything is working
```

## 📊 Database Schema

New SQLite tables:

| Table | Purpose |
|-------|---------|
| `news_articles` | Core articles with metadata |
| `deals` | Extracted funding deals |
| `ai_categories` | AI technology categories |
| `article_categories` | Article-to-category mappings |
| `companies` | Extracted company info |
| `investors` | Extracted investor info |
| `article_mentions` | Company/investor mentions |

## 🚀 Usage: Old vs New

### Scraping Fresh News

**Before**:
```bash
python main.py --news
python main.py --view  # View JSON output
```

**After** (same commands, better results):
```bash
python main.py --news         # Stores in SQLite, auto-dedup
python main.py --stats        # See funding/deal totals
python main.py --view         # Dashboard now shows deals extracted from DB
```

### Analyzing Data

**Before** (had to parse JSON manually):
```python
import json
with open('output/news.json') as f:
    news = json.load(f)
# Manual filtering...
```

**After** (query directly):
```python
from db import get_db

db = get_db()

# Get high-relevance articles
articles = db.get_articles(limit=50, min_relevance=0.7)

# Get all deals with funding amounts
deals = db.get_deals(limit=100)

# Get statistics
stats = db.get_statistics()
print(f"Total funding tracked: ${stats['total_funding_usd']:,.0f}")
```

### Exporting for Reports

**Before** (no export tools):
```bash
# Manual copy/paste from JSON files
```

**After**:
```bash
# Export to CSV for Excel
python export.py --deals

# Export to JSON for API integration  
python export.py --articles

# Generate funding report
python export.py --report
```

## 📋 AI Categories (New)

Articles are auto-categorized into:

1. **Generative AI** - LLMs, text/image generation, GPT, Claude
2. **Machine Learning** - Neural networks, training, deep learning
3. **Computer Vision** - Object detection, image recognition
4. **NLP** - Language models, speech, translation
5. **AI Infrastructure** - GPUs, TPUs, model serving, MLOps
6. **AI Agents** - Autonomous agents, reasoning
7. **Robotics** - Robot learning, embodied AI
8. **AI Safety** - Alignment, fairness, ethics
9. **Enterprise AI** - Business AI, SaaS, workplace

## 🔄 Migration Path (Optional)

### Option A: Start Fresh (Recommended)
```bash
# Delete old JSON files (optional backup first)
mv output/news.json output/news.json.backup

# Start scraping with new system
python main.py --news

# All new data goes to SQLite
```

### Option B: Keep Existing Data
```bash
# Your JSON files still work
# New news scrapes go to SQLite
# Dashboard shows both JSON and SQLite data
```

## ✨ New Features for Reporters

### 1. Relevance Scoring
```python
from db import get_db
db = get_db()

# Get only highly relevant AI articles (70%+ relevance)
hot_news = db.get_articles(limit=20, min_relevance=0.7)
```

### 2. Deal Tracking
```python
# Access financial data for stories
deals = db.get_deals(limit=50)
for deal in deals:
    print(f"{deal['company_name']} raised ${deal['funding_amount']:,.0f}")
```

### 3. Funding Reports
```bash
python export.py --report
# Generates AI_DEALS_REPORT.txt with top deals
```

### 4. Smart Deduplication
- Same article won't appear twice (even from different searches)
- URL-based detection using MD5 hashing
- Automatic when you re-run scraper

## 🔧 Configuration Unchanged

All existing config still works:

```python
# config.py - Still supports all these settings:
AI_SEARCH_TERMS = [...]
MIN_DELAY_SECONDS = 3
MAX_DELAY_SECONDS = 6
MAX_SEARCH_PAGES = 5
MAX_ARTICLES_PAGES = 10
HEADLESS = True
```

## 📁 File Changes

### New Files
- `db.py` - SQLite database manager
- `scraper/ai_parser.py` - Intelligent parser
- `export.py` - Data export tool
- `quickstart.py` - Setup verification
- `ai_news.db` - SQLite database (auto-created)

### Updated Files
- `main.py` - Added `--stats` flag, database integration
- `scraper/news.py` - Now uses SQLite, AI parser
- `viewer.py` - Shows data from SQLite
- `config.py` - Added more search terms
- `requirements.txt` - No new dependencies (SQLite3 is built-in)

### Unchanged Files
- `scraper/base.py` - Browser automation (same)
- `scraper/companies.py` - Company scraper (same)
- `scraper/accelerators.py` - Investor scraper (same)
- `scraper/people.py` - People scraper (same)
- `models/schemas.py` - Data models (kept for compatibility)

## ⚠️ Important Notes

### Backward Compatibility
- Old JSON files still work
- Dashboard shows both JSON and SQLite data
- Existing scripts that read JSON still work
- Companies/investors/people scrapers unchanged

### Breaking Changes
- None! All existing commands still work
- Just get better results and new features

### Performance
- SQLite queries are **much faster** than JSON
- Deduplication means cleaner, smaller dataset
- Dashboard loads instantly from DB

## 🎓 Learning Path

1. **Start**: `python quickstart.py` - Verify setup
2. **Scrape**: `python main.py --news` - Collect data
3. **Explore**: `python main.py --view` - See dashboard
4. **Query**: Use Python to explore the database
5. **Export**: `python export.py --all` - Generate reports

## 💡 Common Tasks

### Show Database Size
```bash
python main.py --stats
```

### Find Recent Funding Deals
```python
from db import get_db
db = get_db()
deals = db.get_deals(limit=25)
for d in deals:
    print(f"{d['company_name']}: ${d['funding_amount']:,.0f}")
```

### List High-Relevance Articles
```python
from db import get_db
db = get_db()
articles = db.get_articles(min_relevance=0.8, limit=30)
for a in articles:
    print(f"[{a['ai_relevance_score']:.0%}] {a['title']}")
```

### Export for Analysis
```bash
# Export everything
python export.py --all

# Or specific formats
python export.py --deals --output my_deals.csv
python export.py --articles --output articles.json
```

## 🆘 Getting Help

### Database Issues
```bash
# Verify database is working
python quickstart.py

# Check statistics
python main.py --stats
```

### Scraping Problems
```bash
# Run with slower delays
python main.py --news --delay 10

# Check logs (shown in terminal output)
```

### Data Questions
```bash
# Open dashboard for visual exploration
python main.py --view
```

## 📚 Learn More

- **README_v2.md** - Complete documentation
- **db.py** - Database API documentation (docstrings)
- **scraper/ai_parser.py** - Parser logic and categories
- **export.py** - Export tool with examples

## 🎉 You're All Set!

Your AI news intelligence platform is now:
- ✅ SQLite-based (faster, scalable)
- ✅ Intelligent (extracts deals, scores relevance)
- ✅ Deduplicated (no repeated articles)
- ✅ Professional (ready for reporters)

Start scraping:
```bash
python main.py --news
```

View results:
```bash
python main.py --stats
python main.py --view
```

Enjoy your AI news intelligence platform! 🚀
