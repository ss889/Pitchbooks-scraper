"""
Validate and update URL status for all articles in the database.

This script ensures every article has a verified, working link.
For newsletter creators: no more broken links in your content.

Usage:
    python validate_urls.py [--fix] [--limit N]
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from db import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


async def validate_url(url: str, timeout: int = 10) -> str:
    """Check if URL is accessible and return status."""
    import aiohttp
    
    if not url or not url.startswith(('http://', 'https://')):
        return 'inaccessible'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            ) as response:
                if response.status == 200:
                    return 'accessible'
                elif response.status in (401, 402, 403):
                    return 'preview_only'
                else:
                    return 'inaccessible'
    except asyncio.TimeoutError:
        return 'inaccessible'
    except Exception:
        return 'inaccessible'


async def validate_all_urls(fix: bool = False, limit: int = None):
    """Validate all article URLs and optionally update status."""
    db = get_db()
    
    # Get all articles
    articles = db.get_articles(limit=limit or 1000, min_relevance=0.0)
    
    print(f"\n{'='*60}")
    print(f"URL Validation Report")
    print(f"{'='*60}")
    print(f"Total articles to check: {len(articles)}")
    print()
    
    results = {
        'accessible': [],
        'preview_only': [],
        'inaccessible': [],
    }
    
    for article in articles:
        url = article['url']
        title = article['title'][:50]
        article_id = article['id']
        
        status = await validate_url(url)
        results[status].append({
            'id': article_id,
            'url': url,
            'title': title
        })
        
        # Print status
        icon = {'accessible': '✓', 'preview_only': '⚠', 'inaccessible': '✗'}[status]
        print(f"  {icon} [{status:12}] {title}")
        
        # Update database if fix mode
        if fix:
            db.update_url_status(article_id, status)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary")
    print(f"{'='*60}")
    print(f"  ✓ Accessible:    {len(results['accessible'])}")
    print(f"  ⚠ Preview Only:  {len(results['preview_only'])}")
    print(f"  ✗ Inaccessible:  {len(results['inaccessible'])}")
    
    if results['inaccessible']:
        print(f"\n{'='*60}")
        print(f"Broken URLs (need attention)")
        print(f"{'='*60}")
        for item in results['inaccessible']:
            print(f"  ID {item['id']}: {item['url']}")
    
    if fix:
        print(f"\n✓ Database updated with URL status")
    else:
        print(f"\nRun with --fix to update database")
    
    return results


def remove_broken_articles():
    """Remove articles with inaccessible URLs from database."""
    db = get_db()
    
    # Get inaccessible articles
    broken = db.get_articles_by_url_status('inaccessible', limit=1000)
    
    if not broken:
        print("No broken articles to remove.")
        return
    
    print(f"\nRemoving {len(broken)} broken articles...")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        for article in broken:
            article_id = article['id']
            # Delete related records
            cursor.execute("DELETE FROM article_categories WHERE article_id = ?", (article_id,))
            cursor.execute("DELETE FROM article_mentions WHERE article_id = ?", (article_id,))
            cursor.execute("DELETE FROM deals WHERE article_id = ?", (article_id,))
            cursor.execute("DELETE FROM news_articles WHERE id = ?", (article_id,))
            print(f"  Deleted: {article['title'][:50]}")
        
        conn.commit()
    
    print(f"\n✓ Removed {len(broken)} broken articles")


def main():
    parser = argparse.ArgumentParser(
        description="Validate article URLs in database"
    )
    parser.add_argument(
        '--fix', 
        action='store_true',
        help="Update URL status in database"
    )
    parser.add_argument(
        '--remove-broken',
        action='store_true', 
        help="Remove articles with broken URLs"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help="Limit number of articles to check"
    )
    
    args = parser.parse_args()
    
    if args.remove_broken:
        # First validate, then remove
        asyncio.run(validate_all_urls(fix=True, limit=args.limit))
        remove_broken_articles()
    else:
        asyncio.run(validate_all_urls(fix=args.fix, limit=args.limit))


if __name__ == "__main__":
    main()
