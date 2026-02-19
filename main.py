"""
PitchBook AI Investing Scraper – CLI Entry Point.

Usage:
    python main.py --all              # Run all scrapers
    python main.py --companies        # Companies only
    python main.py --investors        # Investors & accelerators only
    python main.py --people           # People only
    python main.py --news             # News & deals only (stores in SQLite)
    python main.py --delay 5          # Custom min delay (seconds)
    python main.py --stats            # Show database statistics
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Add project root to sys.path to fix import errors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from models.schemas import to_json
from scraper.companies import CompanyScraper
from scraper.accelerators import AcceleratorScraper
from scraper.people import PeopleScraper
from scraper.news import NewsScraper
from viewer import open_dashboard
from db import get_db


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)


async def scrape_companies():
    """Run the company scraper."""
    async with CompanyScraper() as scraper:
        companies = await scraper.run()
        if companies:
            to_json(companies, os.path.join(config.OUTPUT_DIR, "companies.json"))
        return companies


async def scrape_investors():
    """Run the investor/accelerator scraper."""
    async with AcceleratorScraper() as scraper:
        investors = await scraper.run()
        if investors:
            to_json(investors, os.path.join(config.OUTPUT_DIR, "investors.json"))
        return investors


async def scrape_people():
    """Run the people scraper."""
    async with PeopleScraper() as scraper:
        people = await scraper.run()
        if people:
            to_json(people, os.path.join(config.OUTPUT_DIR, "people.json"))
        return people


async def scrape_news():
    """Run the news/deals scraper (stores in SQLite)."""
    async with NewsScraper() as scraper:
        articles = await scraper.run()
        return articles


def show_database_stats():
    """Display database statistics."""
    db = get_db()
    stats = db.get_statistics()
    
    print("\n" + "=" * 60)
    print("  AI News Intelligence Database Statistics")
    print("=" * 60)
    print(f"  Total Articles:        {stats['total_articles']:>6}")
    print(f"  Total Deals:           {stats['total_deals']:>6}")
    print(f"  Total Companies:       {stats['total_companies']:>6}")
    print(f"  Total Investors:       {stats['total_investors']:>6}")
    print(f"  Total Funding (USD):   ${stats['total_funding_usd']:>15,.0f}")
    print(f"  Avg Relevance Score:   {stats['avg_relevance_score']:>6.2f}")
    print("=" * 60 + "\n")


async def scrape_all():
    """Run all scrapers sequentially (to share rate limits)."""
    print("\n" + "=" * 60)
    print("  PitchBook AI Investing Scraper")
    print("=" * 60)

    # Type annotation to help linter
    results: dict[str, Any] = {}

    print("\n> [1/4] Scraping AI Companies ...")
    companies = await scrape_companies()
    results["companies"] = companies or []

    print("\n> [2/4] Scraping Investors & Accelerators ...")
    investors = await scrape_investors()
    results["investors"] = investors or []

    print("\n> [3/4] Scraping Key People ...")
    people = await scrape_people()
    results["people"] = people or []

    print("\n> [4/4] Scraping News & Deals ...")
    news = await scrape_news()
    results["news"] = news or []

    # Print summary
    print("\n" + "=" * 60)
    print("  Scraping Complete!")
    print("=" * 60)
    print(f"  Companies:    {len(results['companies'])}")
    print(f"  Investors:    {len(results['investors'])}")
    print(f"  People:       {len(results['people'])}")
    print(f"  Articles:     {len(results['news'])}")
    print(f"  Output dir:   {os.path.abspath(config.OUTPUT_DIR)}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="PitchBook AI Investing Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --all                   Run all scrapers
  python main.py --companies --investors Run companies + investors
  python main.py --news --delay 5        News with 5s min delay
  python main.py --stats                 Show database statistics
        """,
    )

    parser.add_argument("--all", action="store_true", help="Run all scrapers")
    parser.add_argument("--companies", action="store_true", help="Scrape AI company profiles")
    parser.add_argument("--investors", action="store_true", help="Scrape investors & accelerators")
    parser.add_argument("--people", action="store_true", help="Scrape key people")
    parser.add_argument("--news", action="store_true", help="Scrape news articles & deals (stores in SQLite)")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--view", action="store_true", help="Open the dashboard to view scraped data")
    parser.add_argument("--delay", type=float, default=None, help="Minimum delay between requests (seconds)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory path")
    parser.add_argument("--max-pages", type=int, default=None, help="Max search pages per term")

    args = parser.parse_args()

    # Apply overrides
    if args.delay is not None:
        config.MIN_DELAY_SECONDS = args.delay
        config.MAX_DELAY_SECONDS = args.delay + 3
    if args.output_dir:
        config.OUTPUT_DIR = args.output_dir
    if args.max_pages:
        config.MAX_SEARCH_PAGES = args.max_pages

    ensure_output_dir()

    # If --stats only, show stats and exit
    if args.stats and not any([args.all, args.companies, args.investors, args.people, args.news, args.view]):
        show_database_stats()
        return

    # If --view only, just open the dashboard
    if args.view and not any([args.all, args.companies, args.investors, args.people, args.news]):
        open_dashboard()
        # Show stats too
        show_database_stats()
        return

    # Default to --all if nothing specified
    if not any([args.all, args.companies, args.investors, args.people, args.news]):
        args.all = True

    if args.all:
        asyncio.run(scrape_all())
    else:
        async def run_selected():
            if args.companies:
                print("\n> Scraping AI Companies ...")
                await scrape_companies()
            if args.investors:
                print("\n> Scraping Investors & Accelerators ...")
                await scrape_investors()
            if args.people:
                print("\n> Scraping Key People ...")
                await scrape_people()
            if args.news:
                print("\n> Scraping News & Deals ...")
                await scrape_news()
            print("\n[OK] Done! Output saved to:", os.path.abspath(config.OUTPUT_DIR))

        asyncio.run(run_selected())

    # Show stats after scraping
    show_database_stats()

    # Open dashboard after scraping if --view was passed
    if args.view:
        open_dashboard()


if __name__ == "__main__":
    main()
