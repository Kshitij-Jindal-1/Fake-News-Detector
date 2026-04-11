"""
Web scraping utilities for extracting article content from URLs.
"""

import trafilatura
import requests
from typing import Optional
from urllib.parse import urlparse


def extract_article_text(url: str) -> dict:
    """
    Extract the main article text from a URL using trafilatura with fallback.
    
    Args:
        url: The URL of the news article
        
    Returns:
        Dictionary with 'text', 'title', 'author', 'date', 'source' or 'error'
    """
    try:
        # Set custom headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Try downloading with custom headers
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            downloaded = response.text
        except Exception as e:
            # Fallback to trafilatura's default fetch
            print(f"[INFO] requests failed, trying trafilatura: {e}")
            downloaded = trafilatura.fetch_url(url)
        
        if downloaded is None or len(str(downloaded).strip()) == 0:
            return {'error': 'Failed to download the URL. The page may be inaccessible or blocking automated access.'}
        
        # Extract main content
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            favor_recall=True  # Get more content even if less precise
        )
        
        if not text or len(text.strip()) < 50:
            return {
                'error': 'Could not extract sufficient text from the URL. The website may be using JavaScript to load content or blocking scrapers.'
            }
        
        # Extract metadata
        metadata = trafilatura.extract_metadata(downloaded)
        
        result = {
            'text': text,
            'source': url,
        }
        
        if metadata:
            if metadata.title:
                result['title'] = metadata.title
            if metadata.author:
                result['author'] = metadata.author
            if metadata.date:
                result['date'] = metadata.date
            if metadata.hostname:
                result['hostname'] = metadata.hostname
        
        return result
        
    except requests.exceptions.Timeout:
        return {'error': 'Request timeout. The website took too long to respond.'}
    except requests.exceptions.ConnectionError:
        return {'error': 'Connection failed. Check your internet connection or the URL may be invalid.'}
    except requests.exceptions.HTTPError as e:
        return {'error': f'HTTP error {e.response.status_code}. The page may not exist or may be restricted.'}
    except Exception as e:
        return {'error': f'Error extracting content: {str(e)}'}


def is_valid_url(url: str) -> bool:
    """Check if the provided string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception:
        return False

