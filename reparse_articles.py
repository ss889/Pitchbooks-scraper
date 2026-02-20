"""Re-parse existing articles with improved AI parser."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from db import get_db

# Force reimport of the parser module
import importlib
import scraper.ai_parser
importlib.reload(scraper.ai_parser)

def main():
    db = get_db()
    parser = scraper.ai_parser.AINewsParser()
    
    # Get all articles
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content, summary FROM news_articles")
        articles = cursor.fetchall()
    
    print(f"Re-parsing {len(articles)} articles...")
    
    deals_added = 0
    for i, article in enumerate(articles):
        article_id, title, content, summary = article
        full_content = f"{summary or ''}\n{content or ''}"
        
        # Parse with improved AI parser
        result = parser.parse_article(title, full_content)
        
        if result and 'deals' in result and result['deals']:
            for deal in result['deals']:
                company = deal.get('company', '')
                amount_text = deal.get('amount_text', '')
                amount_val = deal.get('amount_usd', 0)  # Use amount_usd not amount
                investors_list = deal.get('investors', [])
                round_type = deal.get('round_type', '')
                
                # Skip if no company name extracted
                if not company or len(company) < 3:
                    continue
                
                # Insert deal
                try:
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT OR REPLACE INTO deals 
                            (article_id, company_name, funding_amount, round_type, investors)
                            VALUES (?, ?, ?, ?, ?)
                        """, (article_id, company, amount_val or 0, round_type, ', '.join(investors_list) if investors_list else ''))
                    deals_added += 1
                    print(f"  ✓ {company}: {amount_text} ({round_type})")
                except Exception as e:
                    print(f"  ✗ Error: {e}")
    
    print(f"\nDone. Added {deals_added} deals.")
    
    # Show stats
    stats = db.get_statistics()
    print(f"\nDatabase Status:")
    print(f"  Total articles: {stats['total_articles']}")
    print(f"  Total deals: {stats['total_deals']}")

if __name__ == "__main__":
    main()
