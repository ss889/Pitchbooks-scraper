"""Check for duplicates in database."""
from db import get_db

db = get_db()
stats = db.get_statistics()
print(f"\nTotal articles in DB: {stats['total_articles']}\n")

articles = db.get_articles(limit=100)
print("Article titles and URLs:")
print("=" * 80)

seen = set()
duplicates = []

for i, article in enumerate(articles, 1):
    title = article['title']
    url = article['url']
    
    if title in seen:
        duplicates.append(title)
    seen.add(title)
    
    print(f"{i}. {title}")
    print(f"   URL: {url}\n")

if duplicates:
    print(f"\n⚠️  FOUND {len(duplicates)} DUPLICATE TITLES:")
    for dup in duplicates:
        print(f"   - {dup}")
else:
    print("\n✓ No duplicate titles found")
