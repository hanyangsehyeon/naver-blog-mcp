"""Debug: find post links deeper in iframe, with longer wait"""
import sys, os, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.common import *
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

driver = make_driver(headless=False)
login_with_qr(driver)

driver.get(f"https://blog.naver.com/{BLOG_ID}")
time.sleep(3)  # wait longer for JS

iframe = driver.find_element(By.ID, "mainFrame")
driver.switch_to.frame(iframe)
time.sleep(3)

soup = BeautifulSoup(driver.page_source, "lxml")

# Find all links with numeric IDs (post URLs)
print("\n=== Links with numeric post IDs ===")
found = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if re.search(r'/\d{8,}', href):
        print(f"  href='{href}' text='{a.text.strip()[:40]}'")
        found.append(href)

print(f"\nTotal: {len(found)}")

if not found:
    print("\n=== All unique hrefs (to find pattern) ===")
    hrefs = list(dict.fromkeys(a["href"] for a in soup.find_all("a", href=True)))
    for h in hrefs:
        print(f"  {h}")

driver.quit()
