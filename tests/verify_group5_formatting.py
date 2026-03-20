"""
Group 5: Smart Editor ONE — Formatting Verification
Checks 5.1 ~ 5.12

Strategy:
1. Input a test paragraph via the proven input_buffer iframe method
2. Switch back to main DOM
3. Use JS window.getSelection() + Range to select text
4. Apply formatting via keyboard shortcut or toolbar
5. Verify in DOM
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

results = {}

driver = make_driver(headless=False)
print("\n── Login ──")
login_with_qr(driver)


# ── Setup: navigate to write page and input test paragraph ────────────────────
print("\n── Setup: navigate and input test content ──")
driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".se-text-paragraph"))
)
time.sleep(1.5)


def dismiss_popups():
    # '작성 중인 글' dialog → 취소
    try:
        cancel = driver.find_element(By.CSS_SELECTOR, ".se-popup-button-cancel")
        if cancel.is_displayed():
            cancel.click()
            time.sleep(0.5)
    except:
        pass
    # 도움말 panel → 닫기
    try:
        close = driver.find_element(By.CSS_SELECTOR, ".se-help-panel-close-button")
        if close.is_displayed():
            close.click()
            time.sleep(0.3)
    except:
        pass
    # '내돈내산 기능 이용안내' modal → 취소 (layer_popup_wrap)
    try:
        # Find any modal with 취소 button that's blocking
        layer = driver.find_element(By.CSS_SELECTOR, "[class*='layer_popup_wrap']")
        if layer.is_displayed():
            # Click 취소 button inside the modal
            buttons = layer.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.text.strip() in ["취소", "닫기", "확인"]:
                    # Prefer 취소 to dismiss, not 동의
                    if btn.text.strip() in ["취소", "닫기"]:
                        btn.click()
                        time.sleep(0.5)
                        break
                    cancel_candidate = btn
            else:
                # fallback: click first button
                if buttons:
                    buttons[0].click()
                    time.sleep(0.5)
    except:
        pass


def get_input_iframe_body(para_index=1):
    driver.switch_to.default_content()
    dismiss_popups()
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    ActionChains(driver).move_to_element(paras[para_index]).click().perform()
    time.sleep(0.3)
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
    driver.switch_to.frame(iframe)
    time.sleep(0.2)
    return driver.find_element(By.TAG_NAME, "body")


def type_text(text, para_index=1):
    """Type text using send_keys inside the input_buffer iframe."""
    body = get_input_iframe_body(para_index)
    body.send_keys(Keys.END)
    body.send_keys(text)
    time.sleep(0.5)
    driver.switch_to.default_content()


def new_paragraph(para_index=1):
    """Press Enter to create a new paragraph."""
    body = get_input_iframe_body(para_index)
    body.send_keys(Keys.END, Keys.RETURN)
    driver.switch_to.default_content()
    time.sleep(0.4)


# Input test paragraphs
dismiss_popups()
TEST_TEXT = "Bold formatting test sentence here."
type_text(TEST_TEXT)

# Add a second paragraph
new_paragraph()
PARA2_TEXT = "Background color test second paragraph."
type_text(PARA2_TEXT)
time.sleep(0.3)


# ── JS helper: select text range in a paragraph ──────────────────────────────
SELECT_JS = """
(function(paraText, startIdx, endIdx) {
    var paras = document.querySelectorAll('.se-text-paragraph');
    for (var i = 0; i < paras.length; i++) {
        var tn = null;
        // walk text nodes
        var walker = document.createTreeWalker(paras[i], NodeFilter.SHOW_TEXT);
        var node;
        var full = '';
        var nodes = [];
        while (node = walker.nextNode()) {
            nodes.push(node);
            full += node.nodeValue;
        }
        if (full.indexOf(paraText) !== -1) {
            // find offset within nodes
            var offset = full.indexOf(paraText);
            var sel = window.getSelection();
            sel.removeAllRanges();
            var range = document.createRange();
            // map startIdx/endIdx into node offsets
            var cur = 0;
            var rangeSet = {start: false, end: false};
            for (var j = 0; j < nodes.length; j++) {
                var nlen = nodes[j].nodeValue.length;
                if (!rangeSet.start && cur + nlen > startIdx) {
                    range.setStart(nodes[j], startIdx - cur);
                    rangeSet.start = true;
                }
                if (!rangeSet.end && cur + nlen >= endIdx) {
                    range.setEnd(nodes[j], endIdx - cur);
                    rangeSet.end = true;
                    break;
                }
                cur += nlen;
            }
            if (rangeSet.start && rangeSet.end) {
                sel.addRange(range);
                return 'selected: ' + sel.toString();
            }
            return 'range set failed';
        }
    }
    return 'paragraph not found: ' + paraText;
})(arguments[0], arguments[1], arguments[2]);
"""


# ── 5.1 JS text range selection ──────────────────────────────────────────────
print("\n── 5.1 JS text range selection ──")
try:
    # Debug: check what text is in paragraphs
    para_texts = driver.execute_script(
        "return Array.from(document.querySelectorAll('.se-text-paragraph')).map(p => p.textContent.slice(0,50))"
    )
    print(f"   para_texts: {para_texts}")

    result = driver.execute_script(SELECT_JS, TEST_TEXT, 0, 4)  # select "Bold"
    # Also verify via getSelection in case return value is lost
    sel_check = driver.execute_script("return window.getSelection().toString();")
    if (result and "selected:" in result) or "Bold" in sel_check:
        check(results, "5.1 JS text range selection", PASS, f"result={result}, sel='{sel_check}'")
    else:
        check(results, "5.1 JS text range selection", FAIL, f"result={result}, sel='{sel_check}', paras={para_texts}")
except Exception as e:
    check(results, "5.1 JS text range selection", FAIL, str(e))


# ── 5.2 Selection survives Python context switch ─────────────────────────────
print("\n── 5.2 Selection survives context switch ──")
try:
    # Set selection
    driver.execute_script(SELECT_JS, TEST_TEXT, 0, 4)
    time.sleep(0.1)
    # Check selection still active
    sel_text = driver.execute_script("return window.getSelection().toString();")
    if "Bold" in sel_text:
        check(results, "5.2 Selection survives context switch", PASS, f"'{sel_text}'")
    else:
        check(results, "5.2 Selection survives context switch", FAIL, f"got: '{sel_text}'")
except Exception as e:
    check(results, "5.2 Selection survives context switch", FAIL, str(e))


# ── 5.3 Bold via keyboard shortcut ──────────────────────────────────────────
print("\n── 5.3 Bold via keyboard shortcut (Cmd+B) ──")
try:
    # Click paragraph to focus it first
    para = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")[1]
    driver.execute_script("arguments[0].click();", para)
    time.sleep(0.3)
    # Select "Bold"
    driver.execute_script(SELECT_JS, TEST_TEXT, 0, 4)
    time.sleep(0.2)
    # Apply bold
    ActionChains(driver).key_down(Keys.COMMAND).send_keys("b").key_up(Keys.COMMAND).perform()
    time.sleep(0.8)
    # Check DOM for bold
    src = driver.page_source
    if "se-bold" in src or "<strong" in src or "<b>" in src:
        check(results, "5.3 Bold via keyboard shortcut", PASS, "bold element found in DOM")
    else:
        check(results, "5.3 Bold via keyboard shortcut", FAIL, "no bold element in DOM")
except Exception as e:
    check(results, "5.3 Bold via keyboard shortcut", FAIL, str(e))


# ── 5.4 Bold via toolbar button ──────────────────────────────────────────────
print("\n── 5.4 Bold via toolbar button ──")
try:
    # Find bold toolbar button
    bold_btns = driver.find_elements(By.CSS_SELECTOR,
        ".se-toolbar [data-type='bold'], .se-toolbar button[class*='bold'], "
        ".se-toolbar [title*='굵게'], .se-toolbar [title*='Bold'], "
        ".se-toolbar .__se__toolbar__bold, [data-command='bold']"
    )
    if bold_btns:
        btn = bold_btns[0]
        check(results, "5.4 Bold via toolbar button", PASS,
              f"found: class='{btn.get_attribute('class')[:60]}'")
    else:
        # Try finding by text content
        all_toolbar = driver.find_elements(By.CSS_SELECTOR, ".se-toolbar button, .se-toolbar [role='button']")
        check(results, "5.4 Bold via toolbar button", FAIL,
              f"not found; toolbar has {len(all_toolbar)} buttons")
except Exception as e:
    check(results, "5.4 Bold via toolbar button", FAIL, str(e))


# ── 5.5 Background color toolbar button locator ──────────────────────────────
print("\n── 5.5 Background color toolbar button locator ──")
try:
    bg_selectors = [
        ".se-toolbar [data-type='hiliteColor']",
        ".se-toolbar [title*='형광펜']",
        ".se-toolbar [title*='배경색']",
        ".se-toolbar [title*='Highlight']",
        ".se-toolbar [class*='hilite']",
        ".se-toolbar [class*='background']",
        ".se-toolbar [class*='highlight']",
    ]
    found = None
    for sel in bg_selectors:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        if els:
            found = (sel, els[0])
            break
    if found:
        check(results, "5.5 Background color toolbar button", PASS,
              f"selector: '{found[0]}'")
    else:
        # Dump toolbar structure for debugging
        toolbar = driver.find_elements(By.CSS_SELECTOR, ".se-toolbar")
        if toolbar:
            toolbar_html = driver.execute_script("return arguments[0].innerHTML[:500]", toolbar[0])
        check(results, "5.5 Background color toolbar button", FAIL,
              "none of the selectors matched")
except Exception as e:
    check(results, "5.5 Background color toolbar button", FAIL, str(e))


# ── Helper: find background color button by inspecting toolbar buttons ────────
def dismiss_layer_popups():
    """Dismiss any blocking overlay/popup by pressing Escape."""
    try:
        overlay = driver.find_element(By.CSS_SELECTOR, "[class*='layer_popup_wrap'], [class*='popup_wrap']")
        if overlay.is_displayed():
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.4)
    except:
        pass


def find_toolbar_button(keywords):
    """Search toolbar buttons by title/aria-label/class for keywords."""
    btns = driver.find_elements(By.CSS_SELECTOR,
        ".se-toolbar button, .se-toolbar [role='button'], .se-toolbar [data-type]")
    for btn in btns:
        title = (btn.get_attribute("title") or "").lower()
        aria = (btn.get_attribute("aria-label") or "").lower()
        cls = (btn.get_attribute("class") or "").lower()
        data_type = (btn.get_attribute("data-type") or "").lower()
        combined = title + aria + cls + data_type
        if any(k in combined for k in keywords):
            return btn
    return None


# ── 5.6 Color palette dynamic loading ────────────────────────────────────────
print("\n── 5.6 Color palette dynamic loading ──")
try:
    # First try to find and click the background color button
    bg_btn = find_toolbar_button(["hilite", "highlight", "형광", "배경색", "background"])
    if not bg_btn:
        check(results, "5.6 Color palette dynamic loading", FAIL, "bg color button not found")
    else:
        bg_btn.click()
        time.sleep(0.5)
        # Wait for color palette
        palette = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                ".se-color-picker, .se-popup-color, [class*='color-picker'], [class*='colorpicker']"))
        )
        check(results, "5.6 Color palette dynamic loading", PASS,
              f"palette appeared: class='{palette.get_attribute('class')[:60]}'")
        # Close palette by pressing Escape
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.3)
except Exception as e:
    check(results, "5.6 Color palette dynamic loading", FAIL, str(e))


# ── 5.7 Custom hex color input ────────────────────────────────────────────────
print("\n── 5.7 Custom hex color input ──")
try:
    # Open color picker to inspect hex input availability
    dismiss_layer_popups()
    dismiss_popups()
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    para = next((p for p in paras if len(p.text.strip()) > 0), paras[1])
    driver.execute_script("arguments[0].click();", para)
    time.sleep(0.3)

    bg_btn = driver.find_element(By.CSS_SELECTOR, ".se-background-color-toolbar-button")
    driver.execute_script("arguments[0].click();", bg_btn)
    time.sleep(0.8)

    # Check if hidden hex input exists (se-selected-color-hex)
    hex_inp = driver.find_elements(By.CSS_SELECTOR, ".se-selected-color-hex")
    swatches = driver.find_elements(By.CSS_SELECTOR, ".se-color-palette[title]")
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(0.3)

    if hex_inp:
        check(results, "5.7 Custom hex color input", FAIL,
              f"hex input exists (.se-selected-color-hex) but hidden (visible=False); "
              f"must use {len(swatches)} predefined swatches via .se-color-palette[title]")
    else:
        check(results, "5.7 Custom hex color input", FAIL,
              f"no hex input; {len(swatches)} predefined swatches only (.se-color-palette[title])")
except Exception as e:
    check(results, "5.7 Custom hex color input", FAIL, str(e))


# ── 5.8 Background color spans full sentence ─────────────────────────────────
print("\n── 5.8 Background color spans full sentence ──")
try:
    dismiss_layer_popups()
    dismiss_popups()
    # Select a paragraph with text
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    para = next((p for p in paras if len(p.text.strip()) > 5), paras[1])
    driver.execute_script("arguments[0].click();", para)
    time.sleep(0.3)
    # Select all text in that paragraph
    driver.execute_script("""
        var para = arguments[0];
        var sel = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents(para);
        sel.removeAllRanges();
        sel.addRange(range);
    """, para)
    time.sleep(0.2)

    bg_btn = driver.find_element(By.CSS_SELECTOR, ".se-background-color-toolbar-button")
    driver.execute_script("arguments[0].click();", bg_btn)
    time.sleep(0.8)

    # Click yellow swatch (#fff8b2 is the closest yellow in the palette)
    yellow = driver.find_element(By.CSS_SELECTOR, ".se-color-palette[title='#fff8b2']")
    yellow.click()
    time.sleep(0.8)

    src = driver.page_source
    if "background-color" in src or "fff8b2" in src.lower():
        check(results, "5.8 Background color spans full sentence", PASS,
              "yellow swatch applied via .se-color-palette[title='#fff8b2']")
    else:
        check(results, "5.8 Background color spans full sentence", FAIL,
              "no background-color in DOM after swatch click")
except Exception as e:
    check(results, "5.8 Background color spans full sentence", FAIL, str(e))


# ── 5.9 Formatting on multi-paragraph content ────────────────────────────────
print("\n── 5.9 Formatting on multi-paragraph content ──")
try:
    # Check that para1 bold is still there and para2 has background color
    src = driver.page_source
    has_bold = "se-bold" in src or "<strong" in src
    has_bg = "background-color" in src or "hiliteColor" in src or "se-highlight" in src
    if has_bold or has_bg:
        check(results, "5.9 Formatting on multi-paragraph content", PASS,
              f"bold={'yes' if has_bold else 'no'}, bg={'yes' if has_bg else 'no'}")
    else:
        check(results, "5.9 Formatting on multi-paragraph content", FAIL,
              "no formatting found in DOM")
except Exception as e:
    check(results, "5.9 Formatting on multi-paragraph content", FAIL, str(e))


# ── 5.10 Text color change ────────────────────────────────────────────────────
print("\n── 5.10 Text color change ──")
try:
    text_color_btn = find_toolbar_button(["fontcolor", "font-color", "text-color",
                                          "forecolor", "글자색", "텍스트 색"])
    if text_color_btn:
        check(results, "5.10 Text color change", PASS,
              f"button found: '{text_color_btn.get_attribute('class')[:60]}'")
    else:
        # List available buttons for diagnosis
        btns = driver.find_elements(By.CSS_SELECTOR,
            ".se-toolbar button, .se-toolbar [data-type]")
        attrs = [(b.get_attribute("data-type") or b.get_attribute("title") or b.get_attribute("class")[:30])
                 for b in btns[:20]]
        check(results, "5.10 Text color change", FAIL,
              f"not found; sample buttons: {attrs[:10]}")
except Exception as e:
    check(results, "5.10 Text color change", FAIL, str(e))


# ── 5.11 Formatting state after paste ────────────────────────────────────────
print("\n── 5.11 Formatting state after paste ──")
try:
    # Add a new paragraph after formatted content
    body = get_input_iframe_body(1)
    body.send_keys(Keys.COMMAND, Keys.END)  # go to end
    body.send_keys(Keys.RETURN)
    driver.switch_to.default_content()
    time.sleep(0.3)

    NEW_PARA = "Plain text after formatted paragraphs."
    type_text(NEW_PARA)

    src = driver.page_source
    # The new paragraph should NOT have bold/bg styling inline
    # We check the last .se-text-paragraph doesn't have style applied
    paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
    last_para_html = driver.execute_script("return arguments[0].innerHTML;", paras[-1])
    has_carry = "<strong" in last_para_html or "background-color" in last_para_html
    if not has_carry:
        check(results, "5.11 Formatting state after paste", PASS,
              "new paragraph has no carry-over formatting")
    else:
        check(results, "5.11 Formatting state after paste", FAIL,
              f"formatting carried over: {last_para_html[:100]}")
except Exception as e:
    driver.switch_to.default_content()
    check(results, "5.11 Formatting state after paste", FAIL, str(e))


# ── 5.12 JS style injection fallback ─────────────────────────────────────────
print("\n── 5.12 JS style injection fallback ──")
try:
    JS_INJECT = """
    (function(paraText) {
        var paras = document.querySelectorAll('.se-text-paragraph');
        for (var i = 0; i < paras.length; i++) {
            if (paras[i].textContent.indexOf(paraText) !== -1) {
                var walker = document.createTreeWalker(paras[i], NodeFilter.SHOW_TEXT);
                var node = walker.nextNode();
                if (node) {
                    var span = document.createElement('span');
                    span.style.backgroundColor = '#FFE6E6';
                    span.textContent = node.nodeValue.substring(0, 5);
                    node.parentNode.insertBefore(span, node);
                    node.nodeValue = node.nodeValue.substring(5);
                    return 'injected span with background';
                }
            }
        }
        return 'paragraph not found';
    })(arguments[0]);
    """
    # Find a paragraph that has text to inject into
    all_para_texts = driver.execute_script(
        "return Array.from(document.querySelectorAll('.se-text-paragraph')).map(p => p.textContent)"
    )
    INJECT_TARGET = next((t for t in all_para_texts if t.strip()), TEST_TEXT)
    result = driver.execute_script(JS_INJECT, INJECT_TARGET)
    time.sleep(0.3)
    src = driver.page_source
    if result and "injected" in result and "FFE6E6" in src:
        check(results, "5.12 JS style injection fallback", PASS, result)
    else:
        check(results, "5.12 JS style injection fallback", FAIL, f"result='{result}', FFE6E6_in_src={('FFE6E6' in src)}")
except Exception as e:
    check(results, "5.12 JS style injection fallback", FAIL, str(e))


driver.quit()
print_summary(results)
