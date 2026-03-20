"""Debug: screenshot login page state after submit"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
NAVER_ID = os.getenv("NAVER_ID")
NAVER_PW = os.getenv("NAVER_PW")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://nid.naver.com/nidlogin.login")
time.sleep(2)

id_field = driver.find_element(By.ID, "id")
pw_field = driver.find_element(By.ID, "pw")
id_field.click(); id_field.clear(); id_field.send_keys(NAVER_ID)
time.sleep(0.5)
pw_field.click(); pw_field.clear(); pw_field.send_keys(NAVER_PW)
time.sleep(0.5)

btn = driver.find_element(By.ID, "log.login")
btn.click()
time.sleep(3)

out = "/Users/sehyun/Documents/GitHub/naver-blog-mcp/tests/login_state.png"
driver.save_screenshot(out)
print(f"URL: {driver.current_url}")
print(f"Screenshot: {out}")

# Print any visible error text
try:
    errors = driver.find_elements(By.CSS_SELECTOR, ".error_msg, .error, #err_common, .msg")
    for e in errors:
        if e.text:
            print(f"Error element: {e.text}")
except:
    pass

driver.quit()
