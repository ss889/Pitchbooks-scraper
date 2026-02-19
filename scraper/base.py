"""
Base scraper with Playwright browser automation, rate limiting,
retry logic, and user-agent rotation.
"""

import asyncio
import random
import logging
import sys
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pitchbook")


class BaseScraper:
    """
    Manages a headless Playwright browser with:
      • Randomized delays between requests (rate limiting)
      • User-agent rotation
      • Retry with exponential backoff
      • Clean async context-manager lifecycle
    """

    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None
        self.log = logging.getLogger(self.__class__.__name__)

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def __aenter__(self):
        self.log.info("Launching browser …")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=config.HEADLESS)
        self._context = await self._browser.new_context(
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT},
            user_agent=random.choice(config.USER_AGENTS),
        )
        self.page = await self._context.new_page()
        self.page.set_default_timeout(config.TIMEOUT_MS)
        return self

    async def __aexit__(self, *exc):
        self.log.info("Closing browser …")
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    # ── Navigation helpers ───────────────────────────────────────────────

    async def _delay(self):
        """Random delay between requests to avoid detection."""
        wait = round(random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS), 1)
        self.log.debug(f"  [WAIT] waiting {wait}s ...")
        await asyncio.sleep(wait)

    async def goto(self, url: str, *, wait_until: str = "domcontentloaded") -> bool:
        """
        Navigate to *url* with retry + backoff.
        Returns True on success, False if all retries fail.
        """
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                await self._delay()
                self.log.info(f"  -> {url}")
                resp = await self.page.goto(url, wait_until=wait_until)
                if resp and resp.status == 200:
                    return True
                if resp and resp.status == 403:
                    self.log.warning(f"  [403] Forbidden (attempt {attempt})")
                elif resp:
                    self.log.warning(f"  [WARN] HTTP {resp.status} (attempt {attempt})")
            except Exception as e:
                self.log.warning(f"  [ERR] {type(e).__name__}: {e} (attempt {attempt})")

            if attempt < config.MAX_RETRIES:
                backoff = config.RETRY_BACKOFF_BASE ** attempt
                self.log.info(f"  [RETRY] retrying in {backoff}s ...")
                await asyncio.sleep(backoff)

        self.log.error(f"  [ERR] Failed after {config.MAX_RETRIES} attempts: {url}")
        return False

    async def get_text(self, selector: str, default: str = "") -> str:
        """Safely extract text content from a CSS selector."""
        try:
            el = await self.page.query_selector(selector)
            if el:
                text = await el.text_content()
                return text.strip() if text else default
        except Exception:
            pass
        return default

    async def get_texts(self, selector: str) -> list[str]:
        """Extract text from all elements matching a CSS selector."""
        try:
            elements = await self.page.query_selector_all(selector)
            results = []
            for el in elements:
                text = await el.text_content()
                if text and text.strip():
                    results.append(text.strip())
            return results
        except Exception:
            return []

    async def get_attr(self, selector: str, attr: str, default: str = "") -> str:
        """Safely extract an attribute value from a CSS selector."""
        try:
            el = await self.page.query_selector(selector)
            if el:
                val = await el.get_attribute(attr)
                return val.strip() if val else default
        except Exception:
            pass
        return default

    async def get_all_attrs(self, selector: str, attr: str) -> list[str]:
        """Extract an attribute from all elements matching a selector."""
        try:
            elements = await self.page.query_selector_all(selector)
            results = []
            for el in elements:
                val = await el.get_attribute(attr)
                if val:
                    results.append(val.strip())
            return results
        except Exception:
            return []

    async def exists(self, selector: str) -> bool:
        """Check if an element exists on the page."""
        try:
            el = await self.page.query_selector(selector)
            return el is not None
        except Exception:
            return False

    async def get_page_html(self) -> str:
        """Return the full page HTML content."""
        return await self.page.content()

    def rotate_user_agent(self):
        """Switch to a new random user-agent for the next context."""
        ua = random.choice(config.USER_AGENTS)
        self.log.debug(f"  [ROT] User-Agent rotated")
        return ua
