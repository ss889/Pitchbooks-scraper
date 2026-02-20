"""Test regex patterns for funding extraction."""
import re

# Test the specific patterns
patterns = [
    r'\$(\d+\.?\d*)\s*(?:billion|million|m\b|bn\b|b\b|k\b)',  
    r'(?:raises?|secured?|closed|obtained?|announced?|worth|valued?\s*at)\s+\$(\d+\.?\d*)\s*(?:billion|million|m\b|bn\b|b\b|k\b)?',
    r'(\d+\.?\d*)\s*(?:billion|million)\s*(?:dollar|usd)?(?:\s*in\s*funding)?',
]

test_texts = [
    '$100 billion in funding',
    'OpenAI is finalizing $100 billion in funding',
    'raises $67M Series B',
    'raises $67 million',
    'Anthropic raises $2B from Google',
    '100 billion dollar funding',
]

for text in test_texts:
    print(f'Text: "{text}"')
    for i, pattern in enumerate(patterns):
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            for m in matches:
                print(f'  Pattern {i+1}: matched="{m.group(0)}", group1="{m.group(1)}"')
    print()
