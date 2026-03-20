"""
Debug: bold toggle + ActionChains Cmd+V (inside iframe)
Question: does paste inside iframe respect bold toggle state?
"""
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
dismiss_naver_popups(driver)
time.sleep(0.5)
dismiss_naver_popups(driver)


def focus_paragraph(para_index=1):
    driver.switch_to.default_content()
    dismiss_naver_popups(driver)
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    ActionChains(driver).move_to_element(paras[para_index]).click().perform()
    time.sleep(0.4)
    dismiss_naver_popups(driver)


def get_iframe_body():
    """Switch to iframe WITHOUT re-clicking paragraph."""
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
    driver.switch_to.frame(iframe)
    time.sleep(0.2)
    return driver.find_element(By.TAG_NAME, "body")


def paste_in_iframe(text):
    """Paste text using ActionChains Cmd+V inside iframe."""
    pyperclip.copy(text)
    time.sleep(0.2)
    ActionChains(driver).key_down(Keys.COMMAND).send_keys("v").key_up(Keys.COMMAND).perform()
    time.sleep(0.5)


def click_toolbar_btn(selector):
    driver.switch_to.default_content()
    btn = driver.find_element(By.CSS_SELECTOR, selector)
    ActionChains(driver).click(btn).perform()
    time.sleep(0.3)


def get_para_html(index=1):
    driver.switch_to.default_content()
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    return driver.execute_script("return arguments[0].innerHTML;", paras[index])


# ── Test 1: plain text via iframe paste (baseline) ───────────────────────
print("\n=== Test 1: plain paste (baseline) ===")
focus_paragraph(1)
get_iframe_body()
paste_in_iframe("plain text ")
driver.switch_to.default_content()
time.sleep(0.3)
print(f"  para text: '{driver.find_elements(By.CSS_SELECTOR, '.se-text-paragraph')[1].text}'")


# ── Test 2: Bold toggle ON → paste → toggle OFF ───────────────────────────
print("\n=== Test 2: Bold toggle + paste ===")

# Bold ON
click_toolbar_btn(".se-bold-toolbar-button")

# Cursor back in editor, switch to iframe, paste
focus_paragraph(1)
get_iframe_body()
paste_in_iframe("볼드텍스트 BOLD")
driver.switch_to.default_content()

# Bold OFF
click_toolbar_btn(".se-bold-toolbar-button")

# Plain text after
focus_paragraph(1)
get_iframe_body()
paste_in_iframe(" plain_end.")
driver.switch_to.default_content()

time.sleep(0.5)
driver.save_screenshot("tests/bold_paste_result.png")

html = get_para_html(1)
text = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")[1].text
print(f"  para text: '{text}'")
print(f"  para HTML: {html[:600]}")
has_bold = "se-bold" in html or "<strong" in html or "font-weight:bold" in html.replace(" ", "")
print(f"  Bold in DOM: {has_bold}")


# ── Test 3: Background color toggle + paste ───────────────────────────────
print("\n=== Test 3: Background color toggle + paste ===")

# New line
focus_paragraph(1)
get_iframe_body()
driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END, Keys.RETURN)
driver.switch_to.default_content()
time.sleep(0.3)

focus_paragraph(1)
get_iframe_body()
paste_in_iframe("start ")
driver.switch_to.default_content()

# BG color ON
click_toolbar_btn(".se-background-color-toolbar-button")
try:
    yellow = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-color-palette[title='#fff8b2']"))
    )
    ActionChains(driver).click(yellow).perform()
    time.sleep(0.4)
    print("  Yellow selected")
except Exception as e:
    print(f"  Yellow error: {e}")

# Paste highlighted text
focus_paragraph(1)
get_iframe_body()
paste_in_iframe("형광펜 HIGHLIGHTED")
driver.switch_to.default_content()

# BG color OFF (색상 없음)
click_toolbar_btn(".se-background-color-toolbar-button")
try:
    no_color = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-color-palette-no-color"))
    )
    ActionChains(driver).click(no_color).perform()
    time.sleep(0.3)
except Exception as e:
    print(f"  No-color error: {e}")

focus_paragraph(1)
get_iframe_body()
paste_in_iframe(" end.")
driver.switch_to.default_content()

time.sleep(0.5)
driver.save_screenshot("tests/bg_paste_result.png")

paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
for p in paras:
    if "HIGHLIGHTED" in p.text:
        h = driver.execute_script("return arguments[0].innerHTML;", p)
        print(f"  text: '{p.text}'")
        print(f"  HTML: {h[:700]}")
        has_bg = "background-color" in h and "HIGHLIGHTED" in h
        print(f"  BG on HIGHLIGHTED: {has_bg}")
        break

print("\nCheck: bold_paste_result.png, bg_paste_result.png")
driver.quit()
