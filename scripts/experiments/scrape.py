import requests
import pandas as pd

url = "https://gpracingstats.com/seasons/2025-world-championship/"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

response = requests.get(url, headers=headers)
print("Status:", response.status_code)

html = response.text  # even if 403, you'll still get the body

if response.status_code != 200:
    print("Server said no (", response.status_code, ")")
    print(html[:500])  # see what the page says
    raise SystemExit()

tables = pd.read_html(html)
print(f"Found {len(tables)} tables")
print(tables[0].head())
