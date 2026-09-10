"""
Source Verification module for fake news detection.
Searches the web for trusted sources covering the same topic
and uses measurable signals to calculate a source verification score.

The scoring uses 3 signals:
  1. Coverage Density - How widely is this story covered online?
  2. Trusted Source Ratio - What % of results come from verified outlets?
  3. Content Relevance - How closely do search results match the input text?

Each signal is formula-based with no hardcoded thresholds, 
making every score mathematically explainable.
"""

import re
import math
import time
from typing import List, Dict, Set
from urllib.parse import urlparse
from django.conf import settings


# ============================================================================
# TEXT PROCESSING
# ============================================================================

def clean_input_text(text: str) -> str:
    """
    Strip metadata prefixes from pasted article text.
    Users often paste articles with headers like 'Headline:', 'Published:', etc.
    """
    lines = text.strip().split('\n')
    cleaned_lines = []
    headline = None
    skip_prefixes = (
        'headline:', 'published:', 'byline:', 'article text',
        'end of excerpt', 'date:', 'author:', 'source:',
    )
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(lower.startswith(p) for p in skip_prefixes):
            # Extract content after colon for headline specifically
            if lower.startswith('headline:') and ':' in stripped:
                headline = stripped.split(':', 1)[1].strip()
            continue
        if stripped.startswith('(') and stripped.endswith(')'):
            continue  # Skip parenthetical notes like "(Guardian US staff)"
        cleaned_lines.append(stripped)
    
    cleaned = ' '.join(cleaned_lines)
    return cleaned, headline


def extract_keywords(text: str) -> Set[str]:
    """
    Extract significant keywords from text for relevance comparison.
    Removes common stop words and keeps meaningful terms.
    """
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
        'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
        'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'out', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
        'how', 'all', 'both', 'each', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'because', 'but', 'and', 'or',
        'if', 'while', 'about', 'up', 'that', 'this', 'these', 'those',
        'it', 'its', 'he', 'she', 'they', 'we', 'you', 'i', 'me', 'my',
        'your', 'his', 'her', 'their', 'our', 'said', 'also', 'which',
        'who', 'whom', 'what', 'been', 'them', 'him', 'an', 'will',
    }
    # Extract words, lowercase, filter short words and stop words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return {w for w in words if w not in stop_words}


