"""
Debug: HTML clipboard paste
Set clipboard to HTML-formatted text, then paste.
Smart Editor ONE might preserve <b>, <span style="background-color"> etc.
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


def focus_and_iframe():
    driver.switch_to.default_content()
    dismiss_naver_popups(driver)
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    ActionChains(driver).move_to_element(paras[1]).click().perform()
    time.sleep(0.4)
    dismiss_naver_popups(driver)
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
    driver.switch_to.frame(iframe)
    time.sleep(0.2)
    return driver.find_element(By.TAG_NAME, "body")


def plain_paste(text):
    """Plain text paste inside iframe via ActionChains Cmd+V."""
    import pyperclip
    pyperclip.copy(text)
    time.sleep(0.15)
    ActionChains(driver).key_down(Keys.COMMAND).send_keys("v").key_up(Keys.COMMAND).perform()
    time.sleep(0.4)


def html_paste(html, plain_fallback):
    """
    Set clipboard to HTML + plain text, dispatch paste event in iframe.
    Uses JS ClipboardEvent with DataTransfer to inject HTML-formatted content.
    """
    js = """
    (function(html, plain) {
        // Build a DataTransfer with both HTML and plain text
        var dt = new DataTransfer();
        dt.setData('text/html', html);
        dt.setData('text/plain', plain);
        var ev = new ClipboardEvent('paste', {
            clipboardData: dt,
            bubbles: true,
            cancelable: true
        });
        document.activeElement.dispatchEvent(ev);
        return 'dispatched';
    })(arguments[0], arguments[1]);
    """
    result = driver.execute_script(js, html, plain_fallback)
    time.sleep(0.6)
    return result


# ── Test 1: plain paste baseline ─────────────────────────────────────────
print("\n=== Test 1: plain paste baseline ===")
body = focus_and_iframe()
plain_paste("plain start ")
driver.switch_to.default_content()
print(f"  text: '{driver.find_elements(By.CSS_SELECTOR, '.se-text-paragraph')[1].text}'")


# ── Test 2: HTML paste with <b> tag ───────────────────────────────────────
print("\n=== Test 2: HTML paste with <b>BOLD</b> ===")
body = focus_and_iframe()
r = html_paste("<b>볼드텍스트 BOLD</b>", "볼드텍스트 BOLD")
print(f"  dispatch result: {r}")
driver.switch_to.default_content()
time.sleep(0.3)

driver.save_screenshot("tests/html_paste_bold.png")
paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
p = paras[1]
html = driver.execute_script("return arguments[0].innerHTML;", p)
print(f"  text: '{p.text}'")
print(f"  HTML: {html[:500]}")
has_bold = "se-bold" in html or "<strong" in html or "<b>" in html or "font-weight" in html
print(f"  Bold in DOM: {has_bold}")


# ── Test 3: HTML paste with background-color ──────────────────────────────
print("\n=== Test 3: HTML paste with background-color ===")
body = focus_and_iframe()
body.send_keys(Keys.END)
r2 = html_paste(
    '<span style="background-color:#fff8b2">형광펜 HIGHLIGHT</span>',
    "형광펜 HIGHLIGHT"
)
print(f"  dispatch result: {r2}")
driver.switch_to.default_content()
time.sleep(0.3)

driver.save_screenshot("tests/html_paste_bg.png")
paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
for p in paras:
    if "HIGHLIGHT" in p.text:
        h = driver.execute_script("return arguments[0].innerHTML;", p)
        print(f"  text: '{p.text}'")
        print(f"  HTML: {h[:600]}")
        print(f"  BG in DOM: {'background-color' in h and 'HIGHLIGHT' in h}")
        break


# ── Test 4: combined paragraph - plain + bold + plain ─────────────────────
print("\n=== Test 4: combined paragraph ===")
body = focus_and_iframe()
body.send_keys(Keys.END, Keys.RETURN)
driver.switch_to.default_content()
time.sleep(0.3)

body = focus_and_iframe()
r3 = html_paste(
    'normal <b>볼드부분</b> normal again',
    'normal 볼드부분 normal again'
)
print(f"  dispatch result: {r3}")
driver.switch_to.default_content()
time.sleep(0.3)

driver.save_screenshot("tests/html_paste_combined.png")
paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
for p in paras:
    if "볼드부분" in p.text:
        h = driver.execute_script("return arguments[0].innerHTML;", p)
        print(f"  text: '{p.text}'")
        print(f"  HTML: {h[:600]}")
        print(f"  Bold: {'se-bold' in h or '<b>' in h or '<strong' in h}")
        break

print("\nCheck: html_paste_bold.png, html_paste_bg.png, html_paste_combined.png")
driver.quit()
