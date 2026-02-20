"""Check link status and data quality."""
import asyncio
import aiohttp
from db import get_db

async def check_url(session, url):
    try:
        async with session.head(url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as r:
            return r.status
    except Exception as e:
        return str(e)[:30]

async def main():
    db = get_db()
    articles = db.get_articles(limit=20)
    deals = db.get_deals(50)
    
    # Check investors
    investors = set()
    for d in deals:
        if d.get('investors'):
            for inv in d['investors'].split(', '):
                if inv.strip() and len(inv) > 2:
                    investors.add(inv.strip())
    
    # Check startups with actual funding amounts
    startups = {}
    for d in deals:
        company = d.get('company_name', '')
        amount = d.get('funding_amount')
        # Filter out bad parses
        if company and amount and len(company) > 2 and amount > 1000000:
            # Skip common false positives
            bad_names = ['how', 'the', 'as', 'just', 'former', 'saudi', 'china', 'retail', 'partnerships']
            if company.lower() not in bad_names:
                startups[company] = amount
    
    print("=" * 50)
    print("DATA QUALITY CHECK")
    print("=" * 50)
    
    print(f"\n📊 TOP INVESTORS ({len(investors)} total)")
    for inv in sorted(list(investors))[:10]:
        print(f"   • {inv}")
    
    print(f"\n🚀 TOP STARTUPS (by funding)")
    sorted_startups = sorted(startups.items(), key=lambda x: x[1], reverse=True)[:10]
    for name, amount in sorted_startups:
        print(f"   • {name}: ${amount/1e6:.1f}M")
    
    # Check URLs
    print(f"\n🔗 LINK VALIDATION (checking {min(10, len(articles))} articles)")
    async with aiohttp.ClientSession() as session:
        for article in articles[:10]:
            url = article['url']
            status = await check_url(session, url)
            icon = "✅" if status == 200 else "⚠️" if status in (301, 302) else "❌"
            print(f"   {icon} [{status}] {url[:60]}...")
    
    # Summary
    print(f"\n📈 SUMMARY")
    stats = db.get_statistics()
    print(f"   Total Articles: {stats['total_articles']}")
    print(f"   Total Deals: {stats['total_deals']}")
    print(f"   Total Funding: ${stats['total_funding_usd']/1e9:.1f}B")
    print(f"   Avg Relevance: {stats['avg_relevance_score']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
