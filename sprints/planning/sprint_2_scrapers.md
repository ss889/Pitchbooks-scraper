# Sprint 2: Scraper Reliability & Data Sources

**Duration:** 1 week  
**Status:** Planning  
**Depends On:** Sprint 1 completion  

---

## Goal

Multiple data sources, retry logic, fallback behavior

## Deliverables

- [ ] RSS feed scraper (TechCrunch, VentureBeat, etc.)
- [ ] Enhanced retry/backoff logic
- [ ] Proxy rotation support
- [ ] Scraper health monitoring
- [ ] Data source priority system
- [ ] Unit tests for all scrapers

## Success Metrics

- At least 2 working data sources
- 95% success rate on scrape attempts
- Automatic fallback when primary source fails

## Technical Details

### RSS Sources to Implement

| Source | Feed URL | Priority |
|--------|----------|----------|
| TechCrunch AI | `/feed/?tag=ai` | 1 |
| VentureBeat AI | `/category/ai/feed/` | 2 |
| The Verge AI | `/ai/rss/index.xml` | 3 |
| MIT Tech Review | `/feed/` (filtered) | 4 |

### Retry Strategy

```python
# Exponential backoff configuration
BASE_DELAY = 3  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2

# Delay calculation: BASE_DELAY * (BACKOFF_FACTOR ^ attempt)
# Attempt 1: 3s, Attempt 2: 6s, Attempt 3: 12s
```

### Proxy Rotation (Optional)

```yaml
scraping:
  proxies:
    enabled: false
    provider: "rotating"
    endpoints:
      - url: "proxy1.example.com"
      - url: "proxy2.example.com"
```

---

## Tasks Breakdown

*To be detailed when sprint becomes active*

## Notes

- PitchBook direct scraping blocked - must rely on alternative sources
- RSS feeds are more reliable and ToS-compliant
- Consider Crunchbase API as paid alternative (budget TBD)
