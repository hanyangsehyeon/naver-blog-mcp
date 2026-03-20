"""Debug: input via input_buffer iframe"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.common import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip

driver = make_driver(headless=False)
login_with_qr(driver)

driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".se-text-paragraph"))
)
time.sleep(2)

# Step 1: Click the paragraph area to activate editor
para = driver.find_element(By.CSS_SELECTOR, ".se-text-paragraph")
ActionChains(driver).move_to_element(para).click().perform()
time.sleep(0.5)

# Step 2: Switch to input_buffer iframe
iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
print(f"iframe id: {iframe.get_attribute('id')}")
driver.switch_to.frame(iframe)
time.sleep(0.3)

# Step 3: Find contenteditable inside iframe
els = driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true'], body")
print(f"Elements inside iframe: {len(els)}")
for e in els:
    print(f"  tag={e.tag_name} class='{e.get_attribute('class')}' ce='{e.get_attribute('contenteditable')}'")

# Step 4: Try send_keys on body of iframe
print("\n=== send_keys on iframe body ===")
try:
    body = driver.find_element(By.TAG_NAME, "body")
    body.send_keys("hello test")
    time.sleep(0.5)
    print(f"page_source snippet: {driver.page_source[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Switch back and check main page
driver.switch_to.default_content()
time.sleep(0.5)
print(f"\n'hello test' in main page_source: {'hello test' in driver.page_source}")

# Check paragraph text via JS
paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
print(f"\nParagraph texts:")
for p in paras:
    print(f"  '{p.text}'")

driver.save_screenshot("tests/editor_state3.png")
driver.quit()
