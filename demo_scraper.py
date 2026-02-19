"""
Demo scraper - Uses sample AI news data to demonstrate the system in action.
No actual scraping - just populates the database with realistic test data.
"""

import logging
from datetime import datetime, timedelta
from db import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample AI news articles for demo
SAMPLE_ARTICLES = [
    {
        "title": "OpenAI Raises $6.6B in Series C Funding Round",
        "summary": "OpenAI closed a Series C funding round at a $80B valuation, with major tech companies investing.",
        "content": "OpenAI announced a $6.6 billion Series C funding round led by Thrive Capital and Apollo Global Management. The round values the company at $80 billion. Microsoft, which has already invested billions, participated in the round. This funding will accelerate OpenAI's research into AI safety and scaling.",
        "url": "https://www.cnbc.com/2024/10/01/openai-raises-6-6-billion-in-series-c-funding/",
        "date": datetime.now() - timedelta(days=5),
        "categories": ["generative_ai", "enterprise_ai"],
        "deals": [
            {
                "company": "OpenAI",
                "amount_usd": 6600000000,
                "round_type": "Series C",
                "investors": ["Thrive Capital", "Apollo Global Management", "Microsoft"],
                "date": datetime.now() - timedelta(days=5)
            }
        ]
    },
    {
        "title": "Anthropic Completes $5B Funding to Build Constitutional AI",
        "summary": "Anthropic secures $5 billion in funding to develop safer large language models.",
        "content": "Anthropic, an AI safety-focused company founded by former OpenAI members, announced a $5 billion funding round. The funding will support research into constitutional AI and alignment techniques. Google made a significant investment alongside other institutional investors.",
        "url": "https://www.anthropic.com/news/anthropic-secures-5-billion-in-series-d-funding",
        "date": datetime.now() - timedelta(days=10),
        "categories": ["generative_ai", "ai_safety", "nlp"],
        "deals": [
            {
                "company": "Anthropic",
                "amount_usd": 5000000000,
                "round_type": "Series D",
                "investors": ["Google", "Salesforce Ventures", "Amazon"],
                "date": datetime.now() - timedelta(days=10)
            }
        ]
    },
    {
        "title": "Stability AI Raises Series A for Image Generation Tech",
        "summary": "Stability AI secures $101M Series A to scale Stable Diffusion and AI art generation.",
        "content": "Stability AI, creators of Stable Diffusion, announced a $101 million Series A funding round. The company focuses on democratizing AI by making generative models accessible. Funding from Coatue, O'Shaughnessy Ventures, and others will accelerate product development.",
        "url": "https://stability.ai/blog/stability-ai-funding-announcement",
        "date": datetime.now() - timedelta(days=15),
        "categories": ["generative_ai", "computer_vision"],
        "deals": [
            {
                "company": "Stability AI",
                "amount_usd": 101000000,
                "round_type": "Series A",
                "investors": ["Coatue", "O'Shaughnessy Ventures", "Lightning Ventures"],
                "date": datetime.now() - timedelta(days=15)
            }
        ]
    },
    {
        "title": "DeepMind Achieves Breakthrough in AI Protein Folding",
        "summary": "AlphaFold3 shows significant improvements in predicting protein structures and molecular interactions.",
        "content": "DeepMind announced a major breakthrough with AlphaFold3, which can now predict the structure of proteins, RNA, and other biological molecules with unprecedented accuracy. This advancement could accelerate drug discovery and biological research.",
        "url": "https://www.deepmind.com/blog/alphafold-3-structure-prediction-for-biology",
        "date": datetime.now() - timedelta(days=20),
        "categories": ["ai_infrastructure", "machine_learning"],
        "deals": []
    },
    {
        "title": "Tesla Unveils New AI Chip for FSD Development",
        "summary": "Tesla's new custom AI chip will power Full Self-Driving and autonomous vehicle capabilities.",
        "content": "Tesla announced a custom-designed AI chip optimized for autonomous driving. The chip accelerates neural network processing for Full Self-Driving (FSD) and improves real-time decision-making in vehicles. This move reduces dependency on third-party chip manufacturers.",
        "url": "https://www.tesla.com/AI/dojo",
        "date": datetime.now() - timedelta(days=25),
        "categories": ["ai_infrastructure", "robotics"],
        "deals": []
    },
]


def insert_sample_data():
    """Insert sample articles into the database."""
    
    print("\n" + "=" * 60)
    print("Demo Scraper - Sample Data")
    print("=" * 60 + "\n")
    
    try:
        db = get_db()
        
        # Get stats before
        stats_before = db.get_statistics()
        logger.info(f"Database before demo:")
        logger.info(f"  Articles: {stats_before['total_articles']}")
        logger.info(f"  Deals: {stats_before['total_deals']}\n")
        
        inserted_count = 0
        
        for article_data in SAMPLE_ARTICLES:
            # Check if URL already exists
            if db.article_exists(article_data["url"]):
                logger.info(f"[DUP] {article_data['title']}")
                continue
            
            # Insert article
            article_id = db.insert_article(
                url=article_data["url"],
                title=article_data["title"],
                summary=article_data["summary"],
                content=article_data["content"],
                published_date=article_data["date"],
                ai_relevance_score=0.92,  # All sample articles are highly relevant
                is_deal_news=1 if article_data["deals"] else 0
            )
            
            if not article_id:
                logger.warning(f"[ERR] Failed to insert: {article_data['title']}")
                continue
            
            # Add categories
            for category in article_data.get("categories", []):
                db.add_article_category(article_id, category)
            
            # Insert deals
            for deal in article_data.get("deals", []):
                db.insert_deal(
                    article_id=article_id,
                    company_name=deal["company"],
                    funding_amount=deal["amount_usd"],
                    round_type=deal["round_type"],
                    investors=", ".join(deal["investors"]),
                    announcement_date=deal["date"]
                )
            
            logger.info(f"[OK] {article_data['title']}")
            inserted_count += 1
        
        # Get stats after
        stats_after = db.get_statistics()
        logger.info(f"\n✓ Demo completed!")
        logger.info(f"\nDatabase after demo:")
        logger.info(f"  Total Articles: {stats_after['total_articles']}")
        logger.info(f"  Total Deals: {stats_after['total_deals']}")
        logger.info(f"  Total Funding: ${stats_after['total_funding_usd']:,.0f}")
        logger.info(f"  Average Relevance: {stats_after['avg_relevance_score']:.2f}")
        logger.info(f"  AI Categories: {stats_after['total_categories']}")
        
        print("\n" + "=" * 60)
        print("Sample Data Loaded! Now start the API:")
        print("=" * 60)
        print("\n  python run_service.py\n")
        print("Then visit: http://localhost:8000/docs\n")
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)


if __name__ == '__main__':
    insert_sample_data()
