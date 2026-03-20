"""
Debug: correct toggle approach
Key: after clicking toolbar, DON'T re-click the paragraph.
Just switch to iframe directly and type.
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


def focus_paragraph(para_index=1):
    """Click paragraph to place cursor inside editor. Stay in main DOM."""
    driver.switch_to.default_content()
    dismiss_naver_popups(driver)
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    ActionChains(driver).move_to_element(paras[para_index]).click().perform()
    time.sleep(0.4)
    dismiss_naver_popups(driver)


def switch_to_iframe_body():
    """Switch to input_buffer iframe and return body. Don't click paragraph."""
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
    driver.switch_to.frame(iframe)
    time.sleep(0.2)
    return driver.find_element(By.TAG_NAME, "body")


def click_toolbar_btn(selector):
    """Click toolbar button WITHOUT re-clicking paragraph."""
    driver.switch_to.default_content()
    btn = driver.find_element(By.CSS_SELECTOR, selector)
    ActionChains(driver).click(btn).perform()
    time.sleep(0.3)


def type_text(text):
    """Type into iframe body. Cursor must already be in editor."""
    body = switch_to_iframe_body()
    body.send_keys(Keys.END)
    body.send_keys(text)
    time.sleep(0.4)
    driver.switch_to.default_content()


# ── Test 1: Bold toggle ───────────────────────────────────────────────────
print("\n=== Test 1: Bold toggle ===")
# Place cursor in paragraph
focus_paragraph(1)

# Type plain text first
type_text("plain ")

# Now: click Bold (toggle ON) → type → click Bold (toggle OFF)
focus_paragraph(1)                        # cursor at end of "plain "
click_toolbar_btn(".se-bold-toolbar-button")  # toggle bold ON
type_text("BOLD_TEXT")                    # type while bold is on
click_toolbar_btn(".se-bold-toolbar-button")  # toggle bold OFF
type_text(" more plain.")

driver.save_screenshot("tests/fmt_1_bold_toggle.png")
paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
para_text = paras[1].text
para_html = driver.execute_script("return arguments[0].innerHTML;", paras[1])
print(f"  text: '{para_text}'")
print(f"  HTML: {para_html[:500]}")
has_bold = "se-bold" in para_html or "<strong" in para_html
print(f"  Bold in DOM: {has_bold}")


# ── Test 2: Background color ──────────────────────────────────────────────
print("\n=== Test 2: Background color toggle ===")
# New paragraph
focus_paragraph(1)
body = switch_to_iframe_body()
body.send_keys(Keys.END, Keys.RETURN)
driver.switch_to.default_content()
time.sleep(0.3)

focus_paragraph(1)
type_text("start ")

# Open bg color picker → select yellow → type highlighted text
focus_paragraph(1)
click_toolbar_btn(".se-background-color-toolbar-button")
try:
    yellow = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-color-palette[title='#fff8b2']"))
    )
    ActionChains(driver).click(yellow).perform()
    time.sleep(0.4)
    print("  Yellow selected")
except Exception as e:
    print(f"  Error: {e}")

type_text("HIGHLIGHTED_TEXT")

# Turn off highlight
focus_paragraph(1)
click_toolbar_btn(".se-background-color-toolbar-button")
try:
    no_color = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-color-palette-no-color"))
    )
    ActionChains(driver).click(no_color).perform()
    time.sleep(0.3)
    print("  No-color selected")
except Exception as e:
    print(f"  No-color error: {e}")

type_text(" end.")

driver.save_screenshot("tests/fmt_2_bg_toggle.png")
paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
for p in paras:
    if "HIGHLIGHTED_TEXT" in p.text:
        p_html = driver.execute_script("return arguments[0].innerHTML;", p)
        print(f"  text: '{p.text}'")
        print(f"  HTML: {p_html[:700]}")
        has_bg = "background-color" in p_html and "HIGHLIGHTED_TEXT" in p_html
        print(f"  BG on HIGHLIGHTED_TEXT: {has_bg}")
        break


print("\nCheck fmt_1_bold_toggle.png and fmt_2_bg_toggle.png")
driver.quit()
