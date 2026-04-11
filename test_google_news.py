"""Quick test: Does Google News RSS return results?"""
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

query = "House passes Save America Act"
url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"

print(f"Fetching: {url}")
r = requests.get(url, timeout=10)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    root = ET.fromstring(r.content)
    items = root.findall('.//item')
    print(f"Found {len(items)} results\n")
    for item in items[:5]:
        title = item.find('title').text if item.find('title') is not None else 'N/A'
        link = item.find('link').text if item.find('link') is not None else 'N/A'
        source = item.find('source').text if item.find('source') is not None else 'N/A'
        print(f"  [{source}] {title}")
        print(f"    {link}\n")
else:
    print(f"Failed: {r.text[:500]}")
