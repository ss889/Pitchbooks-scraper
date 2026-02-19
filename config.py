"""
Configuration for PitchBook AI Investing Scraper.
"""

# ── Search Terms ─────────────────────────────────────────────────────────
# Keywords used to find AI-related companies, investors, and news
AI_SEARCH_TERMS = [
    "artificial intelligence",
    "machine learning",
    "generative AI",
    "LLM",
    "AI infrastructure",
    "AI SaaS",
    "deep learning",
    "computer vision",
    "natural language processing",
    "agentic AI",    "AI agents",
    "AI startup funding",
    "generative AI funding",
    "AI acquisition",
    "AI venture capital",
    "AI safety",
    "multimodal AI",]

# ── Rate Limiting ────────────────────────────────────────────────────────
MIN_DELAY_SECONDS = 3       # Minimum delay between requests
MAX_DELAY_SECONDS = 6       # Maximum delay between requests
MAX_RETRIES = 3             # Retry count on failure
RETRY_BACKOFF_BASE = 2      # Exponential backoff multiplier

# ── Pagination ───────────────────────────────────────────────────────────
MAX_SEARCH_PAGES = 5        # Max search result pages to scrape per term
MAX_ARTICLES_PAGES = 10     # Max news article listing pages to scrape

# ── Output ───────────────────────────────────────────────────────────────
OUTPUT_DIR = "output"

# ── Browser ──────────────────────────────────────────────────────────────
HEADLESS = True             # Run browser in headless mode
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080
TIMEOUT_MS = 30000          # Page load timeout in milliseconds

# ── PitchBook URLs ───────────────────────────────────────────────────────
BASE_URL = "https://pitchbook.com"
SEARCH_URL = f"{BASE_URL}/profiles/search"
NEWS_URL = f"{BASE_URL}/news"
ARTICLES_URL = f"{NEWS_URL}/articles"
REPORTS_URL = f"{NEWS_URL}/reports"

# ── User Agents (rotated to avoid detection) ─────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
]
