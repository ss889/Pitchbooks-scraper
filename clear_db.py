"""Delete all articles from database to start fresh."""
import sqlite3
import os

db_path = "pitchbooks.db"

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Delete all data from tables
        cursor.execute("DELETE FROM article_categories")
        cursor.execute("DELETE FROM deals")
        cursor.execute("DELETE FROM news_articles")
        cursor.execute("DELETE FROM ai_categories")
        cursor.execute("DELETE FROM companies")
        cursor.execute("DELETE FROM investors")
        cursor.execute("DELETE FROM article_mentions")
        
        conn.commit()
        conn.close()
        
        print("✓ All data cleared from database")
    except Exception as e:
        print(f"Error clearing database: {e}")
else:
    print(f"Database not found at {db_path}")
