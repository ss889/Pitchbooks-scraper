"""Check current articles in database."""
from db import get_db

db = get_db()
articles = db.get_articles(limit=50)
stats = db.get_statistics()

print(f"=== Database Status ===")
print(f"Total articles: {stats.get('total_articles', 0)}")
print(f"Total deals: {stats.get('total_deals', 0)}")
print(f"\n=== Articles ===")
for a in articles:
    print(f"ID {a['id']}: {a['url']}")
    print(f"   Title: {a['title'][:60]}...")
    print(f"   Relevance: {a['ai_relevance_score']}")
    print()