def extract_key_phrases(text: str, max_phrases: int = 3) -> List[str]:
    """
    Extract key phrases from the input text for web searching.
    Strategy:
    0. Use FIRST LINE as headline (articles always start with the title)
    1. Use extracted headline if available (from 'Headline:' prefix)
    2. Find named entities from the body for additional queries
    3. Fall back to first sentence
    4. Informal text fallback: strip stop words, use dense keywords
    Keeps queries SHORT (<120 chars) for better search results.
    """
    cleaned, headline = clean_input_text(text)
    search_text = cleaned if cleaned else text.strip()

    queries = []

    # 0. First line = headline (both single-line and multi-line inputs)
    #    When users paste articles, the first line IS the title.
    #    When users paste headlines, the entire text IS the query.
    lines = [l.strip() for l in search_text.split('\n') if l.strip()]
    if lines:
        first_line = lines[0]
        
        # Clean common article metadata that gets concatenated with headlines
        # Strip "By Author Name" suffix (common in Reuters, AP, HT articles)
        first_line = re.sub(r'\s*By\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*$', '', first_line)
        # Strip dates, timestamps, "Updated X ago"
        first_line = re.sub(r'\s*(?:Updated|Published)\s+(?:on:?)?.*$', '', first_line, flags=re.IGNORECASE)
        first_line = re.sub(r'\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}.*$', '', first_line, flags=re.IGNORECASE)
        first_line = first_line.strip()[:120]
        
        # Only use if it looks like a headline (not too short, not metadata)
        if len(first_line) > 15 and not first_line.startswith(('http', 'Updated', 'Published', 'By ')):
            queries.append(first_line)
            print(f"[KEYPHRASE] Using first line as headline: '{first_line[:80]}'")

    # 1. Extracted headline (from 'Headline:' prefix in clean_input_text)
    if not queries and headline and len(headline) > 10:
        queries.append(headline[:120])
    
    # 2. Extract named entities (multi-word capitalized phrases)
    proper_nouns = re.findall(
        r'\b([A-Z][a-zA-Z]*(?:\s+(?:of|the|and|in|for|on|at|by|with|from)\s+|\s+)[A-Z][a-zA-Z]*(?:(?:\s+(?:of|the|and|in|for|on|at|by|with|from)\s+|\s+)[A-Z][a-zA-Z]*)*)\b',
        search_text
    )
    # Also find quoted phrases
    quoted = re.findall(r'["\u201c]([^"\u201d]{5,60})["\u201d]', search_text)
    
    # Combine and deduplicate entities, filtering out metadata junk
    metadata_patterns = {
        'AM GMT', 'PM GMT', 'AM IST', 'PM IST', 'GMT Updated', 'IST Updated',
        'HT Correspondent', 'Staff Reporter', 'Special Correspondent',
        'News Desk', 'Web Desk', 'Our Correspondent',
    }
    month_names = {'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December'}
    
    entities = []
    for phrase in proper_nouns + quoted:
        phrase = phrase.strip()
        if len(phrase) < 6:
            continue
        if phrase in entities:
            continue
        # Skip metadata patterns
        if phrase in metadata_patterns:
            continue
        # Skip if starts with "By " (byline)
        if phrase.startswith('By '):
            continue
        # Skip if it's just a month + something
        first_word = phrase.split()[0] if phrase.split() else ''
        if first_word in month_names:
            continue
        # Skip timezone/time patterns
        if re.match(r'^(?:AM|PM|GMT|IST|UTC|EST|PST)\b', phrase):
            continue
        entities.append(phrase)
    
    for entity in entities[:2]:
        if entity not in queries:
            queries.append(entity)
    
    # 3. First sentence fallback
    if not queries:
        first_sentence = search_text.split('.')[0].strip()
        if len(first_sentence) > 100:
            first_sentence = first_sentence[:100]
        if first_sentence and len(first_sentence) > 15:
            queries.append(first_sentence)
    
    # 4. Informal text fallback (WhatsApp/Reddit/Telegram style)
    #    No headline, no proper nouns → extract dense keywords
    if not queries:
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'shall', 'can', 'need', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
            'during', 'before', 'after', 'out', 'off', 'over', 'under', 'again',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'because', 'but', 'and', 'or', 'if', 'while',
            'about', 'up', 'that', 'this', 'these', 'those', 'it', 'its',
            'he', 'she', 'they', 'we', 'you', 'me', 'my', 'your', 'his',
            'her', 'their', 'our', 'said', 'also', 'which', 'who', 'whom',
            'what', 'them', 'him', 'guys', 'like', 'just', 'got', 'did',
            'see', 'get', 'know', 'think', 'say', 'come', 'make', 'going',
            'been', 'https', 'http', 'com', 'www', 'news', 'post', 'reddit',
        }
        words = re.findall(r'\b[a-zA-Z]{3,}\b', search_text.lower())
        keywords = [w for w in words if w not in stop_words]
        # Take top 8 unique keywords
        seen = set()
        unique_kw = []
        for w in keywords:
            if w not in seen:
                seen.add(w)
                unique_kw.append(w)
            if len(unique_kw) >= 8:
                break
        if unique_kw:
            queries.append(' '.join(unique_kw))
    
    # 5. Ultimate fallback
    if not queries:
        queries.append(search_text[:80])

    return queries[:max_phrases]


# ============================================================================
# WEB SEARCH (Three-tier: Bing News → Google News RSS → Google CSE)
# ============================================================================

