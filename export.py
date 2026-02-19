#!/usr/bin/env python3
"""
Data Export Tool - Export AI news database to various formats

Useful for reporters, analysts, and researchers who want to:
  • Export deals to CSV for analysis
  • Generate funding reports
  • Create company lists
  • Track investor activity
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from db import get_db

def export_deals_csv(filename="ai_deals_export.csv", limit=500):
    """Export deals to CSV format."""
    db = get_db()
    deals = db.get_deals(limit=limit)
    
    if not deals:
        print("⚠️  No deals found in database")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'company_name', 'funding_amount', 'funding_currency',
                'round_type', 'investors', 'announcement_date',
                'published_date', 'title', 'url'
            ])
            writer.writeheader()
            
            for deal in deals:
                writer.writerow({
                    'company_name': deal.get('company_name', ''),
                    'funding_amount': deal.get('funding_amount', ''),
                    'funding_currency': deal.get('funding_currency', 'USD'),
                    'round_type': deal.get('round_type', ''),
                    'investors': deal.get('investors', ''),
                    'announcement_date': deal.get('announcement_date', ''),
                    'published_date': deal.get('published_date', ''),
                    'title': deal.get('title', ''),
                    'url': deal.get('url', '')
                })
        
        print(f"✓ Exported {len(deals)} deals to {filename}")
        return True
    except Exception as e:
        print(f"✗ Error exporting: {e}")
        return False

def export_articles_json(filename="ai_articles_export.json", limit=500, min_relevance=0.0):
    """Export articles to JSON format."""
    db = get_db()
    articles = db.get_articles(limit=limit, min_relevance=min_relevance)
    
    if not articles:
        print("⚠️  No articles found in database")
        return False
    
    try:
        # Convert Row objects to dicts if needed
        articles_list = [dict(a) for a in articles]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'exported_at': datetime.now().isoformat(),
                'total_articles': len(articles_list),
                'min_relevance_score': min_relevance,
                'articles': articles_list
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported {len(articles_list)} articles to {filename}")
        return True
    except Exception as e:
        print(f"✗ Error exporting: {e}")
        return False

def export_funding_report(filename="funding_report_ai.txt"):
    """Generate a text report of AI funding trends."""
    db = get_db()
    stats = db.get_statistics()
    deals = db.get_deals(limit=100)
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("AI MARKET FUNDING REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary Statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total Articles Tracked:    {stats['total_articles']}\n")
            f.write(f"Total Deals:               {stats['total_deals']}\n")
            f.write(f"Total Companies:           {stats['total_companies']}\n")
            f.write(f"Total Investors:           {stats['total_investors']}\n")
            f.write(f"Total Funding:             ${stats['total_funding_usd']:,.0f}\n")
            f.write(f"Average Relevance Score:   {stats['avg_relevance_score']:.2%}\n\n")
            
            # Top Deals
            f.write("TOP FUNDING DEALS\n")
            f.write("-" * 70 + "\n")
            
            sorted_deals = sorted(deals, key=lambda d: d.get('funding_amount', 0) or 0, reverse=True)
            
            for i, deal in enumerate(sorted_deals[:20], 1):
                company = deal.get('company_name', 'Unknown')
                amount = deal.get('funding_amount', 0)
                currency = deal.get('funding_currency', 'USD')
                round_type = deal.get('round_type', 'Funding')
                date = deal.get('announcement_date', '')
                
                f.write(f"\n{i}. {company.upper()}\n")
                f.write(f"   Amount:  ${amount:,.0f} {currency}\n")
                f.write(f"   Round:   {round_type}\n")
                if date:
                    f.write(f"   Date:    {date}\n")
        
        print(f"✓ Generated funding report: {filename}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def show_statistics():
    """Show database statistics."""
    db = get_db()
    stats = db.get_statistics()
    
    print("\n" + "=" * 70)
    print("DATABASE STATISTICS")
    print("=" * 70)
    print(f"Total Articles:          {stats['total_articles']:>10}")
    print(f"Total Deals:             {stats['total_deals']:>10}")
    print(f"Total Companies:         {stats['total_companies']:>10}")
    print(f"Total Investors:         {stats['total_investors']:>10}")
    print(f"Total Funding Tracked:   ${stats['total_funding_usd']:>15,.0f}")
    print(f"Average Relevance Score: {stats['avg_relevance_score']:>10.2%}")
    print("=" * 70 + "\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Export AI news database to various formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export.py --deals                        # Export all deals to CSV
  python export.py --articles                     # Export articles to JSON
  python export.py --articles --min-relevance 0.7 # Only high-relevance
  python export.py --report                       # Generate funding report
  python export.py --stats                        # Show statistics
  python export.py --all                          # Export everything
        """
    )
    
    parser.add_argument('--deals', action='store_true', help='Export deals to CSV')
    parser.add_argument('--articles', action='store_true', help='Export articles to JSON')
    parser.add_argument('--report', action='store_true', help='Generate funding report')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--all', action='store_true', help='Export everything')
    
    parser.add_argument('--output', type=str, help='Output filename prefix')
    parser.add_argument('--limit', type=int, default=500, help='Max records to export')
    parser.add_argument('--min-relevance', type=float, default=0.0, help='Minimum relevance score (0-1)')
    
    args = parser.parse_args()
    
    # If no action specified, show stats
    if not any([args.deals, args.articles, args.report, args.stats, args.all]):
        args.stats = True
    
    print("\n📊 AI News Database Export Tool\n")
    
    if args.stats or args.all:
        show_statistics()
    
    if args.deals or args.all:
        filename = args.output or "ai_deals_export.csv"
        if not filename.endswith('.csv'):
            filename += '.csv'
        export_deals_csv(filename, limit=args.limit)
    
    if args.articles or args.all:
        filename = args.output or "ai_articles_export.json"
        if not filename.endswith('.json'):
            filename += '.json'
        export_articles_json(filename, limit=args.limit, min_relevance=args.min_relevance)
    
    if args.report or args.all:
        filename = args.output or "funding_report_ai.txt"
        if not filename.endswith('.txt'):
            filename += '.txt'
        export_funding_report(filename)
    
    print("\n✓ Done!\n")

if __name__ == "__main__":
    main()
