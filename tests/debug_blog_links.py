"""Debug: find post link structure on blog main page"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.common import *
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

driver = make_driver(headless=False)
login_with_qr(driver)

driver.get(f"https://blog.naver.com/{BLOG_ID}")
time.sleep(2)

# Save screenshot
driver.save_screenshot("tests/blog_main.png")

# Print all <a> tags with href
soup = BeautifulSoup(driver.page_source, "lxml")
print("\n=== All <a> hrefs containing BLOG_ID or post numbers ===")
for a in soup.find_all("a", href=True):
    href = a["href"]
    if BLOG_ID in href or (href.split("/")[-1].isdigit() and len(href.split("/")[-1]) > 5):
        print(f"  href='{href}' class='{a.get('class')}' text='{a.text.strip()[:40]}'")

# Also check if blog is inside an iframe
print("\n=== iframes on page ===")
for f in soup.find_all("iframe"):
    print(f"  id='{f.get('id')}' src='{f.get('src')}'")

driver.quit()
