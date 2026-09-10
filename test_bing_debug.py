"""Debug: Save Bing HTML to see what we're actually parsing"""
import requests
from urllib.parse import quote_plus

query = "PM Modi inaugurates new Prime Minister Office Seva Teerth"
url = f"https://www.bing.com/search?q={quote_plus(query)}&count=10"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

print(f"Fetching Bing for: '{query}'")
resp = requests.get(url, headers=headers, timeout=10)
print(f"HTTP Status: {resp.status_code}")
print(f"Response length: {len(resp.text)} chars")

# Save HTML for inspection
with open("bing_debug.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("Saved to bing_debug.html")

# Try to find what class Bing actually uses for results
import re
# Look for common result patterns
li_classes = re.findall(r'<li class="([^"]*)"', resp.text)
print(f"\nAll <li> classes found: {set(li_classes)}")

# Check for b_algo specifically
algo_count = resp.text.count('b_algo')
print(f"'b_algo' occurrences: {algo_count}")

# Try alternative patterns
ol_results = re.findall(r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>', resp.text, re.DOTALL)
print(f"b_algo results: {len(ol_results)}")

# Check if it's a redirect/captcha page
if 'captcha' in resp.text.lower() or 'blocked' in resp.text.lower():
    print("\n⚠ CAPTCHA/BLOCK DETECTED")
elif len(resp.text) < 5000:
    print(f"\n⚠ Suspiciously short response ({len(resp.text)} chars)")
    print(resp.text[:1000])
