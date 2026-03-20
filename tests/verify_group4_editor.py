"""
Group 4: Smart Editor ONE — Text Input Verification
Checks 4.1 ~ 4.11

Key finding: Smart Editor ONE uses a hidden iframe (id starts with 'input_buffer')
as the actual input area. Must click .se-text-paragraph first to activate it,
then switch_to.frame(input_buffer iframe) and send_keys to <body>.
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.common import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

results = {}

driver = make_driver(headless=False)
print("\n── Login ──")
login_with_qr(driver)


# ── 4.1 Navigate to write page ───────────────────────────────────────────────
print("\n── 4.1 Navigate to write page ──")
try:
    driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".se-text-paragraph"))
    )
    time.sleep(1)
    check(results, "4.1 Navigate to write page", PASS, driver.current_url)
except Exception as e:
    check(results, "4.1 Navigate to write page", FAIL, str(e))


# ── 4.2 Title field locator ──────────────────────────────────────────────────
print("\n── 4.2 Title field locator ──")
try:
    title_el = driver.find_element(By.CSS_SELECTOR, ".se-title-text")
    check(results, "4.2 Title field locator", PASS, ".se-title-text")
except Exception as e:
    check(results, "4.2 Title field locator", FAIL, str(e))


# ── Helpers ──────────────────────────────────────────────────────────────────
def dismiss_popups():
    """Close '작성 중인 글' dialog (cancel) and 도움말 panel."""
    # '작성 중인 글' dialog — click 취소 to start fresh
    try:
        cancel = driver.find_element(By.CSS_SELECTOR, ".se-popup-button-cancel")
        if cancel.is_displayed():
            cancel.click()
            time.sleep(0.5)
    except:
        pass
    # 도움말 panel — click 닫기
    try:
        close = driver.find_element(By.CSS_SELECTOR, ".se-help-panel-close-button")
        if close.is_displayed():
            close.click()
            time.sleep(0.3)
    except:
        pass

def get_input_iframe_body(para_index):
    """Click paragraph by index, switch to input_buffer iframe, return body."""
    driver.switch_to.default_content()
    dismiss_popups()
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    ActionChains(driver).move_to_element(paras[para_index]).click().perform()
    time.sleep(0.3)
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
    driver.switch_to.frame(iframe)
    time.sleep(0.2)
    return driver.find_element(By.TAG_NAME, "body")

def get_editor_body():
    return get_input_iframe_body(1)  # index 1 = body (0 = title)


# ── 4.3 Title input ──────────────────────────────────────────────────────────
print("\n── 4.3 Title input ──")
try:
    body = get_input_iframe_body(0)  # index 0 = title
    body.send_keys("테스트 제목 Test Title")
    time.sleep(0.5)
    driver.switch_to.default_content()
    val = driver.find_element(By.CSS_SELECTOR, ".se-title-text").text
    if "테스트" in val or "Test" in val:
        check(results, "4.3 Title input", PASS, f"'{val}'")
    else:
        check(results, "4.3 Title input", FAIL, f"got: '{val}'")
except Exception as e:
    driver.switch_to.default_content()
    check(results, "4.3 Title input", FAIL, str(e))


# ── 4.4 Body editor iframe detection ────────────────────────────────────────
print("\n── 4.4 Body editor iframe detection ──")
try:
    driver.switch_to.default_content()
    para = driver.find_element(By.CSS_SELECTOR, ".se-text-paragraph")
    ActionChains(driver).move_to_element(para).click().perform()
    time.sleep(0.3)
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
    fid = iframe.get_attribute("id")
    check(results, "4.4 Body editor iframe detection", PASS, f"input_buffer iframe: id='{fid}'")
except Exception as e:
    check(results, "4.4 Body editor iframe detection", FAIL, str(e))


# ── 4.5 Body contenteditable locator ────────────────────────────────────────
print("\n── 4.5 Body contenteditable locator ──")
try:
    body = get_editor_body()
    ce = body.get_attribute("contenteditable")
    check(results, "4.5 Body contenteditable locator", PASS,
          f"<body contenteditable='{ce}'> inside input_buffer iframe")
    driver.switch_to.default_content()
except Exception as e:
    check(results, "4.5 Body contenteditable locator", FAIL, str(e))
    driver.switch_to.default_content()


# ── 4.6 send_keys for body text ──────────────────────────────────────────────
print("\n── 4.6 send_keys for body text ──")
try:
    body = get_editor_body()
    body.send_keys("send_keys test paragraph.")
    time.sleep(0.5)
    driver.switch_to.default_content()
    if "send_keys test paragraph." in driver.page_source:
        check(results, "4.6 send_keys for body text", PASS)
    else:
        check(results, "4.6 send_keys for body text", FAIL, "text not found in page source")
except Exception as e:
    driver.switch_to.default_content()
    check(results, "4.6 send_keys for body text", FAIL, str(e))


# ── 4.7 Clipboard paste ──────────────────────────────────────────────────────
print("\n── 4.7 Clipboard paste (pyperclip + Cmd+V) ──")
try:
    import pyperclip
    body = get_editor_body()
    body.send_keys(Keys.END, Keys.RETURN)
    time.sleep(0.2)
    clipboard_text = "clipboard paste test."
    pyperclip.copy(clipboard_text)
    time.sleep(0.2)
    # Send Cmd+V while inside iframe context via ActionChains
    ActionChains(driver).key_down(Keys.COMMAND).send_keys("v").key_up(Keys.COMMAND).perform()
    time.sleep(0.8)
    driver.switch_to.default_content()
    if clipboard_text in driver.page_source:
        check(results, "4.7 Clipboard paste", PASS)
    else:
        check(results, "4.7 Clipboard paste", FAIL, "text not found after paste")
except ImportError:
    driver.switch_to.default_content()
    check(results, "4.7 Clipboard paste", FAIL, "pyperclip not installed")
except Exception as e:
    driver.switch_to.default_content()
    check(results, "4.7 Clipboard paste", FAIL, str(e))


# ── 4.8 JS execCommand fallback ──────────────────────────────────────────────
print("\n── 4.8 JS execCommand('insertText') fallback ──")
try:
    body = get_editor_body()
    body.send_keys(Keys.END, Keys.RETURN)
    time.sleep(0.2)
    js_text = "execCommand test."
    driver.execute_script("document.execCommand('insertText', false, arguments[0])", js_text)
    time.sleep(0.5)
    driver.switch_to.default_content()
    if js_text in driver.page_source:
        check(results, "4.8 JS execCommand fallback", PASS)
    else:
        check(results, "4.8 JS execCommand fallback", FAIL, "text not found")
except Exception as e:
    driver.switch_to.default_content()
    check(results, "4.8 JS execCommand fallback", FAIL, str(e))


# ── 4.9 Paragraph separator via Enter ───────────────────────────────────────
print("\n── 4.9 Paragraph separator via Enter ──")
try:
    driver.switch_to.default_content()
    para_before = len(driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph"))
    body = get_editor_body()
    body.send_keys(Keys.END, Keys.RETURN)
    time.sleep(0.5)
    driver.switch_to.default_content()
    para_after = len(driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph"))
    if para_after > para_before:
        check(results, "4.9 Paragraph separator via Enter", PASS,
              f"paragraphs: {para_before} → {para_after}")
    else:
        check(results, "4.9 Paragraph separator via Enter", FAIL,
              f"count unchanged: {para_before}")
except Exception as e:
    driver.switch_to.default_content()
    check(results, "4.9 Paragraph separator via Enter", FAIL, str(e))


# ── 4.10 Korean text input ───────────────────────────────────────────────────
print("\n── 4.10 Korean text input ──")
try:
    import pyperclip
    korean_text = "한글 테스트 문단입니다."
    body = get_editor_body()
    body.send_keys(Keys.END, Keys.RETURN)
    time.sleep(0.2)
    body.send_keys(korean_text)
    time.sleep(0.5)
    driver.switch_to.default_content()
    if korean_text in driver.page_source:
        check(results, "4.10 Korean text input", PASS, "send_keys works for Korean")
    else:
        # Try clipboard
        body = get_editor_body()
        body.send_keys(Keys.END, Keys.RETURN)
        pyperclip.copy(korean_text)
        time.sleep(0.2)
        ActionChains(driver).key_down(Keys.COMMAND).send_keys("v").key_up(Keys.COMMAND).perform()
        time.sleep(0.8)
        driver.switch_to.default_content()
        if korean_text in driver.page_source:
            check(results, "4.10 Korean text input", PASS, "clipboard works for Korean")
        else:
            check(results, "4.10 Korean text input", FAIL, "Korean not found via any method")
except Exception as e:
    driver.switch_to.default_content()
    check(results, "4.10 Korean text input", FAIL, str(e))


# ── 4.11 Multi-paragraph loop stability ─────────────────────────────────────
print("\n── 4.11 Multi-paragraph loop stability ──")
try:
    import pyperclip
    errors = []
    for i in range(8):
        try:
            body = get_editor_body()
            body.send_keys(Keys.END, Keys.RETURN)
            time.sleep(0.2)
            para_text = f"문단 {i+1}: 안정성 테스트입니다."
            pyperclip.copy(para_text)
            time.sleep(0.2)
            ActionChains(driver).key_down(Keys.COMMAND).send_keys("v").key_up(Keys.COMMAND).perform()
            time.sleep(0.4)
            driver.switch_to.default_content()
        except Exception as e:
            driver.switch_to.default_content()
            errors.append(f"para {i+1}: {str(e)[:60]}")

    if not errors:
        para_count = len(driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph"))
        check(results, "4.11 Multi-paragraph loop stability", PASS,
              f"8 paragraphs inserted, total in DOM: {para_count}")
    else:
        check(results, "4.11 Multi-paragraph loop stability", FAIL, str(errors))
except Exception as e:
    driver.switch_to.default_content()
    check(results, "4.11 Multi-paragraph loop stability", FAIL, str(e))


driver.quit()
print_summary(results)
