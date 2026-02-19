"""
APScheduler-based task scheduler for PitchBooks scraper.

Runs the AI news scraper daily to fetch and store new articles.
Uses a multi-source strategy:
1. Primary: PitchBook scraper (when accessible)
2. Fallback: RSS feeds (always accessible)

For newsletter creators: This ensures you always have fresh,
verified content every day, regardless of any single source's
availability.
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job

# Configure logging
LOG_FILE = Path(__file__).parent / "scraper.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Scrape results file for health monitoring
HEALTH_FILE = Path(__file__).parent / "scrape_health.json"


def save_scrape_result(result: Dict[str, Any]):
    """Save scrape result for health monitoring."""
    try:
        result['timestamp'] = datetime.now().isoformat()
        with open(HEALTH_FILE, 'w') as f:
            json.dump(result, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save health data: {e}")


def get_last_scrape_result() -> Optional[Dict[str, Any]]:
    """Get last scrape result for health check."""
    try:
        if HEALTH_FILE.exists():
            with open(HEALTH_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def run_scraper():
    """
    Execute all scrapers and log results.
    
    Strategy:
    1. Try PitchBook scraper first (primary source)
    2. Always run RSS scraper (reliable fallback)
    3. Validate all new URLs
    4. Generate summary
    """
    result = {
        'success': True,
        'articles_total': 0,
        'articles_by_source': {},
        'errors': [],
        'started_at': datetime.now().isoformat(),
    }
    
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled scraper run")
        logger.info(f"Time: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        import asyncio
        
        # Strategy 1: Try PitchBook scraper (may fail)
        pitchbook_count = 0
        try:
            logger.info("\n[1/3] Running PitchBook scraper...")
            from scraper.news import NewsScraper
            
            pb_scraper = NewsScraper()
            pb_articles = asyncio.run(pb_scraper.run())
            pitchbook_count = len(pb_articles) if pb_articles else 0
            logger.info(f"  PitchBook: {pitchbook_count} articles")
            result['articles_by_source']['pitchbook'] = pitchbook_count
            
        except Exception as e:
            logger.warning(f"  PitchBook scraper failed: {e}")
            result['errors'].append(f"PitchBook: {str(e)}")
            result['articles_by_source']['pitchbook'] = 0
        
        # Strategy 2: Run RSS scraper (always reliable)
        rss_count = 0
        try:
            logger.info("\n[2/3] Running RSS scraper...")
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from scrapers.rss_scraper import RSSNewsScraper
            
            rss_scraper = RSSNewsScraper()
            rss_articles = asyncio.run(rss_scraper.run(max_per_source=20))
            rss_count = len(rss_articles) if rss_articles else 0
            logger.info(f"  RSS feeds: {rss_count} articles")
            result['articles_by_source']['rss'] = rss_count
            
        except Exception as e:
            logger.error(f"  RSS scraper failed: {e}")
            result['errors'].append(f"RSS: {str(e)}")
            result['articles_by_source']['rss'] = 0
        
        # Strategy 3: Validate URLs for new articles
        logger.info("\n[3/3] Validating article URLs...")
        try:
            from db import get_db
            db = get_db()
            unchecked = db.get_unchecked_articles(limit=50)
            
            if unchecked:
                # Import validation
                sys.path.insert(0, str(Path(__file__).parent / "src"))
                from utils.url_validator import validate_url_sync, URLStatus
                
                validated = 0
                for article in unchecked:
                    status, _, _ = validate_url_sync(article['url'])
                    db.update_url_status(article['id'], status.value)
                    validated += 1
                
                logger.info(f"  Validated {validated} URLs")
                result['urls_validated'] = validated
            else:
                logger.info("  No URLs need validation")
                result['urls_validated'] = 0
                
        except Exception as e:
            logger.error(f"  URL validation failed: {e}")
            result['errors'].append(f"Validation: {str(e)}")
        
        # Summary
        total = pitchbook_count + rss_count
        result['articles_total'] = total
        result['completed_at'] = datetime.now().isoformat()
        
        logger.info("\n" + "=" * 60)
        logger.info("Daily Scrape Summary")
        logger.info("=" * 60)
        logger.info(f"  Total new articles: {total}")
        logger.info(f"    - PitchBook: {pitchbook_count}")
        logger.info(f"    - RSS feeds: {rss_count}")
        
        if result['errors']:
            logger.warning(f"  Errors encountered: {len(result['errors'])}")
            result['success'] = False
        else:
            logger.info("  ✓ All sources scraped successfully")
        
        logger.info("=" * 60)
        
        # Get database stats
        try:
            from db import get_db
            stats = get_db().get_statistics()
            result['database_stats'] = stats
            logger.info(f"\nDatabase totals:")
            logger.info(f"  Articles: {stats['total_articles']}")
            logger.info(f"  Deals: {stats['total_deals']}")
        except Exception:
            pass
        
    except Exception as e:
        logger.error(f"✗ Critical scraper error: {str(e)}", exc_info=True)
        result['success'] = False
        result['errors'].append(f"Critical: {str(e)}")
    
    # Save result for health monitoring
    save_scrape_result(result)
    
    return result


class ScraperScheduler:
    """
    Wrapper class for APScheduler managing scraper tasks.
    
    For newsletter creators: This ensures your data pipeline
    runs reliably every day at 2 AM, with automatic fallbacks
    and health monitoring.
    """
    
    def __init__(self, scrape_hour: int = 2, scrape_minute: int = 0):
        """
        Initialize the scheduler.
        
        Args:
            scrape_hour: Hour to run daily scrape (0-23, default 2 AM)
            scrape_minute: Minute to run daily scrape (0-59, default 0)
        """
        self.scheduler = BackgroundScheduler()
        self.job: Job | None = None
        self.scrape_hour = scrape_hour
        self.scrape_minute = scrape_minute
        
    def start(self):
        """Start the scheduler with daily job."""
        try:
            if self.scheduler.running:
                logger.warning("Scheduler is already running")
                return
            
            # Schedule job to run daily
            self.job = self.scheduler.add_job(
                run_scraper,
                CronTrigger(hour=self.scrape_hour, minute=self.scrape_minute),
                id='daily_scraper',
                name='Daily AI News Scraper',
                replace_existing=True,
                max_instances=1  # Prevent concurrent runs
            )
            
            self.scheduler.start()
            logger.info(f"✓ Scheduler started - Daily scraper scheduled for {self.scrape_hour:02d}:{self.scrape_minute:02d}")
            logger.info(f"  Next run: {self.job.next_run_time}")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)
            raise
    
    def stop(self):
        """Stop the scheduler gracefully."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("✓ Scheduler stopped")
            else:
                logger.warning("Scheduler is not running")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}", exc_info=True)
    
    def run_now(self) -> Dict[str, Any]:
        """
        Manually trigger scraper immediately (for testing).
        
        Returns:
            Scrape result dictionary
        """
        logger.info("Manual scraper trigger requested")
        result = run_scraper()
        
        if self.job:
            logger.info(f"Next scheduled run: {self.job.next_run_time}")
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status for health monitoring."""
        status = {
            'running': self.scheduler.running,
            'next_run': str(self.job.next_run_time) if self.job else None,
            'last_result': get_last_scrape_result(),
        }
        return status
    
    @property
    def is_healthy(self) -> bool:
        """Check if scheduler is healthy."""
        if not self.scheduler.running:
            return False
        
        last_result = get_last_scrape_result()
        if last_result:
            return last_result.get('success', False)
        
        return True


# Global scheduler instance
_scheduler_instance: ScraperScheduler | None = None


def get_scheduler() -> ScraperScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ScraperScheduler()
    return _scheduler_instance


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="PitchBook Scraper Scheduler")
    parser.add_argument('--run-now', action='store_true', help="Run scraper immediately")
    parser.add_argument('--status', action='store_true', help="Show scheduler status")
    parser.add_argument('--hour', type=int, default=2, help="Hour for daily scrape (0-23)")
    parser.add_argument('--minute', type=int, default=0, help="Minute for daily scrape (0-59)")
    
    args = parser.parse_args()
    
    if args.run_now:
        logger.info("Running scraper immediately...")
        result = run_scraper()
        print(json.dumps(result, indent=2))
    elif args.status:
        scheduler = get_scheduler()
        status = scheduler.get_status()
        print(json.dumps(status, indent=2))
    else:
        logger.info("Starting scheduler in standalone mode...")
        scheduler = ScraperScheduler(scrape_hour=args.hour, scrape_minute=args.minute)
        scheduler.start()
        
        try:
            logger.info("Scheduler running. Press Ctrl+C to stop.")
            import time
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            scheduler.stop()