def search_bing(query: str, max_results: int = 10) -> List[Dict]:
    """
    TIER 1: Scrape Bing search results (free, no API key, reliable).
    Bing is far less aggressive about blocking automated requests than Google.
    Returns titles + snippets for content relevance scoring.
    """
    import requests
    from urllib.parse import quote_plus
    
    url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            print(f"[SEARCH-BING] HTTP {resp.status_code} for '{query[:50]}'")
            return []
        
        html = resp.text
        results = []
        
        # Parse Bing search results from HTML
        # Bing wraps results in <li class="b_algo"> tags
        import re as _re
        # Extract result blocks
        blocks = _re.findall(r'<li class="b_algo">(.*?)</li>', html, _re.DOTALL)
        
        for block in blocks[:max_results]:
            # Extract URL from <a href="...">
            url_match = _re.search(r'<a[^>]+href="(https?://[^"]+)"', block)
            # Extract title from <a>...</a>
            title_match = _re.search(r'<a[^>]+>(.*?)</a>', block, _re.DOTALL)
            # Extract snippet
            snippet_match = _re.search(r'<p[^>]*>(.*?)</p>', block, _re.DOTALL)
            
            if url_match:
                result_url = url_match.group(1)
                # Clean HTML tags from title and snippet
                raw_title = title_match.group(1) if title_match else ''
                raw_snippet = snippet_match.group(1) if snippet_match else ''
                title = _re.sub(r'<[^>]+>', '', raw_title).strip()
                snippet = _re.sub(r'<[^>]+>', '', raw_snippet).strip()
                domain = urlparse(result_url).netloc.replace('www.', '')
                
                results.append({
                    'title': title,
                    'url': result_url,
                    'snippet': snippet,
                    'source': domain
                })
        
        if results:
            print(f"[SEARCH-BING] Got {len(results)} results for '{query[:60]}'")
            for r in results[:3]:
                print(f"  -> {r['source']}: {r['title'][:50]}")
        else:
            print(f"[SEARCH-BING] 0 results parsed for '{query[:60]}'")
        
        return results
    
    except Exception as e:
        print(f"[SEARCH-BING] Error: {e}")
        return []


def search_google_news_rss(query: str, max_results: int = 10) -> List[Dict]:
    """
    TIER 2: Google News RSS feed (free, no API key).
    RSS feeds are designed for machine consumption, less likely to be blocked.
    Best for recent/trending news stories.
    """
    import requests
    import xml.etree.ElementTree as ET
    from urllib.parse import quote_plus
    
    # Try without locale first (global results), then with IN locale
    # US locale was missing many articles that are prominent in other regions
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            print(f"[SEARCH-GNEWS] HTTP {resp.status_code}")
            return []
        
        root = ET.fromstring(resp.content)
        items = root.findall('.//item')
        
        results = []
        for item in items[:max_results]:
            title_el = item.find('title')
            link_el = item.find('link')
            source_el = item.find('source')
            
            if link_el is not None and link_el.text:
                result_url = link_el.text
                title = title_el.text if title_el is not None else ''
                
                # Google News RSS: <source url="https://ndtv.com">NDTV</source>
                # The link is a news.google.com redirect, but source has the real URL
                source_name = ''
                if source_el is not None:
                    source_name = source_el.text or ''
                    # Try to get real URL from source element's url attribute
                    real_source_url = source_el.get('url', '')
                    if real_source_url:
                        domain = urlparse(real_source_url).netloc.replace('www.', '')
                    else:
                        domain = urlparse(result_url).netloc.replace('www.', '')
                else:
                    domain = urlparse(result_url).netloc.replace('www.', '')
                
                results.append({
                    'title': title or '',
                    'url': result_url,
                    'snippet': f'Source: {source_name}' if source_name else '',
                    'source': domain
                })
        
        if results:
            print(f"[SEARCH-GNEWS] Got {len(results)} results for '{query[:60]}'")
        else:
            print(f"[SEARCH-GNEWS] 0 results for '{query[:60]}'")
        
        return results
    
    except Exception as e:
        print(f"[SEARCH-GNEWS] Error: {e}")
        return []


def search_google_custom(query: str, max_results: int = 10) -> List[Dict]:
    """
    TIER 3: Google Custom Search API (100 free queries/day).
    Only called when Bing and Google News RSS both fail.
    Requires GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX in settings.py.
    """
    api_key = getattr(settings, 'GOOGLE_CSE_API_KEY', '')
    cx = getattr(settings, 'GOOGLE_CSE_CX', '')
    
    if not api_key or not cx:
        print("[SEARCH-CSE] Not configured (no API key/CX). Skipping.")
        return []
    
    try:
        from googleapiclient.discovery import build
        
        service = build('customsearch', 'v1', developerKey=api_key)
        response = service.cse().list(
            q=query,
            cx=cx,
            num=min(max_results, 10)
        ).execute()
        
        items = response.get('items', [])
        results = []
        for item in items:
            url = item.get('link', '')
            results.append({
                'title': item.get('title', ''),
                'url': url,
                'snippet': item.get('snippet', ''),
                'source': urlparse(url).netloc.replace('www.', '')
            })
        
        print(f"[SEARCH-CSE] Got {len(results)} results for '{query[:60]}'")
        return results
    
    except Exception as e:
        print(f"[SEARCH-CSE] Error: {e}")
        return []


