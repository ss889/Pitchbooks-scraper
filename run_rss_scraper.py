"""
Run RSS scraper to populate database with real, accessible articles.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)

from src.scrapers.rss_scraper import RSSNewsScraper
from db import get_db


async def main():
    print("=" * 60)
    print("RSS Scraper - Fetching Real AI News")
    print("=" * 60)
    
    scraper = RSSNewsScraper()
    articles = await scraper.run(max_per_source=15)
    
    print("\n" + "=" * 60)
    print("Scrape Complete")
    print("=" * 60)
    print(f"New articles inserted: {len(articles)}")
    
    # Show database stats
    db = get_db()
    stats = db.get_statistics()
    print(f"\nDatabase Status:")
    print(f"  Total articles: {stats['total_articles']}")
    print(f"  Total deals: {stats['total_deals']}")
    
    # Show sample articles
    if articles:
        print(f"\nSample new articles:")
        for a in articles[:5]:
            print(f"  - {a['title'][:60]}...")
            print(f"    Source: {a['source']} | Status: {a['url_status']}")


if __name__ == "__main__":
    asyncio.run(main())
