"""Quick test: Does Bing search return results?"""
import requests
from urllib.parse import quote_plus
import re

query = "House passes Save America Act"
url = f"https://www.bing.com/search?q={quote_plus(query)}&count=10"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

print(f"Searching Bing for: '{query}'")
resp = requests.get(url, headers=headers, timeout=10)
print(f"HTTP Status: {resp.status_code}")

# Parse Bing results
blocks = re.findall(r'<li class="b_algo">(.*?)</li>', resp.text, re.DOTALL)
print(f"Found {len(blocks)} result blocks\n")

for i, block in enumerate(blocks[:5]):
    url_match = re.search(r'<a[^>]+href="(https?://[^"]+)"', block)
    title_match = re.search(r'<a[^>]+>(.*?)</a>', block, re.DOTALL)
    
    if url_match:
        result_url = url_match.group(1)
        raw_title = title_match.group(1) if title_match else ''
        title = re.sub(r'<[^>]+>', '', raw_title).strip()
        print(f"  [{i+1}] {title[:80]}")
        print(f"      {result_url}\n")