def search_web(query: str, max_results: int = 10) -> List[Dict]:
    """
    Three-tier search: Google News RSS → Bing → Google Custom Search API.
    Returns list of {title, url, snippet, source} dicts.
    """
    # Tier 1: Google News RSS (most reliable for news, free, no blocking)
    results = search_google_news_rss(query, max_results)
    if results:
        return results
    
    print(f"[SEARCH] Tier 1 (Google News RSS) returned 0 results. Trying Tier 2 (Bing)...")
    
    # Tier 2: Bing web search (broader coverage)
    results = search_bing(query, max_results)
    if results:
        return results
    
    print(f"[SEARCH] Tier 2 (Bing) returned 0 results. Trying Tier 3 (Custom Search API)...")
    
    # Tier 3: Google Custom Search API (100/day free)
    results = search_google_custom(query, max_results)
    if results:
        return results
    
    print(f"[SEARCH] All 3 tiers returned 0 results for '{query[:50]}'")
    return []


# ============================================================================
# DOMAIN UTILITIES
# ============================================================================

def get_domain(url: str) -> str:
    """Extract clean domain from URL."""
    try:
        return urlparse(url).netloc.replace('www.', '').lower()
    except Exception:
        return ''


def is_trusted_domain(url: str) -> bool:
    """Check if a URL belongs to a trusted news domain."""
    domain = get_domain(url)
    if not domain:
        return False
    trusted_domains = getattr(settings, 'TRUSTED_NEWS_DOMAINS', [])
    return any(
        trusted in domain or domain in trusted
        for trusted in (d.lower() for d in trusted_domains)
    )


# ============================================================================
# 3 MEASURABLE SIGNALS (formula-based, no hardcoded scores)
# ============================================================================

def signal_coverage_density(total_results: int) -> float:
    """
    SIGNAL 1: Coverage Density (0.0 - 1.0)
    
    Measures: How widely is this story covered on the internet?
    
    Logic: If a news story is real, multiple sources will cover it.
    Zero coverage is a strong indicator of fabrication.
    
    Formula: sigmoid(total_results, midpoint=5, steepness=0.6)
    - 0 results → ~0.05 (near zero - nobody is covering this)
    - 2 results → ~0.15
    - 5 results → ~0.50 (midpoint)
    - 10 results → ~0.95 (well-covered)
    
    Uses sigmoid instead of linear because:
    - Going from 0→2 results is a BIG jump (0 = likely fabricated)
    - Going from 10→20 results is small (already well-covered)
    """
    midpoint = 5
    steepness = 0.6
    score = 1.0 / (1.0 + math.exp(-steepness * (total_results - midpoint)))
    return round(score, 4)


def signal_trusted_ratio(trusted_count: int, total_results: int) -> float:
    """
    SIGNAL 2: Trusted Source Ratio (0.0 - 1.0)
    
    Measures: What fraction of search results come from verified news outlets?
    
    Logic: Real news gets picked up by Reuters, BBC, NDTV, etc.
    Fake news only appears on unknown or unreliable sites.
    
    Formula: trusted_count / max(total_results, 1)
    With a boost for having ANY trusted source (the first trusted match
    is worth more than the second, because it demonstrates credibility).
    
    - 0 trusted out of 10 → 0.0 (no credible outlets covering it)
    - 1 trusted out of 10 → 0.10 base + 0.15 first-match bonus = 0.25
    - 3 trusted out of 10 → 0.30 base + 0.15 bonus = 0.45
    - 5 trusted out of 10 → 0.50 base + 0.15 bonus = 0.65
    """
    if total_results == 0:
        return 0.0  # No results at all, can't calculate ratio
    
    base_ratio = trusted_count / total_results
    
    # First-match bonus: having at least ONE trusted source is significant
    first_match_bonus = 0.15 if trusted_count > 0 else 0.0
    
    return min(1.0, round(base_ratio + first_match_bonus, 4))


