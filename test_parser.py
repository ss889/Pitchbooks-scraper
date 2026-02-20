"""Test AI parser with sample articles."""
import sys
sys.path.insert(0, 'src')

from scraper.ai_parser import AINewsParser

# Force reimport
import importlib
import scraper.ai_parser
importlib.reload(scraper.ai_parser)
parser = scraper.ai_parser.AINewsParser()

test_cases = [
    {
        "title": "OpenAI reportedly finalizing $100B deal at more than $300B valuation",
        "content": "OpenAI is finalizing $100 billion in funding that will value the company at more than $300 billion."
    },
    {
        "title": "Freeform raises $67M Series B to scale up laser AI",
        "content": "Freeform, a startup using AI for laser manufacturing, has raised $67 million in Series B funding led by Andreessen Horowitz."
    },
    {
        "title": "Anthropic raises $2B from Google",
        "content": "AI company Anthropic has secured $2 billion in funding from Google as it continues to develop its Claude chatbot."
    },
    {
        "title": "Reliance unveils $110B AI investment plan as India bets big on tech",
        "content": "Indian conglomerate Reliance Industries has announced a $110 billion investment in AI technology."
    }
]

for i, tc in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"Test {i}: {tc['title'][:50]}...")
    print("="*60)
    
    result = parser.parse_article(tc['title'], tc['content'])
    print(f"is_deal_news: {result.get('is_deal_news')}")
    print(f"companies: {result.get('companies')}")
    print(f"investors: {result.get('investors')}")
    print(f"deals: {result.get('deals')}")
