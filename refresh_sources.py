"""Remove TechCrunch articles and re-scrape with new sources."""
import sqlite3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from db import get_db
from src.scrapers.rss_scraper import RSSNewsScraper

def main():
    # Delete TechCrunch articles
    conn = sqlite3.connect('ai_news.db')
    c = conn.cursor()
    c.execute("DELETE FROM news_articles WHERE source LIKE '%techcrunch%'")
    deleted = c.rowcount
    conn.commit()
    conn.close()
    print(f"Deleted {deleted} TechCrunch articles")
    
    # Also clear deals to re-extract
    conn = sqlite3.connect('ai_news.db')
    conn.execute("DELETE FROM deals")
    conn.commit()
    conn.close()
    print("Cleared deals table")
    
    # Re-scrape with new sources
    print("\nScraping new sources...")
    scraper = RSSNewsScraper()
    articles = asyncio.run(scraper.run(max_per_source=15))
    print(f"Added {len(articles)} articles from new sources")
    
    # Show source breakdown
    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT source, COUNT(*) FROM news_articles GROUP BY source ORDER BY COUNT(*) DESC")
        print("\nArticles by source:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    main()
