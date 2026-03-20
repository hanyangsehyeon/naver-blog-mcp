"""Debug: inspect mainFrame iframe contents on blog main page"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.common import *
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

driver = make_driver(headless=False)
login_with_qr(driver)

driver.get(f"https://blog.naver.com/{BLOG_ID}")
time.sleep(2)

iframe = driver.find_element(By.ID, "mainFrame")
driver.switch_to.frame(iframe)
time.sleep(2)

print(f"\nURL inside iframe: {driver.current_url}")

soup = BeautifulSoup(driver.page_source, "lxml")

print("\n=== All <a> tags (first 30) ===")
for a in soup.find_all("a", href=True)[:30]:
    print(f"  href='{a['href']}' text='{a.text.strip()[:40]}'")

print("\n=== page_source snippet (first 3000 chars) ===")
print(driver.page_source[:3000])

driver.quit()
