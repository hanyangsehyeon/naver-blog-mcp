"""
Group 6: Publishing Flow verification
Tests: draft save, publish button, confirmation dialog, post-URL extraction, error detection.
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
login_with_qr(driver)

driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".se-text-paragraph"))
)
time.sleep(2)
dismiss_naver_popups(driver)
time.sleep(0.5)
dismiss_naver_popups(driver)


# ── Setup: write a title + body so we have something to save/publish ─────────
def get_input_iframe_body(index=0):
    """Get body of input_buffer iframe at given index (0=title, 1=body)."""
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
    driver.switch_to.frame(iframes[index])
    time.sleep(0.2)
    body = driver.find_element(By.TAG_NAME, "body")
    return body

def write_test_content(title_text, body_text):
    # Title via input_buffer iframe[0]
    try:
        driver.switch_to.default_content()
        title_el = driver.find_element(By.CSS_SELECTOR, ".se-title-text")
        ActionChains(driver).move_to_element(title_el).click().perform()
        time.sleep(0.3)
        body = get_input_iframe_body(0)
        body.send_keys(title_text)
        driver.switch_to.default_content()
        time.sleep(0.3)
    except Exception as e:
        print(f"  [setup] title error: {e}")
        driver.switch_to.default_content()

    # Body
    try:
        paras = driver.find_elements(By.CSS_SELECTOR, ".se-text-paragraph")
        ActionChains(driver).move_to_element(paras[1]).click().perform()
        time.sleep(0.4)
        dismiss_naver_popups(driver)
        iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='input_buffer']")
        driver.switch_to.frame(iframe)
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(body_text)
        driver.switch_to.default_content()
        time.sleep(0.3)
    except Exception as e:
        print(f"  [setup] body error: {e}")
        driver.switch_to.default_content()

write_test_content("[테스트] Group6 발행 검증", "이 글은 자동화 테스트용입니다. 발행 후 삭제 예정.")
time.sleep(0.5)


# ── 6.1 Draft save button locator ────────────────────────────────────────────
print("\n=== 6.1 Draft save button locator ===")
try:
    # Try common selectors for 임시저장
    selectors_tried = []
    btn = None
    for sel in [
        ".se-draft-save-btn",
        "[class*='draft']",
        "button[data-action='draftSave']",
    ]:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            selectors_tried.append(f"FOUND: {sel}")
            break
        except:
            selectors_tried.append(f"miss: {sel}")

    # Text-based search
    if not btn:
        all_btns = driver.find_elements(By.TAG_NAME, "button")
        for b in all_btns:
            if b.text.strip() in ["임시저장", "저장"]:
                btn = b
                selectors_tried.append(f"text-match: '{b.text}' class='{b.get_attribute('class')}'")
                break

    if btn:
        cls = btn.get_attribute("class")
        check(results, "6.1_draft_btn_locator", PASS, f"class='{cls}'")
        print(f"  selector attempts: {selectors_tried}")
    else:
        check(results, "6.1_draft_btn_locator", FAIL, f"not found. tried: {selectors_tried}")
        # Dump all button texts for debugging
        all_btns = driver.find_elements(By.TAG_NAME, "button")
        print(f"  All buttons: {[b.text[:20] for b in all_btns if b.text.strip()][:20]}")
except Exception as e:
    check(results, "6.1_draft_btn_locator", FAIL, str(e))

driver.save_screenshot("tests/g6_1_draft_btn.png")


# ── 6.2 Draft save click ─────────────────────────────────────────────────────
print("\n=== 6.2 Draft save click ===")
try:
    # Find by text
    btn = None
    for b in driver.find_elements(By.TAG_NAME, "button"):
        if b.text.strip() in ["임시저장", "저장"]:
            btn = b
            break

    if not btn:
        check(results, "6.2_draft_save_click", FAIL, "저장/임시저장 button not found")
    else:
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.5)
        dismiss_naver_popups(driver)
        time.sleep(0.5)

        # Check for save confirmation (toast, modal, URL change, etc.)
        url_after = driver.current_url
        page_src = driver.page_source

        # Signs of successful save: URL gets logNo param, or toast message
        has_logno = "logNo=" in url_after or "postListPage" in url_after
        has_toast = any(kw in page_src for kw in ["임시저장", "저장되었습니다", "저장 완료"])

        driver.save_screenshot("tests/g6_2_after_draft_save.png")
        print(f"  URL after save: {url_after}")
        print(f"  has logNo in URL: {has_logno}")
        print(f"  has save toast: {has_toast}")

        if has_logno or has_toast:
            check(results, "6.2_draft_save_click", PASS, f"URL={url_after[:80]}")
        else:
            check(results, "6.2_draft_save_click", FAIL, f"no confirmation. URL={url_after[:80]}")
except Exception as e:
    check(results, "6.2_draft_save_click", FAIL, str(e))
    driver.switch_to.default_content()


# ── 6.3 Publish button locator ───────────────────────────────────────────────
print("\n=== 6.3 Publish button locator ===")
try:
    btn = None
    for sel in [
        ".se-publish-btn",
        "button[data-action='publish']",
        "[class*='publish']",
    ]:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            print(f"  FOUND via CSS: {sel}")
            break
        except:
            pass

    if not btn:
        for b in driver.find_elements(By.TAG_NAME, "button"):
            if b.text.strip() in ["발행", "게시", "공개발행"]:
                btn = b
                print(f"  FOUND via text: '{b.text}' class='{b.get_attribute('class')}'")
                break

    if btn:
        check(results, "6.3_publish_btn_locator", PASS, f"class='{btn.get_attribute('class')}'")
    else:
        check(results, "6.3_publish_btn_locator", FAIL, "발행 button not found")
        print(f"  All buttons: {[b.text[:20] for b in driver.find_elements(By.TAG_NAME, 'button') if b.text.strip()][:20]}")
except Exception as e:
    check(results, "6.3_publish_btn_locator", FAIL, str(e))

driver.save_screenshot("tests/g6_3_publish_btn.png")


# ── 6.4 Publish confirmation dialog ──────────────────────────────────────────
print("\n=== 6.4 Publish confirmation dialog ===")
try:
    btn = None
    for b in driver.find_elements(By.TAG_NAME, "button"):
        if b.text.strip() in ["발행", "게시", "공개발행"]:
            btn = b
            break

    if not btn:
        check(results, "6.4_publish_dialog", FAIL, "발행 button not found — skip")
    else:
        url_before = driver.current_url
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        dismiss_naver_popups(driver)
        time.sleep(0.5)

        driver.save_screenshot("tests/g6_4_after_publish_click.png")

        url_after = driver.current_url
        page_src = driver.page_source

        # Check for confirmation modal
        modal_found = False
        confirm_btn = None
        for sel in [
            ".se-popup-button-ok",
            "[class*='confirm']",
            "button[class*='btn_confirm']",
        ]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed():
                    modal_found = True
                    confirm_btn = el
                    print(f"  Modal found: {sel} text='{el.text}'")
                    break
            except:
                pass

        # Also search by button text
        if not modal_found:
            for b in driver.find_elements(By.TAG_NAME, "button"):
                if b.text.strip() in ["확인", "발행", "게시하기"] and b.is_displayed():
                    modal_found = True
                    confirm_btn = b
                    print(f"  Modal button found: '{b.text}' class='{b.get_attribute('class')}'")
                    break

        # Check if already published (navigated away)
        already_published = url_after != url_before and "PostWriteForm" not in url_after

        if modal_found:
            check(results, "6.4_publish_dialog", PASS, f"modal present, confirm btn: '{confirm_btn.text}'")
        elif already_published:
            check(results, "6.4_publish_dialog", PASS, f"no dialog — published directly. URL={url_after[:80]}")
        else:
            check(results, "6.4_publish_dialog", FAIL, f"unknown state. URL={url_after[:80]}")
            print(f"  Visible buttons: {[b.text[:20] for b in driver.find_elements(By.TAG_NAME, 'button') if b.is_displayed() and b.text.strip()][:15]}")
except Exception as e:
    check(results, "6.4_publish_dialog", FAIL, str(e))
    driver.switch_to.default_content()


# ── 6.5 Category / visibility settings ───────────────────────────────────────
print("\n=== 6.5 Category / visibility settings ===")
try:
    page_src = driver.page_source
    # Look for category, public/private, tags setting in current state
    has_category = any(kw in page_src for kw in ["카테고리", "category"])
    has_visibility = any(kw in page_src for kw in ["공개", "비공개", "전체공개"])
    has_tags = any(kw in page_src for kw in ["태그", "tag"])

    driver.save_screenshot("tests/g6_5_settings.png")
    print(f"  category UI present: {has_category}")
    print(f"  visibility UI present: {has_visibility}")
    print(f"  tags UI present: {has_tags}")

    if has_visibility:
        check(results, "6.5_publish_settings", PASS, f"category={has_category} visibility={has_visibility} tags={has_tags}")
    else:
        check(results, "6.5_publish_settings", FAIL, "visibility setting not found in current state")
except Exception as e:
    check(results, "6.5_publish_settings", FAIL, str(e))


# ── 6.6 Confirm publish + extract post URL ───────────────────────────────────
print("\n=== 6.6 Post-publish URL extraction ===")
try:
    url_before = driver.current_url
    confirm_btn = None

    # Find confirm/publish button in current state (modal or direct)
    for b in driver.find_elements(By.TAG_NAME, "button"):
        if b.text.strip() in ["확인", "발행", "게시하기", "공개발행"] and b.is_displayed():
            confirm_btn = b
            print(f"  Clicking: '{b.text}'")
            break

    if not confirm_btn:
        # Maybe already published from 6.4 click
        if "PostWriteForm" not in url_before:
            post_url = url_before
            check(results, "6.6_post_url_extraction", PASS, f"already published: {post_url[:80]}")
        else:
            check(results, "6.6_post_url_extraction", FAIL, "no confirm button found and still on write form")
    else:
        driver.execute_script("arguments[0].click();", confirm_btn)
        time.sleep(3)
        dismiss_naver_popups(driver)
        time.sleep(1)

        url_after = driver.current_url
        driver.save_screenshot("tests/g6_6_after_confirm.png")
        print(f"  URL after confirm: {url_after}")

        # Post URL patterns: logNo= in URL, or blog.naver.com/{blogId}/{logNo}
        is_post_url = (
            "logNo=" in url_after or
            ("blog.naver.com" in url_after and "PostWriteForm" not in url_after and "nidlogin" not in url_after)
        )
        if is_post_url:
            check(results, "6.6_post_url_extraction", PASS, url_after[:100])
        else:
            check(results, "6.6_post_url_extraction", FAIL, f"unexpected URL: {url_after[:100]}")
except Exception as e:
    check(results, "6.6_post_url_extraction", FAIL, str(e))
    driver.switch_to.default_content()


# ── 6.7 Error state detection ────────────────────────────────────────────────
print("\n=== 6.7 Error state detection (new post, no title) ===")
try:
    # Open a fresh write form
    driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={MY_BLOG_ID}")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".se-text-paragraph"))
    )
    time.sleep(2)
    dismiss_naver_popups(driver)
    time.sleep(0.5)
    dismiss_naver_popups(driver)

    # Click publish WITHOUT providing title → should show error
    btn = None
    for b in driver.find_elements(By.TAG_NAME, "button"):
        if b.text.strip() in ["발행", "게시", "공개발행"]:
            btn = b
            break

    if not btn:
        check(results, "6.7_error_detection", FAIL, "발행 button not found on fresh form")
    else:
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.5)
        dismiss_naver_popups(driver)
        time.sleep(0.5)

        driver.save_screenshot("tests/g6_7_publish_no_title.png")
        page_src = driver.page_source

        # Look for validation error indicators
        error_found = any(kw in page_src for kw in [
            "제목", "입력", "필수", "오류", "error", "alert", "validation"
        ])
        # Or: still on write form (publish blocked)
        still_on_form = "PostWriteForm" in driver.current_url or "se-text-paragraph" in page_src

        print(f"  error_found: {error_found}")
        print(f"  still_on_form: {still_on_form}")

        if error_found or still_on_form:
            check(results, "6.7_error_detection", PASS, f"error_found={error_found} still_on_form={still_on_form}")
        else:
            check(results, "6.7_error_detection", FAIL, f"published without title? URL={driver.current_url[:80]}")
except Exception as e:
    check(results, "6.7_error_detection", FAIL, str(e))
    driver.switch_to.default_content()


print_summary(results)
driver.quit()
