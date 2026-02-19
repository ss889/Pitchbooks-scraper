"""Delete only the broken PitchBook URLs, keeping the good ones."""
from db import get_db

db = get_db()

# URLs to delete (the broken ones)
broken_urls = [
    "https://pitchbook.com/news/articles/openai-series-c",
    "https://pitchbook.com/news/articles/anthropic-5b-funding",
    "https://pitchbook.com/news/articles/stability-ai-series-a",
    "https://pitchbook.com/news/articles/deepmind-alphafold3",
    "https://pitchbook.com/news/articles/tesla-ai-chip",
    "https://pitchbook.com/news/articles/pitchbook-private-capital-return-barometers",
    "https://pitchbook.com/news/reports/q4-2025-pitchbook-nvca-venture-monitor",
    "https://pitchbook.com/news/articles/the-pitchbook-vc-dealmaking-indicator",
    "https://pitchbook.com/news/reports/q4-2025-allocator-solutions-are-private-markets-worth-it",
    "https://pitchbook.com/news/articles/buyout-replication-portfolio",
    "https://pitchbook.com/news/articles/pitchbook-private-market-indexes",
]

with db.get_connection() as conn:
    cursor = conn.cursor()
    
    for url in broken_urls:
        # Get article ID
        cursor.execute("SELECT id FROM news_articles WHERE url = ?", (url,))
        result = cursor.fetchone()
        
        if result:
            article_id = result[0]
            # Delete related records
            cursor.execute("DELETE FROM article_categories WHERE article_id = ?", (article_id,))
            cursor.execute("DELETE FROM article_mentions WHERE article_id = ?", (article_id,))
            cursor.execute("DELETE FROM deals WHERE article_id = ?", (article_id,))
            cursor.execute("DELETE FROM news_articles WHERE id = ?", (article_id,))
            print(f"✓ Deleted: {url}")
    
    conn.commit()

# Check stats
stats = db.get_statistics()
print(f"\nDatabase cleaned!")
print(f"Articles remaining: {stats['total_articles']}")
print(f"Deals remaining: {stats['total_deals']}")
