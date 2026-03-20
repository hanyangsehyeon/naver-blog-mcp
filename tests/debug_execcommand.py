"""
Debug: test document.execCommand inside input_buffer iframe
"""
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
time.sleep(2)
dismiss_naver_popups(driver)
time.sleep(0.5)
dismiss_naver_popups(driver)


def focus_and_get_iframe_body(para_index=1):
    driver.switch_to.default_content()
    dismiss_naver_popups(driver)
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    ActionChains(driver).move_to_element(paras[para_index]).click().perform()
    time.sleep(0.4)
    dismiss_naver_popups(driver)
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
    driver.switch_to.frame(iframe)
    time.sleep(0.2)
    return driver.find_element(By.TAG_NAME, "body")


def para_html(index=1):
    driver.switch_to.default_content()
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    return driver.execute_script("return arguments[0].innerHTML;", paras[index])


# ── Test 1: execCommand('bold') inside iframe ─────────────────────────────
print("\n=== Test 1: execCommand bold ===")
body = focus_and_get_iframe_body(1)

body.send_keys("plain ")

r = driver.execute_script("return document.execCommand('bold', false, null)")
print(f"  execCommand('bold') returned: {r}")

body.send_keys("BOLD_TEXT")

r2 = driver.execute_script("return document.execCommand('bold', false, null)")
print(f"  execCommand('bold') off returned: {r2}")

body.send_keys(" plain_end.")
time.sleep(0.5)

driver.save_screenshot("tests/exc_1_bold.png")
html = para_html(1)
print(f"  para HTML: {html[:500]}")
has_bold = "se-bold" in html or "<strong" in html or "<b>" in html
print(f"  Bold in DOM: {has_bold}")


# ── Test 2: execCommand('hiliteColor') inside iframe ──────────────────────
print("\n=== Test 2: execCommand hiliteColor ===")
body = focus_and_get_iframe_body(1)
body.send_keys(Keys.END, Keys.RETURN)
driver.switch_to.default_content()
time.sleep(0.3)

body = focus_and_get_iframe_body(1)
body.send_keys("start ")

r3 = driver.execute_script("return document.execCommand('hiliteColor', false, '#fff8b2')")
print(f"  execCommand('hiliteColor') returned: {r3}")

body.send_keys("HIGHLIGHTED")

r4 = driver.execute_script("return document.execCommand('hiliteColor', false, 'transparent')")
print(f"  execCommand('hiliteColor') off returned: {r4}")

body.send_keys(" end.")
time.sleep(0.5)

driver.save_screenshot("tests/exc_2_highlight.png")
driver.switch_to.default_content()
paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
for p in paras:
    if "HIGHLIGHTED" in p.text:
        h = driver.execute_script("return arguments[0].innerHTML;", p)
        print(f"  para HTML: {h[:500]}")
        print(f"  BG on HIGHLIGHTED: {'background-color' in h and 'HIGHLIGHTED' in h}")
        break


# ── Test 3: execCommand('foreColor') inside iframe ────────────────────────
print("\n=== Test 3: execCommand foreColor ===")
body = focus_and_get_iframe_body(1)
body.send_keys(Keys.END, Keys.RETURN)
driver.switch_to.default_content()
time.sleep(0.3)

body = focus_and_get_iframe_body(1)

r5 = driver.execute_script("return document.execCommand('foreColor', false, '#e53935')")
print(f"  execCommand('foreColor') returned: {r5}")

body.send_keys("RED_TEXT")

r6 = driver.execute_script("return document.execCommand('foreColor', false, '#000000')")
print(f"  execCommand('foreColor') reset returned: {r6}")

body.send_keys(" back_to_black.")
time.sleep(0.5)

driver.save_screenshot("tests/exc_3_fontcolor.png")
driver.switch_to.default_content()
paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
for p in paras:
    if "RED_TEXT" in p.text:
        h = driver.execute_script("return arguments[0].innerHTML;", p)
        print(f"  para HTML: {h[:500]}")
        print(f"  Color on RED_TEXT: {'e53935' in h.lower() or 'color' in h}")
        break


print("\n=== SUMMARY ===")
print("Check: exc_1_bold.png, exc_2_highlight.png, exc_3_fontcolor.png")
driver.quit()
