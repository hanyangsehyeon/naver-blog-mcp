"""
Naver Blog publisher.
Handles login, editor input (plain + formatted via HTML paste), and draft save.

Paragraph format expected:
  [
    {
      "text": "단락 내용",
      "formatting": [
        {"type": "highlight", "start": 0, "end": 5, "color": "#fff8b2"},
        {"type": "text_color", "start": 6, "end": 10, "color": "#e53935"},
        {"type": "bold", "start": 0, "end": 5}
      ]
    }
  ]
"""
import os, time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Selenium helpers ──────────────────────────────────────────────────────────

def _dismiss_popups(driver):
    """Dismiss known Naver Blog editor popups."""
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".se-popup-button-cancel")
        if el.is_displayed():
            el.click(); time.sleep(0.5)
    except: pass
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".se-help-panel-close-button")
        if el.is_displayed():
            el.click(); time.sleep(0.3)
    except: pass
    try:
        layer = driver.find_element(By.CSS_SELECTOR, "[class*='layer_popup_wrap']")
        if layer.is_displayed():
            for btn in layer.find_elements(By.TAG_NAME, "button"):
                if btn.text.strip() in ["취소", "닫기"]:
                    btn.click(); time.sleep(0.5); break
    except: pass


def _get_input_iframe_body(driver, index: int):
    """Switch to input_buffer iframe at index and return its body element."""
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
    driver.switch_to.frame(iframes[index])
    time.sleep(0.15)
    return driver.find_element(By.TAG_NAME, "body")


def _html_paste(driver, html: str, plain: str):
    """
    Dispatch ClipboardEvent with HTML + plain text inside the active iframe.
    Must be called while already switched into the input_buffer iframe.
    """
    driver.execute_script("""
        var dt = new DataTransfer();
        dt.setData('text/html', arguments[0]);
        dt.setData('text/plain', arguments[1]);
        var ev = new ClipboardEvent('paste', {
            clipboardData: dt, bubbles: true, cancelable: true
        });
        document.activeElement.dispatchEvent(ev);
    """, html, plain)
    time.sleep(0.5)


# ── Formatting: build HTML from paragraph spec ───────────────────────────────

def _build_html(text: str, formatting: list) -> str:
    """
    Convert text + formatting list into HTML string for paste.
    Handles overlapping ranges by merging formats per character.

    format types: "bold", "highlight" (bg color), "text_color"
    """
    if not formatting:
        return _escape(text)

    n = len(text)
    # Per-char format flags
    bold = [False] * n
    bg = [None] * n      # color string or None
    fg = [None] * n      # color string or None

    for fmt in formatting:
        s, e = fmt.get("start", 0), fmt.get("end", n)
        s, e = max(0, s), min(n, e)
        t = fmt.get("type", "")
        for i in range(s, e):
            if t == "bold":
                bold[i] = True
            elif t == "highlight":
                bg[i] = fmt.get("color", "#fff8b2")
                bold[i] = True  # rule: highlight always bold
            elif t == "text_color":
                fg[i] = fmt.get("color", "#e53935")
                bold[i] = True  # rule: text_color always bold

    # Build HTML by grouping consecutive chars with same style
    html = []
    i = 0
    while i < n:
        j = i + 1
        while j < n and bold[j] == bold[i] and bg[j] == bg[i] and fg[j] == fg[i]:
            j += 1
        chunk = _escape(text[i:j])
        if bold[i] or bg[i] or fg[i]:
            style_parts = []
            if bg[i]:
                style_parts.append(f"background-color:{bg[i]}")
            if fg[i]:
                style_parts.append(f"color:{fg[i]}")
            if bold[i]:
                style_parts.append("font-weight:bold")
            chunk = f'<span style="{";".join(style_parts)}">{chunk}</span>'
        html.append(chunk)
        i = j

    return "".join(html)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Main entry point ──────────────────────────────────────────────────────────

def publish_to_naver(driver, blog_id: str, title: str, paragraphs: list) -> dict:
    """
    Open Naver Blog editor, input title + paragraphs with formatting, save draft.

    Assumes driver is already logged in.
    Returns {"status": "saved", "url": current_url}.
    """
    driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={blog_id}")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".se-text-paragraph"))
    )
    time.sleep(2)
    _dismiss_popups(driver)
    time.sleep(0.5)
    _dismiss_popups(driver)

    # ── Title ──────────────────────────────────────────────────────────────────
    title_el = driver.find_element(By.CSS_SELECTOR, ".se-title-text")
    ActionChains(driver).move_to_element(title_el).click().perform()
    time.sleep(0.3)
    body = _get_input_iframe_body(driver, 0)
    body.send_keys(title)
    driver.switch_to.default_content()
    time.sleep(0.3)

    # ── Body paragraphs ────────────────────────────────────────────────────────
    for idx, para in enumerate(paragraphs):
        text = para.get("text", "")
        fmts = para.get("formatting", [])

        # Focus paragraph: click .se-text-paragraph, switch to body iframe
        _dismiss_popups(driver)
        paras_els = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
        target = paras_els[-1]  # always append to last paragraph
        ActionChains(driver).move_to_element(target).click().perform()
        time.sleep(0.4)
        _dismiss_popups(driver)

        iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
        driver.switch_to.frame(iframe)
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.END)
        time.sleep(0.1)

        if fmts:
            html = _build_html(text, fmts)
            _html_paste(driver, html, text)
        else:
            body.send_keys(text)
            time.sleep(0.3)

        # Add newline between paragraphs (not after the last one)
        if idx < len(paragraphs) - 1:
            body.send_keys(Keys.RETURN)
            time.sleep(0.2)

        driver.switch_to.default_content()
        time.sleep(0.2)

    # ── Draft save ─────────────────────────────────────────────────────────────
    _dismiss_popups(driver)
    save_btn = None
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        if btn.text.strip() in ["저장", "임시저장"]:
            save_btn = btn
            break

    if save_btn:
        driver.execute_script("arguments[0].click();", save_btn)
        time.sleep(2)
        _dismiss_popups(driver)

    return {"status": "saved", "url": driver.current_url}
