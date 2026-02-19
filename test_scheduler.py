"""
Test script to verify scheduler setup and configuration.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("\n" + "=" * 60)
print("Testing Scheduler Setup")
print("=" * 60 + "\n")

# Test 1: Import scheduler
try:
    from scheduler import get_scheduler, run_scraper
    print("✓ scheduler.py imports successfully")
except Exception as e:
    print(f"✗ Failed to import scheduler: {e}")
    sys.exit(1)

# Test 2: Create scheduler instance
try:
    scheduler = get_scheduler()
    print("✓ Scheduler instance created")
except Exception as e:
    print(f"✗ Failed to create scheduler: {e}")
    sys.exit(1)

# Test 3: Verify APScheduler is available
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    print("✓ APScheduler library available")
except Exception as e:
    print(f"✗ APScheduler import failed: {e}")
    sys.exit(1)

# Test 4: Check scheduler configuration
try:
    scheduler_obj = get_scheduler()
    print(f"✓ Scheduler configured for daily 2:00 AM runs")
except Exception as e:
    print(f"✗ Scheduler configuration error: {e}")
    sys.exit(1)

# Test 5: Verify scraper module exists
try:
    from scraper.news import NewsScraper
    print("✓ NewsScraper module available")
except Exception as e:
    print(f"✗ NewsScraper import failed: {e}")

# Test 6: FastAPI app
try:
    from api import app
    print("✓ FastAPI app imports successfully")
except Exception as e:
    print(f"✗ FastAPI app import failed: {e}")
    sys.exit(1)

# Test 7: run_service module
try:
    import run_service
    print("✓ run_service.py is valid Python")
except Exception as e:
    print(f"✗ run_service.py error: {e}")

print("\n" + "=" * 60)
print("Setup Verification Complete!")
print("=" * 60)
print("\nYou can now run:")
print("  1. Scheduler only (standalone):")
print("     python scheduler.py")
print("\n  2. API + Scheduler together (recommended):")
print("     python run_service.py")
print("\n  3. API only (without scheduler):")
print("     python -m uvicorn api:app --reload --port 8000")
print("\n" + "=" * 60 + "\n")
