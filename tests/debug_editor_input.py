"""Debug: check actual state of editor after clipboard paste and Enter"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.common import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip
from bs4 import BeautifulSoup

driver = make_driver(headless=False)
login_with_qr(driver)

driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
)
time.sleep(1)

def focus_body():
    el = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
    driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].focus(); arguments[0].click();", el)
    time.sleep(0.3)
    return el

# Test 1: send_keys
print("\n=== Test 1: send_keys ===")
el = focus_body()
el.send_keys("send_keys line 1")
time.sleep(0.5)
print(f"In page_source: {'send_keys line 1' in driver.page_source}")

# Test 2: clipboard paste
print("\n=== Test 2: clipboard paste ===")
el = focus_body()
el.send_keys(Keys.END, Keys.RETURN)
time.sleep(0.3)
pyperclip.copy("clipboard line 2")
el = focus_body()
ActionChains(driver).key_down(Keys.COMMAND).send_keys("v").key_up(Keys.COMMAND).perform()
time.sleep(1.0)
print(f"In page_source: {'clipboard line 2' in driver.page_source}")

# Test 3: execCommand
print("\n=== Test 3: execCommand ===")
el = focus_body()
el.send_keys(Keys.END, Keys.RETURN)
time.sleep(0.3)
driver.execute_script("document.execCommand('insertText', false, 'execCommand line 3')")
time.sleep(0.5)
print(f"In page_source: {'execCommand line 3' in driver.page_source}")

# Check paragraph structure
print("\n=== Paragraph structure ===")
soup = BeautifulSoup(driver.page_source, "lxml")
paras = soup.select(".se-text-paragraph")
print(f"Total .se-text-paragraph: {len(paras)}")
for i, p in enumerate(paras):
    print(f"  [{i}] '{p.get_text()[:80]}'")

# Check what Enter actually creates
print("\n=== Testing Enter key paragraph creation ===")
el = focus_body()
el.send_keys(Keys.END)
before = len(driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph"))
el.send_keys(Keys.RETURN)
time.sleep(0.5)
after = len(driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph"))
print(f"Paragraphs before Enter: {before}, after: {after}")

# Check if Shift+Enter is different
el.send_keys(Keys.SHIFT, Keys.RETURN)
time.sleep(0.5)
after2 = len(driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph"))
print(f"Paragraphs after Shift+Enter: {after2}")

driver.quit()
