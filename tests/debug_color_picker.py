"""Debug: inspect color picker HTML structure"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.common import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = make_driver(headless=False)
login_with_qr(driver)

driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".se-text-paragraph"))
)
time.sleep(1.5)

# Dismiss popups
dismiss_naver_popups(driver)

# Type some text
paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
ActionChains(driver).move_to_element(paras[1]).click().perform()
time.sleep(0.3)
iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
driver.switch_to.frame(iframe)
body = driver.find_element(By.TAG_NAME, "body")
body.send_keys("Test text for color picker inspection.")
time.sleep(0.4)
driver.switch_to.default_content()

# Select text via JS
driver.execute_script("""
    var paras = document.querySelectorAll('.se-text-paragraph');
    for (var i = 0; i < paras.length; i++) {
        if (paras[i].textContent.indexOf('Test text') !== -1) {
            var sel = window.getSelection();
            var range = document.createRange();
            range.selectNodeContents(paras[i]);
            sel.removeAllRanges();
            sel.addRange(range);
            break;
        }
    }
""")
time.sleep(0.2)

# Find background color button
btns = driver.find_elements(By.CSS_SELECTOR, ".se-toolbar button, .se-toolbar [data-type]")
bg_btn = None
for btn in btns:
    cls = (btn.get_attribute("class") or "").lower()
    if "background" in cls or "hilite" in cls:
        bg_btn = btn
        break

if bg_btn:
    print(f"bg_btn class: {bg_btn.get_attribute('class')}")
    driver.execute_script("arguments[0].click();", bg_btn)
    time.sleep(1.0)

    # Get all inputs inside the opened picker
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"\n=== All visible inputs after picker open ({len(inputs)}) ===")
    for inp in inputs:
        print(f"  type={inp.get_attribute('type')} placeholder='{inp.get_attribute('placeholder')}' "
              f"maxlength={inp.get_attribute('maxlength')} class='{inp.get_attribute('class')[:60]}' "
              f"visible={inp.is_displayed()}")

    # Get picker container HTML
    picker = driver.find_elements(By.CSS_SELECTOR,
        ".se-property-color-picker-container, .se-color-picker, [class*='color-picker']")
    if picker:
        html = driver.execute_script("return arguments[0].outerHTML;", picker[0])
        print(f"\n=== Color picker HTML (first 2000 chars) ===")
        print(html[:2000])

    # All buttons inside picker
    picker_btns = driver.find_elements(By.CSS_SELECTOR,
        ".se-property-color-picker-container button, [class*='color-picker'] button")
    print(f"\n=== Buttons inside picker ({len(picker_btns)}) ===")
    for b in picker_btns[:20]:
        print(f"  class='{b.get_attribute('class')[:60]}' style='{b.get_attribute('style')}' "
              f"title='{b.get_attribute('title')}'")

driver.quit()
