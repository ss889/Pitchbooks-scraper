#!/usr/bin/env python3
"""Test API and Database Integration"""

try:
    from api import app
    print("✓ FastAPI app loaded successfully")
    print(f"✓ App has {len(app.routes)} routes")
except Exception as e:
    print(f"✗ Error loading API: {e}")
    exit(1)

try:
    from db import get_db
    db = get_db()
    print("✓ Database connected successfully")
except Exception as e:
    print(f"✗ Error connecting to database: {e}")
    exit(1)

try:
    stats = db.get_statistics()
    print(f"✓ Database functional")
    print(f"  - {stats['total_articles']} articles")
    print(f"  - {stats['total_deals']} deals")
    print(f"  - {stats['total_categories']} categories")
except Exception as e:
    print(f"✗ Error getting statistics: {e}")
    exit(1)

try:
    categories = db.get_categories()
    print(f"✓ {len(categories)} AI categories loaded")
except Exception as e:
    print(f"✗ Error getting categories: {e}")
    exit(1)

print("\n" + "=" * 60)
print("API is ready! Start with:")
print("=" * 60)
print("\n  python -m uvicorn api:app --reload --port 8000\n")
print("Then visit: http://localhost:8000/docs\n")
