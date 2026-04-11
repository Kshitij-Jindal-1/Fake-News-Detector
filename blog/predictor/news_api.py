"""
News API utilities for fetching REAL headlines via Google News RSS.
No API key needed — uses Google News RSS which is free and reliable.
"""
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, urlparse
from django.core.cache import cache

CACHE_KEY = 'news_headlines_{country}_{category}'
CACHE_TIMEOUT = 600  # 10 minutes


def fetch_headlines(country='in', category='general', page_size=15):
    """
    Fetch top headlines from Google News RSS.
    
    Args:
        country: Country code (in, us, gb, etc.)
        category: Category (general, business, technology, sports, etc.)
        page_size: Number of articles to fetch
        
    Returns:
        List of headline dictionaries with text, url, and source
    """
    cache_key = CACHE_KEY.format(country=country, category=category)
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        print(f"[NEWS] Serving {len(cached)} cached headlines")
        return cached
    
    try:
        headlines = _fetch_google_news_rss(country, category, page_size)
        
        if headlines:
            # Cache the results
            cache.set(cache_key, headlines, CACHE_TIMEOUT)
            print(f"[NEWS] Fetched {len(headlines)} real headlines from Google News RSS")
            return headlines
        else:
            print("[NEWS] Google News RSS returned no results, using fallback")
            return get_fallback_headlines()
            
    except Exception as e:
        print(f"[ERROR] News fetch failed: {e}")
        return get_fallback_headlines()


def _fetch_google_news_rss(country='in', category='general', page_size=15):
    """
    Fetch headlines from Google News RSS feed.
    
    Google News RSS endpoints:
    - Top stories: https://news.google.com/rss?hl=en-{COUNTRY}&gl={COUNTRY}&ceid={COUNTRY}:en
    - By topic: https://news.google.com/rss/topics/{TOPIC_ID}?hl=en&gl={COUNTRY}&ceid={COUNTRY}:en
    - Search:   https://news.google.com/rss/search?q={QUERY}&hl=en&gl={COUNTRY}&ceid={COUNTRY}:en
    """
    # Map category to Google News topic IDs
    category_map = {
        'general': None,  # Top stories (no topic needed)
        'business': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pKVGlnQVAB',
        'technology': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pKVGlnQVAB',
        'sports': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pKVGlnQVAB',
        'science': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pKVGlnQVAB',
        'health': 'CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ',
        'entertainment': 'CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pKVGlnQVAB',
    }
    
    # Map country codes
    country_upper = country.upper()
    gl = country_upper
    ceid = f"{country_upper}:en"
    hl = 'en'
    
    # Special handling for India (Hindi/English mixed)
    if country_upper == 'IN':
        hl = 'en-IN'
    
    # Build URL
    topic_id = category_map.get(category)
    if topic_id:
        url = f"https://news.google.com/rss/topics/{topic_id}?hl={hl}&gl={gl}&ceid={ceid}"
    else:
        url = f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        print(f"[NEWS] Google News RSS HTTP {resp.status_code}")
        return []
    
    root = ET.fromstring(resp.content)
    items = root.findall('.//item')
    
    headlines = []
    seen_titles = set()
    
    for item in items[:page_size]:
        title_el = item.find('title')
        link_el = item.find('link')
        source_el = item.find('source')
        
        if title_el is None or not title_el.text:
            continue
            
        title = title_el.text.strip()
        
        # Skip duplicates
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        # Get URL
        url = link_el.text if link_el is not None and link_el.text else '#'
        
        # Get source name
        source_name = ''
        if source_el is not None:
            source_name = source_el.text or ''
        
        # Add emoji based on category/keywords
        emoji = _get_headline_emoji(title, category)
        
        headlines.append({
            'text': f"{emoji} {title}" if emoji else title,
            'url': url,
            'source': source_name,
        })
    
    return headlines


def _get_headline_emoji(title: str, category: str) -> str:
    """Add relevant emoji to headline based on content."""
    title_lower = title.lower()
    
    # Category-based
    category_emojis = {
        'sports': '🏆',
        'technology': '💻',
        'business': '📈',
        'science': '🔬',
        'health': '🏥',
        'entertainment': '🎬',
    }
    if category in category_emojis:
        return category_emojis[category]
    
    # Content-based for 'general'
    if any(w in title_lower for w in ['breaking', 'urgent', 'just in']):
        return '🔴'
    if any(w in title_lower for w in ['cricket', 'ipl', 'match', 'world cup', 'sports']):
        return '🏏'
    if any(w in title_lower for w in ['war', 'military', 'attack', 'bomb', 'strike']):
        return '⚠️'
    if any(w in title_lower for w in ['election', 'vote', 'modi', 'parliament', 'congress', 'bjp']):
        return '🗳️'
    if any(w in title_lower for w in ['market', 'stock', 'economy', 'gdp', 'trade', 'tariff']):
        return '📊'
    if any(w in title_lower for w in ['tech', 'ai', 'google', 'apple', 'microsoft']):
        return '💡'
    if any(w in title_lower for w in ['climate', 'weather', 'flood', 'earthquake']):
        return '🌍'
    
    return '📰'


def get_fallback_headlines():
    """Return fallback headlines when API fails."""
    return [
        {"text": "📰 Could not load live headlines — check your internet connection", "url": "#", "source": "System"},
    ]
