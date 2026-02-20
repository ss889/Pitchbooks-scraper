"""
AI News Parser – Intelligent extraction of deal information,
companies, investors, and relevance scoring from news articles.

This module helps reporters understand AI market dynamics by extracting:
  • Funding deals and amounts
  • Company and investor names
  • AI technology categories
  • Deal relevance to AI sector
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("ai_parser")


class AINewsParser:
    """Parse news articles for AI-specific deal and company information."""
    
    # AI Technology Categories
    AI_CATEGORIES = {
        "generative_ai": {
            "keywords": ["generative ai", "gpt", "claude", "gemini", "grok", "llm", "large language model",
                        "text generation", "image generation", "diffusion", "transformer"],
            "weight": 1.0
        },
        "machine_learning": {
            "keywords": ["machine learning", "ml", "neural network", "deep learning", "training data",
                        "model training", "supervised learning", "unsupervised learning"],
            "weight": 0.9
        },
        "computer_vision": {
            "keywords": ["computer vision", "object detection", "image recognition", "video analysis",
                        "visual", "cv model", "vision transformer"],
            "weight": 0.85
        },
        "nlp": {
            "keywords": ["natural language", "nlp", "language model", "text analysis", "sentiment analysis",
                        "voice", "speech recognition", "transcription"],
            "weight": 0.85
        },
        "ai_infrastructure": {
            "keywords": ["gpu", "tpu", "accelerator", "inference", "model serving", "mlops", "computational",
                        "cloud compute", "distributed training", "vector database", "embedding"],
            "weight": 1.0
        },
        "ai_agents": {
            "keywords": ["ai agent", "autonomous agent", "reasoning", "multi-step", "agentic", "agent engineering",
                        "task automation", "workflow automation"],
            "weight": 1.0
        },
        "robotics": {
            "keywords": ["robotics", "robot", "autonomous robot", "robot learning", "embodied ai"],
            "weight": 0.8
        },
        "ai_safety": {
            "keywords": ["ai safety", "alignment", "bias detection", "safety", "fairness", "interpretability",
                        "explainability", "responsible ai", "ethics"],
            "weight": 0.9
        },
        "enterprise_ai": {
            "keywords": ["enterprise ai", "business ai", "enterprise software", "saas", "b2b", "copilot",
                        "workplace", "productivity", "workflow"],
            "weight": 0.85
        }
    }
    
    # Funding patterns - more flexible
    FUNDING_PATTERNS = [
        r'\$(\d+\.?\d*)\s*(?:billion|million|m\b|bn\b|b\b|k\b)',  # $5M, $1.2B, $500K
        r'(?:raises?|secured?|closed|obtained?|announced?|worth|valued?\s*at)\s+\$(\d+\.?\d*)\s*(?:billion|million|m\b|bn\b|b\b|k\b)?',
        r'(?:series|round)\s*[a-z]\s*(?:of|worth)?\s*\$(\d+\.?\d*)\s*(?:billion|million|m\b|bn\b|b\b|k\b)?',
        r'(\d+\.?\d*)\s*(?:billion|million)\s*(?:dollar|usd)?(?:\s*in\s*funding)?',
    ]
    
    FUNDING_MULTIPLIERS = {
        'k': 1_000,
        'm': 1_000_000,
        'million': 1_000_000,
        'b': 1_000_000_000,
        'bn': 1_000_000_000,
        'billion': 1_000_000_000,
    }
    
    # Round types
    ROUND_PATTERNS = {
        'seed': r'(?:seed\s*round|seed\s*funding)',
        'series_a': r'(?:series\s*a|\$series\s*a)',
        'series_b': r'(?:series\s*b)',
        'series_c': r'(?:series\s*c)',
        'series_d': r'(?:series\s*d)',
        'series_e': r'(?:series\s*e)',
        'series_f': r'(?:series\s*f)',
        'ipo': r'(?:ipo|initial\s*public\s*offering|goes?\s*public)',
        'acquisition': r'(?:acquired?|acquisition|taken\s*over)',
        'merger': r'(?:merged?|merger)',
    }
    
    # Major AI companies and investors to track
    MAJOR_AI_COMPANIES = {
        "openai", "anthropic", "google", "meta", "microsoft", "tesla", "nvidia",
        "groq", "together", "cohere", "stability", "hugging face", "mistral",
        "aleph alpha", "adept", "jasper", "copy.ai", "perplexity", "scale ai",
        "databricks", "modal", "vllm", "fireworks", "novita", "inflection",
        "character ai", "runway", "midjourney", "pika", "glean", "writer",
        "read ai", "sierra", "cognition", "devin", "factory", "magic",
        "cursor", "replit", "codeium", "tabnine", "sourcegraph", "anyscale",
        "langchain", "llamaindex", "pinecone", "weaviate", "chroma", "qdrant",
        "deepmind", "xai", "ai21", "amazon bedrock", "cerebras", "sambanova",
    }
    
    MAJOR_INVESTORS = {
        "sequoia", "a16z", "andreessen horowitz", "benchmark", "greylock", "khosla",
        "redpoint", "menlo", "spark", "vertex", "bessemer", "lightspeed", "insight",
        "accel", "founders fund", "google ventures", "microsoft ventures", "tiger global",
        "softbank", "general catalyst", "index ventures", "thrive capital", "coatue",
        "felicis", "kleiner perkins", "nea", "ivp", "dst global", "global founders",
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def parse_article(self, title: str, content: str, url: str = "") -> Dict:
        """
        Comprehensive parse of a news article.
        
        Returns:
            {
                'ai_relevance_score': float (0-1),
                'ai_categories': List[str],
                'is_deal_news': bool,
                'deals': List[Dict],
                'companies': List[str],
                'investors': List[str],
                'summary': str
            }
        """
        text = f"{title} {content}".lower()
        
        # Calculate AI relevance score
        relevance_score = self._calculate_relevance(title, text)
        
        # Extract AI categories
        categories = self._extract_categories(text)
        
        # Detect if this is deal news
        is_deal_news = self._is_deal_news(text)
        
        # Extract deals
        deals = self._extract_deals(text, title) if is_deal_news else []
        
        # Extract entities
        companies = self._extract_companies(text)
        investors = self._extract_investors(text)
        
        # Create summary
        summary = self._create_summary(title, content, deals, companies)
        
        return {
            'ai_relevance_score': relevance_score,
            'ai_categories': categories,
            'is_deal_news': is_deal_news,
            'deals': deals,
            'companies': companies,
            'investors': investors,
            'summary': summary
        }
    
    def _calculate_relevance(self, title: str, text: str) -> float:
        """Calculate AI relevance score (0-1)."""
        score = 0.0
        text_lower = text.lower()
        
        # Title weight is higher (news titles are descriptive)
        title_lower = title.lower()
        
        # Check for core AI keywords
        ai_core = ["artificial intelligence", "ai", "machine learning", "neural", "deep learning"]
        if any(kw in title_lower for kw in ai_core):
            score += 0.5
        if any(kw in text_lower for kw in ai_core):
            score += 0.3
        
        # Check categories
        category_weighted_score = 0.0
        max_category_weight = 0.0
        for category, data in self.AI_CATEGORIES.items():
            keywords = data['keywords']
            weight = data['weight']
            max_category_weight = max(max_category_weight, weight)
            
            if any(kw in text_lower for kw in keywords):
                category_weighted_score = max(category_weighted_score, weight)
        
        if category_weighted_score > 0:
            score += (category_weighted_score / 1.0) * 0.2  # Categories contribute max 20%
        
        # Deal news gets positive boost
        if self._is_deal_news(text):
            score += 0.15
        
        # Funding mentions
        if self._extract_funding_amount(text):
            score += 0.1
        
        # Normalize to 0-1
        return min(1.0, score)
    
    def _extract_categories(self, text: str) -> List[str]:
        """Extract relevant AI categories from text."""
        categories = []
        text_lower = text.lower()
        
        for category, data in self.AI_CATEGORIES.items():
            keywords = data['keywords']
            if any(kw in text_lower for kw in keywords):
                categories.append(category)
        
        return categories
    
    def _is_deal_news(self, text: str) -> bool:
        """Determine if this is deal/funding news."""
        deal_keywords = [
            "raises", "raised", "funding", "investment", "funded", "acquir",
            "merger", "ipo", "series", "seed round", "venture capital",
            "round of funding", "million", "billion", "acquisition",
        ]
        
        return any(kw in text for kw in deal_keywords)
    
    def _extract_funding_amount(self, text: str) -> Optional[Tuple[float, str]]:
        """Extract funding amount. Returns (amount_usd, original_text)."""
        for pattern in self.FUNDING_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.group(1))
                    multiplier_text = match.group(0).lower()
                    
                    # Find multiplier
                    multiplier = 1
                    for key, mult in self.FUNDING_MULTIPLIERS.items():
                        if key in multiplier_text:
                            multiplier = mult
                            break
                    
                    amount_usd = amount * multiplier
                    return (amount_usd, match.group(0))
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def _extract_deals(self, text: str, title: str) -> List[Dict]:
        """Extract deal information from article."""
        deals = []
        
        # Try to find funding amount
        funding = self._extract_funding_amount(text)
        if not funding:
            return deals
        
        amount_usd, amount_text = funding
        
        # Find company name (usually mentioned in context of funding)
        company = self._extract_primary_company(text)
        if not company:
            company = self._extract_company_from_title(title)
        
        # Find round type
        round_type = self._extract_round_type(text)
        
        # Find investors
        investors = self._extract_investors(text)
        
        # Find date
        date = self._extract_date(text)
        
        if company:
            deals.append({
                'company': company,
                'amount_usd': amount_usd,
                'amount_text': amount_text,
                'round_type': round_type,
                'investors': investors,
                'date': date,
                'confidence': 0.8 if company and amount_usd else 0.5
            })
        
        return deals
    
    def _extract_companies(self, text: str) -> List[str]:
        """Extract mentioned companies."""
        companies = []
        
        # Look for major AI companies
        for company in self.MAJOR_AI_COMPANIES:
            pattern = r'\b' + company + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                companies.append(company.title())
        
        # Look for capitalized words that might be company names
        # (simplified - in production, use better NER)
        capitalized = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\b', text)
        for cap in capitalized[:10]:  # Limit to avoid noise
            if len(cap) > 2 and cap not in companies and cap not in ["The", "And", "For"]:
                if cap not in text[:100]:  # Prioritize companies mentioned early
                    companies.append(cap)
        
        return list(set(companies))[:15]  # Limit and deduplicate
    
    def _extract_investors(self, text: str) -> List[str]:
        """Extract mentioned investors."""
        investors = []
        
        for investor in self.MAJOR_INVESTORS:
            pattern = r'\b' + investor + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                investors.append(investor.title())
        
        return list(set(investors))
    
    def _extract_round_type(self, text: str) -> Optional[str]:
        """Identify funding round type."""
        for round_name, pattern in self.ROUND_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return round_name
        return None
    
    def _extract_primary_company(self, text: str) -> Optional[str]:
        """Extract the main company being discussed."""
        # Blocklist of common false positives 
        blocklist = {
            'the', 'and', 'for', 'new', 'how', 'why', 'what', 'this', 'that',
            'former', 'china', 'saudi', 'retail', 'partnerships', 'just',
            'african', 'asian', 'european', 'american', 'global', 'local',
            'pitchbook', 'report', 'article', 'news', 'breaking', 'latest',
            'india', 'indian', 'china', 'chinese', 'us', 'uk'
        }
        
        # First check for known AI companies (most reliable)
        text_lower = text.lower()
        for company in self.MAJOR_AI_COMPANIES:
            if company in text_lower:
                # Check if it appears in a funding context
                pattern = rf'\b{company}\b.*?(?:raises?|announces?|secured?|closes?|funding|billion|million)'
                if re.search(pattern, text_lower):
                    return company.title()
        
        # Look for patterns like "{Company} raises" or "{Company} announces"
        patterns = [
            r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:raises?|announces?|secured?|closes?)\s+\$',
            r'(?:startup|company)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:raises?|has)',
            r'^([A-Z][a-zA-Z]+(?:\s+AI)?)\s+raises?\s+\$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if name.lower() not in blocklist and len(name) > 2:
                    return name
        
        return None
    
    def _extract_company_from_title(self, title: str) -> Optional[str]:
        """Extract company name from article title."""
        # Blocklist
        blocklist = {
            'the', 'and', 'for', 'new', 'how', 'why', 'what', 'this', 'that',
            'former', 'china', 'saudi', 'retail', 'partnerships', 'just',
            'african', 'asian', 'european', 'american', 'global', 'local',
            'pitchbook', 'report', 'article', 'news', 'breaking', 'latest',
            'close', 'indexes', 'india', 'indian'
        }
        
        # First check for known AI companies 
        title_lower = title.lower()
        for company in self.MAJOR_AI_COMPANIES:
            if company in title_lower:
                return company.title()
        
        # Try: Look for "X raises $Y" pattern
        funding_match = re.search(r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+raises?\s+\$', title)
        if funding_match:
            name = funding_match.group(1)
            if name.lower() not in blocklist and len(name) > 2:
                return name
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Try to extract publication/announcement date."""
        # Look for date patterns
        patterns = [
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _create_summary(self, title: str, content: str, deals: List[Dict], companies: List[str]) -> str:
        """Create a concise summary highlighting key information."""
        summary_parts = [title]
        
        if deals:
            for deal in deals:
                if deal.get('company') and deal.get('amount_usd'):
                    summary_parts.append(
                        f"{deal['company']} raised {deal['amount_text']} "
                        f"({deal.get('round_type', 'funding')})"
                    )
        
        if companies:
            summary_parts.append(f"Key companies: {', '.join(companies[:5])}")
        
        return " | ".join(summary_parts[:3])