def signal_content_relevance(input_text: str, search_results: List[Dict]) -> float:
    """
    SIGNAL 3: Content Relevance (0.0 - 1.0)
    
    Measures: Are the search results actually about the SAME topic?
    
    Logic: Searching for fake names/events returns unrelated results.
    Searching for real events returns results about that exact topic.
    
    Formula: Overlap Coefficient between input keywords and result keywords.
    
    Overlap(A, B) = |A ∩ B| / min(|A|, |B|)
    
    Why Overlap instead of Jaccard:
    Jaccard divides by the UNION, which is dominated by the larger set.
    A 2000-word article vs a 20-word snippet → union is ~200 keywords,
    even if most snippet words appear in the article, Jaccard ≈ 0.05.
    Overlap Coefficient correctly asks: "what fraction of the SMALLER 
    set's keywords appear in the larger set?" → much more meaningful.
    
    - Completely unrelated results → ~0.0
    - Somewhat related results → ~0.3-0.5
    - Highly relevant results → ~0.6-0.9
    """
    if not search_results:
        return 0.0

    input_keywords = extract_keywords(input_text)
    if not input_keywords:
        return 0.0

    similarities = []
    for result in search_results:
        # Combine title + snippet for comparison
        result_text = f"{result.get('title', '')} {result.get('snippet', '')}"
        result_keywords = extract_keywords(result_text)

        if not result_keywords:
            similarities.append(0.0)
            continue

        # Overlap Coefficient: |intersection| / min(|A|, |B|)
        intersection = input_keywords & result_keywords
        min_size = min(len(input_keywords), len(result_keywords))
        overlap = len(intersection) / min_size if min_size > 0 else 0.0
        similarities.append(overlap)

    # Average similarity across all results
    avg_similarity = sum(similarities) / len(similarities)
    return round(avg_similarity, 4)


# ============================================================================
# SCORE CALCULATION (combining the 3 signals)
# ============================================================================

def calculate_source_score(
    total_results: int,
    trusted_count: int,
    input_text: str,
    search_results: List[Dict],
    source_url: str = None
) -> Dict:
    """
    Calculate source verification score from 3 measurable signals.
    
    Final Score = (coverage × 0.35) + (trust_ratio × 0.40) + (relevance × 0.25)
    
    Weights rationale:
    - Trust ratio (40%): Most important - ARE credible outlets reporting this?
    - Coverage density (35%): If nobody covers it, it's likely fabricated
    - Content relevance (25%): Ensures results are about the same topic
    
    If the input URL is from a trusted domain, apply a bonus since
    the article originates from a verified source.
    """
    # Calculate each signal
    coverage = signal_coverage_density(total_results)
    trust_ratio = signal_trusted_ratio(trusted_count, total_results)
    relevance = signal_content_relevance(input_text, search_results)

    # URL Input Override: When the user provides a URL and we KNOW the source
    # domain is trusted, the Trusted Source Ratio should be 1.0.
    # Rationale: The search-based ratio measures what fraction of random search
    # results happen to be from trusted outlets — but when the article itself
    # is FROM a trusted outlet (e.g., Times of India, Reuters), the source
    # trustworthiness is already established. There's only one source for that
    # specific article URL, and it IS trusted → ratio = 1.0.
    input_is_trusted = False
    if source_url and is_trusted_domain(source_url):
        input_is_trusted = True
        trust_ratio = 1.0
        print(f"[SOURCE VERIFY] Input URL ({get_domain(source_url)}) is a trusted source -> Trusted Ratio overridden to 1.0")

    print(f"[SOURCE VERIFY] Signal 1 - Coverage Density: {coverage:.4f} ({total_results} results)")
    print(f"[SOURCE VERIFY] Signal 2 - Trusted Ratio: {trust_ratio:.4f} ({trusted_count}/{total_results} from search, {'overridden' if input_is_trusted else 'as-is'})")
    print(f"[SOURCE VERIFY] Signal 3 - Content Relevance: {relevance:.4f}")

    # Weighted combination
    w_coverage = 0.35
    w_trust = 0.40
    w_relevance = 0.25

    # CRITICAL: Content Relevance Gating
    # When search results are NOT about the same topic (relevance < 0.3),
    # coverage and trust ratio are MEANINGLESS — they measure "we found
    # articles from trusted domains" not "we found THIS STORY on trusted domains".
    # This catches sophisticated fakes that reference real events/entities.
    if relevance < 0.3 and not input_is_trusted:
        # Scale coverage and trust down by relevance — they're unreliable
        penalty = relevance / 0.3  # 0.0 to 1.0 scale
        effective_coverage = coverage * penalty
        effective_trust = trust_ratio * penalty
        source_score = (effective_coverage * w_coverage) + (effective_trust * w_trust) + (relevance * w_relevance)
        print(f"[SOURCE VERIFY] [!] Low content relevance ({relevance:.2f}) -- penalizing coverage/trust by {penalty:.2f}")
    else:
        source_score = (coverage * w_coverage) + (trust_ratio * w_trust) + (relevance * w_relevance)

    # Trusted source floor: If the article is FROM a trusted outlet, don't let
    # a bad search (rate limiting, few results, etc.) tank the score.
    # The source's credibility is already established — minimum 75%.
    if input_is_trusted:
        source_score = max(source_score, 0.75)
        print(f"[SOURCE VERIFY] Trusted source floor applied: source_score >= 0.75")

    source_score = max(0.0, min(1.0, round(source_score, 4)))
    print(f"[SOURCE VERIFY] Final source score: {source_score:.4f}")

    return {
        'source_score': source_score,
        'signal_coverage': coverage,
        'signal_trust_ratio': trust_ratio,
        'signal_relevance': relevance,
        'input_is_trusted': input_is_trusted,
    }


