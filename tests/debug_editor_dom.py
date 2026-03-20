"""Debug: inspect Smart Editor ONE DOM structure on write page"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.common import *
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

driver = make_driver(headless=False)
login_with_qr(driver)

driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
time.sleep(4)  # wait for editor to fully load

driver.save_screenshot("tests/editor_page.png")

soup = BeautifulSoup(driver.page_source, "lxml")

# Find title-related elements
print("\n=== Title candidates ===")
for el in soup.find_all(["input", "textarea", "div"], limit=200):
    placeholder = el.get("placeholder", "")
    cls = " ".join(el.get("class", []))
    id_ = el.get("id", "")
    ce = el.get("contenteditable", "")
    if any(k in (placeholder + cls + id_).lower() for k in ["title", "제목", "타이틀"]):
        print(f"  tag={el.name} id='{id_}' class='{cls}' placeholder='{placeholder}' contenteditable='{ce}'")

# Find contenteditable elements
print("\n=== contenteditable elements ===")
for el in soup.find_all(attrs={"contenteditable": True}):
    cls = " ".join(el.get("class", []))
    id_ = el.get("id", "")
    print(f"  tag={el.name} id='{id_}' class='{cls}' ce='{el.get('contenteditable')}'")

# Find iframes
print("\n=== iframes ===")
for f in soup.find_all("iframe"):
    print(f"  id='{f.get('id')}' class='{f.get('class')}' name='{f.get('name')}' src='{str(f.get('src',''))[:80]}'")

driver.quit()
