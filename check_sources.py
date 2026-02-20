from db import get_db
import sqlite3

db = get_db()
conn = sqlite3.connect(db.db_path)
c = conn.cursor()

# Get source breakdown
c.execute('SELECT source, COUNT(*) as cnt FROM news_articles GROUP BY source ORDER BY cnt DESC')
print("=== Articles by Source ===")
for row in c.fetchall():
    print(f"  {row[0] or 'unknown'}: {row[1]}")

# Get stats
stats = db.get_statistics()
print(f"\n=== Statistics ===")
print(f"  Total articles: {stats['total_articles']}")
print(f"  Total deals: {stats['total_deals']}")
print(f"  Total funding: ${stats['total_funding_usd']:,.0f}")

# Get recent from new sources
c.execute("SELECT source, title FROM news_articles WHERE source IN ('cbinsights', 'google_news_ai_funding', 'yahoo_finance') ORDER BY scraped_date DESC LIMIT 5")
print(f"\n=== Recent from New Sources ===")
for row in c.fetchall():
    print(f"  [{row[0]}] {row[1][:60]}...")
