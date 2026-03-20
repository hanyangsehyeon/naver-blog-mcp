"""Find QR button selector on Naver login page"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://nid.naver.com/nidlogin.login")
time.sleep(2)

driver.save_screenshot("/Users/sehyun/Documents/GitHub/naver-blog-mcp/tests/login_page.png")

# Print all buttons and links on the page
elems = driver.find_elements(By.CSS_SELECTOR, "a, button")
for e in elems:
    txt = e.text.strip()
    cls = e.get_attribute("class")
    id_ = e.get_attribute("id")
    href = e.get_attribute("href")
    if txt or id_:
        print(f"tag={e.tag_name} id='{id_}' class='{cls}' text='{txt}' href='{href}'")

driver.quit()
