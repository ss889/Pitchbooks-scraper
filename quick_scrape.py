"""
Quick scraper test - Scrapes a limited number of articles to see it in action.
"""

import asyncio
import logging
from scraper.news import NewsScraper
from db import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def quick_scrape(limit=3):
    """Scrape a small number of articles for testing."""
    
    print("\n" + "=" * 60)
    print("Quick Scraper Test - Limited Run")
    print("=" * 60 + "\n")
    
    try:
        # Get database stats before
        db = get_db()
        stats_before = db.get_statistics()
        logger.info(f"Database before scrape:")
        logger.info(f"  Articles: {stats_before['total_articles']}")
        logger.info(f"  Deals: {stats_before['total_deals']}")
        logger.info(f"  Companies: {stats_before['total_companies']}")
        logger.info("")
        
        # Run scraper
        logger.info(f"Starting scraper (limiting to ~{limit} search terms)...")
        scraper = NewsScraper()
        
        # Only use first 3 search terms to get limited results
        limited_terms = [
            "artificial intelligence",
            "generative AI",
            "machine learning investment"
        ]
        
        articles = await scraper.run(search_terms=limited_terms)
        
        logger.info(f"\n✓ Scraper completed!")
        logger.info(f"  Articles fetched: {len(articles)}")
        
        # Get database stats after
        stats_after = db.get_statistics()
        logger.info(f"\nDatabase after scrape:")
        logger.info(f"  Total Articles: {stats_after['total_articles']}")
        logger.info(f"  Total Deals: {stats_after['total_deals']}")
        logger.info(f"  Total Companies: {stats_after['total_companies']}")
        logger.info(f"  Average Relevance: {stats_after['avg_relevance_score']:.2f}")
        logger.info(f"  Total Funding Found: ${stats_after['total_funding_usd']:,.0f}")
        logger.info(f"  AI Categories: {stats_after['total_categories']}")
        
        # Show sample articles
        if articles:
            logger.info(f"\nSample articles scraped:")
            for i, article in enumerate(articles[:3], 1):
                logger.info(f"\n  [{i}] {article.title[:60]}...")
                logger.info(f"      Relevance: {article.ai_relevance_score:.2f}")
                logger.info(f"      Categories: {', '.join(article.categories) if article.categories else 'None'}")
                if article.deals:
                    logger.info(f"      Deals found: {len(article.deals)}")
        
        print("\n" + "=" * 60)
        print("To view data in the API, run:")
        print("  python run_service.py")
        print("\nThen visit: http://localhost:8000/docs")
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Scraper error: {str(e)}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(quick_scrape())
