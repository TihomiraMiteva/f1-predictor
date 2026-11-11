import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

url = "https://gpracingstats.com/seasons/2025-world-championship/"

# 1) Configure Chrome
options = Options()
# Comment this line if you want to actually SEE the browser
# options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

# 2) Start browser
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

try:
    # 3) Open the page
    driver.get(url)
    time.sleep(5)  # simple wait; can be replaced with WebDriverWait

    # 4) Get the fully loaded HTML
    html = driver.page_source

finally:
    driver.quit()

# 5) Let pandas parse all tables from the HTML
tables = pd.read_html(html)
print(f"Found {len(tables)} tables.")

for i, t in enumerate(tables):
    print(f"\n=== TABLE {i} ===")
    print(t.head())

# Example: assume table 0 is the calendar
if tables:
    calendar_df = tables[0]
    calendar_df.to_csv("f1_2025_calendar.csv", index=False)
    print("\nSaved f1_2025_calendar.csv")