# ============================================================================
# TRUSTED SOURCE ANALYSIS
# ============================================================================

def check_trusted_sources(search_results: List[Dict]) -> Dict:
    """Analyze search results to find matches from trusted news sources."""
    trusted_domains = getattr(settings, 'TRUSTED_NEWS_DOMAINS', [])
    trusted_set = set(d.lower() for d in trusted_domains)

    trusted_matches = []
    all_sources = []

    for result in search_results:
        source_domain = result.get('source', '').lower()
        all_sources.append(source_domain)

        is_trusted = any(
            trusted in source_domain or source_domain in trusted
            for trusted in trusted_set
        )

        if is_trusted:
            trusted_matches.append({
                'name': result.get('title', ''),
                'url': result.get('url', ''),
                'domain': source_domain,
                'snippet': result.get('snippet', '')[:200]
            })

    return {
        'trusted_matches': trusted_matches,
        'trusted_count': len(trusted_matches),
        'total_results': len(search_results),
        'all_sources': list(set(all_sources))
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def _detect_url_in_text(text: str) -> str:
    """
    Detect if the user pasted a URL within their text input.
    Common pattern: users paste article text + the source URL at the bottom.
    Returns the first URL found, or None.
    """
    url_pattern = r'https?://[^\s<>"\')]+'
    urls = re.findall(url_pattern, text)
    for url in urls:
        # Only consider URLs that look like news article links (not image URLs, etc.)
        if any(ext in url.lower() for ext in ['.jpg', '.png', '.gif', '.svg', '.css', '.js']):
            continue
        return url
    return None


def verify_with_sources(text: str, source_url: str = None) -> Dict:
    """
    Verify a piece of text by searching trusted sources.
    Returns all 3 signal scores + combined source score.
    Includes search_insufficient flag when search engines fail/rate-limit.
    """
    try:
        # Auto-detect URL in text input if no source_url was explicitly provided
        if not source_url:
            detected_url = _detect_url_in_text(text)
            if detected_url:
                source_url = detected_url
                print(f"[SOURCE VERIFY] Auto-detected URL in text: {source_url}")

        # Step 1: Extract search queries
        queries = extract_key_phrases(text)
        print(f"[SOURCE VERIFY] Search queries: {queries}")

        # Step 2: Search the web (with delay between queries to avoid rate limiting)
        all_results = []
        seen_urls = set()
        for i, query in enumerate(queries):
            if i > 0:
                time.sleep(2.0)  # Longer delay between queries
            results = search_web(query)
            for r in results:
                if r['url'] not in seen_urls:
                    seen_urls.add(r['url'])
                    all_results.append(r)

        print(f"[SOURCE VERIFY] Found {len(all_results)} unique results")

        # CRITICAL: Detect search failure vs genuine lack of coverage
        # If search returned <3 results, it's likely a search failure,
        # NOT evidence that the story isn't covered.
        search_insufficient = len(all_results) < 3
        if search_insufficient:
            print(f"[SOURCE VERIFY] [!] SEARCH INSUFFICIENT: Only {len(all_results)} results. "
                  f"Search engines may be rate-limited. Source score will be marked unreliable.")

        # Step 3: Identify trusted sources
        trusted_analysis = check_trusted_sources(all_results)
        print(f"[SOURCE VERIFY] Trusted sources: {trusted_analysis['trusted_count']}")

        # Step 4: Calculate source score from 3 signals
        score_result = calculate_source_score(
            total_results=trusted_analysis['total_results'],
            trusted_count=trusted_analysis['trusted_count'],
            input_text=text,
            search_results=all_results,
            source_url=source_url,
        )

        return {
            'source_score': score_result['source_score'],
            # Individual signals for frontend display
            'signal_coverage': score_result['signal_coverage'],
            'signal_trust_ratio': score_result['signal_trust_ratio'],
            'signal_relevance': score_result['signal_relevance'],
            'input_is_trusted': score_result['input_is_trusted'],
            # Search reliability flag
            'search_insufficient': search_insufficient,
            # Source details
            'trusted_count': trusted_analysis['trusted_count'],
            'trusted_sources': trusted_analysis['trusted_matches'][:5],
            'total_results': trusted_analysis['total_results'],
            'search_queries': queries,
            'all_sources': trusted_analysis['all_sources'][:10],
        }

    except Exception as e:
        print(f"[ERROR] Source verification failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'source_score': 0.5,
            'signal_coverage': 0.5,
            'signal_trust_ratio': 0.0,
            'signal_relevance': 0.0,
            'input_is_trusted': False,
            'search_insufficient': True,  # Treat errors as insufficient
            'trusted_count': 0,
            'trusted_sources': [],
            'total_results': 0,
            'search_queries': [],
            'all_sources': [],
            'error': str(e)
        }


# ============================================================================
# SCORE COMBINATION (ML + Source)
# ============================================================================

def combine_scores(ml_probability: float, source_score: float, history_signal: Dict = None, search_insufficient: bool = False, trusted_count: int = 0, content_relevance: float = 0.5, word_count: int = 999) -> Dict:
    """
    Combine ML prediction with source verification score and optional
    historical feedback signal.
    
    Strategy:
    - Base: weighted average (ML × 0.4) + (Source × 0.6)
    - SHORT TEXT PROTECTION: For headlines (<150 words), ML models are
      unreliable. Shift to source-heavy weights (ML × 0.15, Source × 0.85)
    - Agreement boost: if both agree, boost confidence
    - Disagreement handling: if they strongly disagree, trust source more
    - STRONG SOURCE OVERRIDE: if 5+ trusted sources confirm the story,
      ML cannot drag the score below 0.55 (the story is almost certainly real)
    - SEARCH FAILURE PROTECTION: if search returned <3 results, the source
      score is unreliable. Fall back to ML-heavy weighting instead of
      letting a failed search tank a correct ML prediction.
    - History blending: if similar articles were seen before, blend their verdict
    """
    ml_weight = getattr(settings, 'ML_SCORE_WEIGHT', 0.4)
    source_weight = getattr(settings, 'SOURCE_SCORE_WEIGHT', 0.6)
    
    short_text_threshold = getattr(settings, 'SHORT_TEXT_THRESHOLD', 150)
    is_short_text = word_count < short_text_threshold

    # SHORT TEXT PROTECTION
    # ML models trained on articles produce near-random scores for headlines.
    # Even headline-specific models are less reliable than source verification
    # for short inputs. Trust source verification much more for short text.
    if is_short_text and not search_insufficient:
        ml_weight = 0.15
        source_weight = 0.85
        print(f"[COMBINE] Short text detected ({word_count} words < {short_text_threshold}) "
              f"-- using source-heavy weights: ML={ml_weight}, Source={source_weight}")

    # CRITICAL: Search failure protection
    # When search engines rate-limit and return 0-2 results, the source score
    # is meaningless (it's measuring "search availability", not "story coverage").
    # In this case, trust ML much more and treat source as merely supplementary.
    if search_insufficient:
        ml_weight = 0.85
        source_weight = 0.15
        # Also set source_score to a neutral 0.5 instead of the near-zero
        # value that a failed search produces
        source_score = max(source_score, 0.5)
        print(f"[COMBINE] [!] Search insufficient -- using ML-heavy weights: "
              f"ML={ml_weight}, Source={source_weight}, source_score adjusted to {source_score:.2f}")

    # Disagreement detection (only meaningful if search was successful)
    disagreement = abs(ml_probability - source_score)
    
    if not search_insufficient and disagreement > 0.5:
        shift = (disagreement - 0.5) * 0.4
        adjusted_ml_weight = max(0.15, ml_weight - shift)
        adjusted_source_weight = min(0.85, source_weight + shift)
        combined = (ml_probability * adjusted_ml_weight) + (source_score * adjusted_source_weight)
        print(f"[COMBINE] Disagreement detected ({disagreement:.2f}). "
              f"Adjusted weights: ML={adjusted_ml_weight:.2f}, Source={adjusted_source_weight:.2f}")
    else:
        combined = (ml_probability * ml_weight) + (source_score * source_weight)

    # Agreement boost (only when search was successful)
    if not search_insufficient:
        if ml_probability > 0.7 and source_score > 0.6:
            combined = min(1.0, combined + 0.08)
        elif ml_probability < 0.3 and source_score < 0.4:
            combined = max(0.0, combined - 0.08)

    # STRONG SOURCE EVIDENCE OVERRIDE
    # When 5+ trusted news outlets independently report the same story,
    # the story is almost certainly real. The ML model should not be able
    # to override this strong evidence from the real world.
    # For short text (headlines), content_relevance is naturally lower since
    # there's less text to match against, so we use a lower threshold.
    relevance_threshold = 0.2 if is_short_text else 0.4
    if not search_insufficient and trusted_count >= 5 and content_relevance > relevance_threshold:
        floor = 0.55  # At least "Likely TRUE"
        if trusted_count >= 8:
            floor = 0.65  # Strong "Likely TRUE"
        if trusted_count >= 12:
            floor = 0.75  # "High confidence TRUE"
        
        if combined < floor:
            print(f"[COMBINE] [OVERRIDE] Strong source override: {trusted_count} trusted sources, "
                  f"relevance={content_relevance:.2f} (threshold={relevance_threshold}). Raising score from {combined:.2f} to {floor:.2f}")
            combined = floor
    elif not search_insufficient and trusted_count >= 5 and content_relevance <= relevance_threshold:
        print(f"[COMBINE] [!] Strong source override BLOCKED: {trusted_count} trusted sources found, "
              f"but content_relevance={content_relevance:.2f} too low (threshold={relevance_threshold})")

    # History blending: if we've seen similar articles before, use that knowledge
    history_applied = False
    if history_signal and history_signal.get('has_history', False):
        history_score = history_signal['history_score']
        history_confidence = history_signal['confidence']
        
        if history_confidence > 0.1:  # Only apply if we have meaningful confidence
            # Blend: the higher the confidence, the more we trust history
            # history_influence ranges from 0 to 0.25 based on confidence
            history_influence = min(0.25, history_confidence * 0.3)
            combined = (combined * (1 - history_influence)) + (history_score * history_influence)
            history_applied = True
            print(f"[COMBINE] History blended: score={history_score:.4f}, "
                  f"confidence={history_confidence:.4f}, influence={history_influence:.4f}")

    # Re-apply strong source override AFTER history blending as the final floor.
    # History from previous incorrect predictions should not override real-world
    # evidence from 5+ trusted news outlets confirming a story RIGHT NOW.
    if not search_insufficient and trusted_count >= 5 and content_relevance > relevance_threshold:
        if combined < floor:
            print(f"[COMBINE] [OVERRIDE] Re-applying source floor after history: "
                  f"raising {combined:.2f} back to {floor:.2f}")
            combined = floor

    combined = max(0.0, min(1.0, combined))

    # Confidence levels
    if combined < 0.3:
        confidence_level = 'High'
        confidence_label = 'High confidence FAKE'
    elif combined < 0.45:
        confidence_level = 'Moderate'
        confidence_label = 'Likely FAKE'
    elif combined < 0.55:
        confidence_level = 'Low'
        confidence_label = 'Uncertain - Cannot determine'
    elif combined < 0.7:
        confidence_level = 'Moderate'
        confidence_label = 'Likely TRUE'
    else:
        confidence_level = 'High'
        confidence_label = 'High confidence TRUE'

    return {
        'combined_probability': round(combined, 4),
        'trueness_probability': round(combined * 100, 2),
        'confidence_level': confidence_level,
        'confidence_label': confidence_label,
        'ml_score': round(ml_probability, 4),
        'source_score': round(source_score, 4),
        'ml_weight': ml_weight,
        'source_weight': source_weight,
        'history_applied': history_applied,
        'search_insufficient': search_insufficient,
    }

