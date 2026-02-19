"""
URL Validation Utilities for PitchBook Scraper.

Ensures every article URL is verified before storage,
supporting the newsletter workflow where broken links
are unacceptable.
"""

import asyncio
import logging
import aiohttp
from typing import Optional, Tuple
from urllib.parse import urlparse
from enum import Enum

logger = logging.getLogger(__name__)


class URLStatus(Enum):
    """URL accessibility status for newsletter content tracking."""
    ACCESSIBLE = "accessible"       # Full content available
    PREVIEW_ONLY = "preview_only"   # Paywall/login required
    INACCESSIBLE = "inaccessible"   # 404, timeout, or error
    UNCHECKED = "unchecked"         # Not yet validated


async def validate_url(
    url: str,
    timeout: int = 10,
    follow_redirects: bool = True
) -> Tuple[URLStatus, Optional[int], Optional[str]]:
    """
    Validate a URL and determine its accessibility status.
    
    Returns:
        Tuple of (URLStatus, status_code, final_url after redirects)
    
    For newsletter creators: This ensures every link we store
    will work when a journalist clicks it.
    """
    if not url or not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL format: {url}")
        return URLStatus.INACCESSIBLE, None, None
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=follow_redirects,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            ) as response:
                status_code = response.status
                final_url = str(response.url)
                
                if status_code == 200:
                    return URLStatus.ACCESSIBLE, status_code, final_url
                elif status_code in (401, 402, 403):
                    # Paywall or authentication required
                    return URLStatus.PREVIEW_ONLY, status_code, final_url
                elif status_code == 404:
                    return URLStatus.INACCESSIBLE, status_code, final_url
                elif status_code in (301, 302, 307, 308):
                    # Redirect without following (shouldn't happen with follow_redirects=True)
                    return URLStatus.ACCESSIBLE, status_code, final_url
                else:
                    logger.warning(f"Unexpected status {status_code} for {url}")
                    return URLStatus.INACCESSIBLE, status_code, final_url
                    
    except asyncio.TimeoutError:
        logger.warning(f"Timeout validating URL: {url}")
        return URLStatus.INACCESSIBLE, None, None
    except aiohttp.ClientError as e:
        logger.warning(f"Client error validating {url}: {e}")
        return URLStatus.INACCESSIBLE, None, None
    except Exception as e:
        logger.error(f"Unexpected error validating {url}: {e}")
        return URLStatus.INACCESSIBLE, None, None


def validate_url_sync(url: str, timeout: int = 10) -> Tuple[URLStatus, Optional[int], Optional[str]]:
    """
    Synchronous wrapper for URL validation.
    
    Use this in non-async contexts like database operations
    or CLI commands.
    """
    import requests
    
    if not url or not url.startswith(('http://', 'https://')):
        return URLStatus.INACCESSIBLE, None, None
    
    try:
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        status_code = response.status_code
        final_url = response.url
        
        if status_code == 200:
            return URLStatus.ACCESSIBLE, status_code, str(final_url)
        elif status_code in (401, 402, 403):
            return URLStatus.PREVIEW_ONLY, status_code, str(final_url)
        else:
            return URLStatus.INACCESSIBLE, status_code, str(final_url)
            
    except requests.Timeout:
        return URLStatus.INACCESSIBLE, None, None
    except requests.RequestException:
        return URLStatus.INACCESSIBLE, None, None


def is_valid_url_format(url: str) -> bool:
    """
    Check if URL has valid format (doesn't verify accessibility).
    
    Quick check before attempting network validation.
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Normalize URL for consistent storage and deduplication.
    
    - Removes trailing slashes
    - Lowercases scheme and host
    - Removes default ports
    """
    if not url:
        return url
        
    parsed = urlparse(url)
    
    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Remove default ports
    if netloc.endswith(':80') and scheme == 'http':
        netloc = netloc[:-3]
    elif netloc.endswith(':443') and scheme == 'https':
        netloc = netloc[:-4]
    
    # Remove trailing slash from path
    path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
    
    # Reconstruct URL
    normalized = f"{scheme}://{netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized


async def batch_validate_urls(urls: list[str], max_concurrent: int = 5) -> dict[str, URLStatus]:
    """
    Validate multiple URLs concurrently.
    
    Useful for cleaning up existing database or validating
    a scrape batch before insertion.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}
    
    async def validate_with_semaphore(url: str):
        async with semaphore:
            status, _, _ = await validate_url(url)
            return url, status
    
    tasks = [validate_with_semaphore(url) for url in urls]
    completed = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in completed:
        if isinstance(result, Exception):
            continue
        url, status = result
        results[url] = status
    
    return results
