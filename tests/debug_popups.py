"""Debug: find selectors for both popups"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.common import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

driver = make_driver(headless=False)
login_with_qr(driver)

driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".se-text-paragraph"))
)
time.sleep(2)

soup = BeautifulSoup(driver.page_source, "lxml")

# Find "작성 중인 글" dialog
print("\n=== '작성 중인 글' dialog ===")
for el in soup.find_all(string=lambda t: t and "작성 중인 글" in t):
    parent = el.parent
    print(f"  tag={parent.name} class='{parent.get('class')}' id='{parent.get('id')}'")

# Find confirm/cancel buttons
print("\n=== Dialog buttons ===")
for el in soup.find_all("button"):
    txt = el.get_text(strip=True)
    if txt in ["확인", "취소", "확 인", "취 소"]:
        print(f"  text='{txt}' class='{el.get('class')}' id='{el.get('id')}'")

# Find 도움말 panel close button
print("\n=== '도움말' panel ===")
for el in soup.find_all(string=lambda t: t and "도움말" in t):
    parent = el.parent
    print(f"  tag={parent.name} class='{parent.get('class')}' id='{parent.get('id')}'")

print("\n=== All visible buttons/close elements ===")
for el in soup.find_all(["button", "a"]):
    cls = " ".join(el.get("class", []))
    if any(k in cls.lower() for k in ["close", "cancel", "confirm", "help"]):
        print(f"  tag={el.name} class='{cls}' id='{el.get('id')}' text='{el.get_text(strip=True)[:30]}'")

driver.quit()
