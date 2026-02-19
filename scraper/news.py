"""
News & Deals scraper.

Scrapes PitchBook's publicly available news articles about AI investing
to extract deal data, funding trends, and market intelligence.

Now integrates with SQLite database to avoid duplicates and provides
intelligent AI-focused extraction for reporters.
"""

import sys
from pathlib import Path
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from models.schemas import NewsArticle, DealInfo
from scraper.base import BaseScraper
from scraper.ai_parser import AINewsParser
from db import get_db


NEWS_AI_TERMS = [
    "artificial intelligence",
    "AI startup funding",
    "generative AI deal",
    "machine learning investment",
    "AI venture capital",
    "AI acquisition",
    "LLM funding round",
]


class NewsScraper(BaseScraper):
    """Scrape AI investing news articles from PitchBook's public news section."""
    
    def __init__(self):
        super().__init__()
        self.db = get_db()
        self.parser = AINewsParser()

    async def run(self, search_terms: list[str] | None = None) -> list[NewsArticle]:
        """
        Scrape AI-related news articles from PitchBook.
        Returns a list of NewsArticle records.
        """
        # Initialize browser context
        async with self:
            terms = search_terms or NEWS_AI_TERMS
            all_articles: list[NewsArticle] = []
            inserted_count = 0

            # Strategy 1: Browse the main news/articles section
            self.log.info("[NEWS] Browsing PitchBook news section ...")
            listing_articles = await self._browse_news_listings()
            for article in listing_articles:
                if self._process_article(article):
                    all_articles.append(article)
                    inserted_count += 1

            # Strategy 2: Search for specific AI terms
            for term in terms:
                self.log.info(f"[SEARCH] Searching news: \"{term}\"")
                articles = await self._search_news(term)
                for article in articles:
                    if self._process_article(article):
                        all_articles.append(article)
                        inserted_count += 1

            self.log.info(f"[TOTAL] Total articles scraped: {len(all_articles)} ({inserted_count} new)")
            return all_articles
    
    def _process_article(self, article: NewsArticle) -> bool:
        """
        Process article: parse it with AI parser and insert into database if new.
        Returns True if article was inserted, False if duplicate.
        """
        # Check if already exists
        if self.db.article_exists(article.url):
            self.log.debug(f"  [DUP] {article.title[:60]}")
            return False
        
        # Parse with AI parser
        parsed = self.parser.parse_article(article.title, article.full_text, article.url)
        
        # Insert into database
        article_id = self.db.insert_article(
            url=article.url,
            title=article.title,
            summary=parsed.get('summary', article.summary),
            content=article.full_text,
            published_date=article.date,
            ai_relevance_score=parsed.get('ai_relevance_score', 0.0),
            is_deal_news=int(parsed.get('is_deal_news', False))
        )
        
        if not article_id:
            self.log.warning(f"  Failed to insert: {article.title[:60]}")
            return False
        
        # Add categories
        for category in parsed.get('ai_categories', []):
            self.db.add_article_category(article_id, category)
        
        # Insert deals if any
        for deal in parsed.get('deals', []):
            self.db.insert_deal(
                article_id=article_id,
                company_name=deal.get('company'),
                funding_amount=deal.get('amount_usd'),
                round_type=deal.get('round_type'),
                investors=', '.join(deal.get('investors', [])) if deal.get('investors') else None,
                announcement_date=deal.get('date')
            )
        
        relevance = parsed.get('ai_relevance_score', 0)
        self.log.info(f"  [OK] {article.title[:60]} (relevance: {relevance:.2f})")
        return True

    async def _browse_news_listings(self) -> list[NewsArticle]:
        """Browse the main news listing pages."""
        articles = []

        for page_num in range(1, config.MAX_ARTICLES_PAGES + 1):
            url = f"{config.ARTICLES_URL}?page={page_num}"
            success = await self.goto(url)
            if not success:
                break

            html = await self.get_page_html()
            soup = BeautifulSoup(html, "lxml")

            # Find article links
            article_links = self._find_article_links(soup)
            if not article_links:
                self.log.info(f"  No more articles on page {page_num}")
                break

            self.log.info(f"  Found {len(article_links)} articles on page {page_num}")

            # Filter for AI-related articles and scrape them
            for link, title in article_links:
                if self._is_ai_related(title):
                    article = await self._scrape_article(link)
                    if article:
                        articles.append(article)

        return articles

    async def _search_news(self, term: str) -> list[NewsArticle]:
        """Search for news articles by term."""
        articles = []

        for page_num in range(1, config.MAX_SEARCH_PAGES + 1):
            url = f"{config.SEARCH_URL}?q={quote_plus(term)}&type=news&page={page_num}"
            success = await self.goto(url)
            if not success:
                break

            html = await self.get_page_html()
            soup = BeautifulSoup(html, "lxml")

            article_links = self._find_article_links(soup)
            if not article_links:
                break

            for link, title in article_links:
                article = await self._scrape_article(link)
                if article:
                    articles.append(article)

        return articles

    async def _scrape_article(self, url: str) -> NewsArticle | None:
        """Scrape a single news article page."""
        success = await self.goto(url)
        if not success:
            return None

        html = await self.get_page_html()
        soup = BeautifulSoup(html, "lxml")

        article = NewsArticle(url=url)

        # ── Title ────────────────────────────────────────────────────
        article.title = self._extract_text(soup, [
            "h1", "article h1", ".article-title", ".post-title",
            "[data-test='article-title']"
        ])

        # ── Date ─────────────────────────────────────────────────────
        article.date = self._extract_text(soup, [
            "time", ".article-date", ".publish-date", ".post-date",
            "[data-test='publish-date']", "[datetime]"
        ])
        # Also try datetime attribute
        time_el = soup.find("time")
        if time_el and time_el.get("datetime"):
            article.date = time_el["datetime"]

        # ── Author ───────────────────────────────────────────────────
        article.author = self._extract_text(soup, [
            ".author-name", ".article-author", "[data-test='author']",
            ".byline a", ".byline"
        ])

        # ── Body text ────────────────────────────────────────────────
        body_selectors = [
            "article", ".article-body", ".article-content",
            ".post-content", ".entry-content", "[data-test='article-body']"
        ]
        for sel in body_selectors:
            el = soup.select_one(sel)
            if el:
                # Get all paragraph text
                paragraphs = el.find_all("p")
                if paragraphs:
                    article.full_text = "\n\n".join(
                        p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
                    )
                    # First paragraph as summary
                    article.summary = paragraphs[0].get_text(strip=True) if paragraphs else ""
                    break

        if not article.full_text:
            # Fallback: grab all paragraph text
            all_p = soup.find_all("p")
            texts = [p.get_text(strip=True) for p in all_p if p.get_text(strip=True)]
            article.full_text = "\n\n".join(texts[:30])  # Cap at 30 paragraphs
            article.summary = texts[0] if texts else ""

        # ── Tags / Categories ────────────────────────────────────────
        article.tags = self._extract_tags(soup)

        # ── Companies mentioned ──────────────────────────────────────
        article.companies_mentioned = self._extract_mentioned_companies(soup)

        # ── Deal info ────────────────────────────────────────────────
        article.deal_info = self._extract_deal_info(article.full_text, article.title)

        return article

    def _find_article_links(self, soup: BeautifulSoup) -> list[tuple[str, str]]:
        """Find article links and their titles from a listing page."""
        results = []
        seen = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/news/articles/" in href or "/news/reports/" in href:
                full_url = href if href.startswith("http") else f"{config.BASE_URL}{href}"
                if full_url not in seen:
                    seen.add(full_url)
                    title = a.get_text(strip=True)
                    results.append((full_url, title))

        return results

    def _is_ai_related(self, text: str) -> bool:
        """Check if text is AI-related."""
        text_lower = text.lower()
        ai_keywords = [
            "artificial intelligence", "ai ", " ai", "machine learning",
            "deep learning", "generative ai", "llm", "gpt", "neural",
            "computer vision", "nlp", "natural language", "chatbot",
            "autonomous", "robotics", "ai-", "openai", "anthropic",
            "ml ", " ml", "agentic"
        ]
        return any(kw in text_lower for kw in ai_keywords)

    def _extract_tags(self, soup: BeautifulSoup) -> list[str]:
        """Extract tags/categories from an article."""
        tags = []
        tag_selectors = [
            ".tags a", ".article-tags a", ".categories a",
            "[data-test='tags'] a", ".topic-tag", ".tag-list a"
        ]
        for sel in tag_selectors:
            elements = soup.select(sel)
            for el in elements:
                tag = el.get_text(strip=True)
                if tag and tag not in tags:
                    tags.append(tag)

        return tags

    def _extract_mentioned_companies(self, soup: BeautifulSoup) -> list[str]:
        """Extract company names mentioned in the article."""
        companies = []
        # Look for links to company profiles
        for a in soup.find_all("a", href=True):
            if "/profiles/company/" in a["href"]:
                name = a.get_text(strip=True)
                if name and name not in companies:
                    companies.append(name)
        return companies

    def _extract_deal_info(self, text: str, title: str) -> DealInfo | None:
        """
        Try to extract deal/funding information from article text.
        Looks for patterns like "$X million/billion", "Series A/B/C", etc.
        """
        import re

        combined = f"{title} {text}"

        # Look for funding amounts
        amount_pattern = r'\$[\d,.]+\s*(?:million|billion|M|B|mn|bn)'
        amounts = re.findall(amount_pattern, combined, re.IGNORECASE)

        # Look for round types
        round_pattern = r'(?:Series\s+[A-Z][\+]*|Seed|Pre-Seed|Series\s+\w+|Growth|Bridge|IPO|SPAC|acquisition)'
        rounds = re.findall(round_pattern, combined, re.IGNORECASE)

        if amounts or rounds:
            deal = DealInfo()
            deal.amount = amounts[0] if amounts else ""
            deal.round_type = rounds[0] if rounds else ""
            return deal

        return None

    def _extract_text(self, soup: BeautifulSoup, selectors: list[str]) -> str:
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return ""
