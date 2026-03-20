"""Debug: map out editor elements with locations and screenshot"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.common import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = make_driver(headless=False)
login_with_qr(driver)

driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".se-text-paragraph"))
)
time.sleep(2)

# Print ALL se-* elements with location, size, text
print("\n=== All .se-* elements ===")
for sel in [".se-title-text", ".se-documentTitle", ".se-main-container",
            ".se-text-paragraph", ".se-component", "[contenteditable]"]:
    els = driver.find_elements(By.CSS_SELECTOR, sel)
    for el in els:
        print(f"  [{sel}] loc={el.location} size={el.size} visible={el.is_displayed()} text='{el.text[:40]}'")

driver.save_screenshot("tests/editor_layout.png")
print("\nScreenshot saved to tests/editor_layout.png")
driver.quit()
