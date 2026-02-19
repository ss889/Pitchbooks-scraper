#!/usr/bin/env python3
"""
Quick Start: Initialize AI News Intelligence System

This script helps you get started with the AI news scraper in 60 seconds.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    print("\n" + "=" * 70)
    print("  AI NEWS INTELLIGENCE PLATFORM - Quick Start")
    print("=" * 70 + "\n")

def check_python():
    """Check Python version."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. You have:", sys.version)
        sys.exit(1)
    print("✓ Python version:", sys.version.split()[0])

def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Checking dependencies...")
    
    required = ['playwright', 'bs4', 'lxml']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (MISSING)")
            missing.append(pkg)
    
    if missing:
        print(f"\n⚠️  Missing: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    return True

def check_database():
    """Check if database exists."""
    db_path = Path(__file__).parent / "ai_news.db"
    if db_path.exists():
        print(f"✓ Database exists: {db_path}")
        return True
    else:
        print(f"ℹ️  Database will be created on first scrape")
        return False

def init_database():
    """Initialize the database."""
    print("\n🗄️  Initializing database...")
    try:
        from db import get_db
        db = get_db()
        print("✓ Database initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def show_examples():
    """Show example commands."""
    print("\n" + "=" * 70)
    print("  QUICK START COMMANDS")
    print("=" * 70)
    
    examples = [
        ("Scrape AI news", "python main.py --news"),
        ("Show statistics", "python main.py --stats"),
        ("Open dashboard", "python main.py --view"),
        ("Scrape everything", "python main.py --all"),
        ("Custom delay (slower)", "python main.py --news --delay 5"),
        ("Query database", "python -c \"from db import get_db; db = get_db(); print(db.get_statistics())\""),
    ]
    
    for desc, cmd in examples:
        print(f"\n  {desc}:")
        print(f"    $ {cmd}")

def main():
    print_banner()
    
    # Checks
    print("🔍 Environment Check\n")
    check_python()
    
    if not check_dependencies():
        print("\n❌ Please install dependencies first:")
        print("   pip install -r requirements.txt")
        print("   playwright install chromium")
        sys.exit(1)
    
    # Database
    init_database()
    check_database()
    
    # Show examples
    show_examples()
    
    print("\n" + "=" * 70)
    print("  ✓ All systems ready!")
    print("  Start scraping: python main.py --news")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
