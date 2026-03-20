"""
Group 3: Blog Post Crawling (Style Analysis) Verification
Checks 3.1 ~ 3.8
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.common import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

results = {}

driver = make_driver(headless=False)
print("\n── Login ──")
login_with_qr(driver)


# ── 3.1 Blog main page load ──────────────────────────────────────────────────
print("\n── 3.1 Blog main page load ──")
try:
    driver.get(f"https://blog.naver.com/{BLOG_ID}")
    WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
    check(results, "3.1 Blog main page load", PASS, driver.title or driver.current_url)
except Exception as e:
    check(results, "3.1 Blog main page load", FAIL, str(e))


# ── 3.2 Post list selector ───────────────────────────────────────────────────
print("\n── 3.2 Post list selector ──")
post_urls = []
try:
    # Blog post list is inside mainFrame iframe
    iframe = driver.find_element(By.ID, "mainFrame")
    driver.switch_to.frame(iframe)
    time.sleep(1)

    all_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='PostView.naver'][href*='logNo=']")
    post_urls = list(dict.fromkeys(
        "https://blog.naver.com" + l.get_attribute("href") if l.get_attribute("href").startswith("/") else l.get_attribute("href")
        for l in all_links if l.get_attribute("href")
    ))[:5]
    driver.switch_to.default_content()

    if post_urls:
        check(results, "3.2 Post list selector", PASS, f"{len(post_urls)} posts found")
        for u in post_urls:
            print(f"   {u}")
    else:
        check(results, "3.2 Post list selector", FAIL, "no post links found inside mainFrame")
except Exception as e:
    driver.switch_to.default_content()
    check(results, "3.2 Post list selector", FAIL, str(e))


# ── 3.3 ~ 3.7: Test on first post ───────────────────────────────────────────
if not post_urls:
    print("\n⚠️  No post URLs found — skipping 3.3~3.7")
    for n in ["3.3", "3.4", "3.5", "3.6"]:
        check(results, f"{n} (skipped)", FAIL, "no post URLs from 3.2")
else:
    post_url = post_urls[0]
    print(f"\n── Testing on: {post_url} ──")

    # ── 3.3 Viewer iframe detection ─────────────────────────────────────────
    print("\n── 3.3 Viewer iframe detection ──")
    try:
        driver.get(post_url)
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(1)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        iframe_ids = [f.get_attribute("id") for f in iframes]
        if "mainFrame" in iframe_ids:
            driver.switch_to.frame(driver.find_element(By.ID, "mainFrame"))
            check(results, "3.3 Viewer iframe detection", PASS, "mainFrame found and switched")
        else:
            # PostView.naver renders content directly without mainFrame
            check(results, "3.3 Viewer iframe detection", PASS,
                  f"no mainFrame — content rendered directly (iframes: {iframe_ids})")
    except Exception as e:
        check(results, "3.3 Viewer iframe detection", FAIL, str(e))
        driver.switch_to.default_content()

    # ── 3.4 Smart Editor ONE DOM in iframe ──────────────────────────────────
    print("\n── 3.4 Smart Editor ONE DOM in iframe ──")
    try:
        src = driver.page_source
        if "se-text-paragraph" in src:
            count = src.count("se-text-paragraph")
            check(results, "3.4 Smart Editor ONE DOM in iframe", PASS, f"se-text-paragraph found ({count} occurrences)")
        else:
            # Older editor fallback
            if "se_textarea" in src or "post-view" in src:
                check(results, "3.4 Smart Editor ONE DOM in iframe", PASS, "older editor structure found (not Smart Editor ONE)")
            else:
                check(results, "3.4 Smart Editor ONE DOM in iframe", FAIL, "no known editor structure found")
    except Exception as e:
        check(results, "3.4 Smart Editor ONE DOM in iframe", FAIL, str(e))

    # ── 3.5 BeautifulSoup parse ─────────────────────────────────────────────
    print("\n── 3.5 BeautifulSoup parse ──")
    try:
        soup = BeautifulSoup(driver.page_source, "lxml")
        paras = soup.select(".se-text-paragraph")
        bolds = soup.select(".se-bold")
        bg_spans = [s for s in soup.select("span[style]") if "background-color" in s.get("style", "")]
        print(f"   paragraphs: {len(paras)}, bold: {len(bolds)}, background-color spans: {len(bg_spans)}")
        if paras:
            check(results, "3.5 BeautifulSoup parse", PASS,
                  f"{len(paras)} paragraphs, {len(bolds)} bold, {len(bg_spans)} bg-color")
        else:
            check(results, "3.5 BeautifulSoup parse", FAIL, "no .se-text-paragraph found by BS4")
    except Exception as e:
        check(results, "3.5 BeautifulSoup parse", FAIL, str(e))

    # ── 3.6 Switching back from iframe ──────────────────────────────────────
    print("\n── 3.6 Switching back from iframe ──")
    try:
        driver.switch_to.default_content()
        _ = driver.current_url  # should not raise
        check(results, "3.6 Switching back from iframe", PASS)
    except Exception as e:
        check(results, "3.6 Switching back from iframe", FAIL, str(e))

    # ── 3.7 Crawl rate / bot detection ──────────────────────────────────────
    print("\n── 3.7 Crawl rate / bot detection ──")
    try:
        blocked = False
        for url in post_urls[:3]:
            driver.get(url)
            time.sleep(0.5)
            if "차단" in driver.page_source or "block" in driver.current_url.lower():
                blocked = True
                break
        if blocked:
            check(results, "3.7 Crawl rate / bot detection", FAIL, "bot block detected — add sleep between requests")
        else:
            check(results, "3.7 Crawl rate / bot detection", PASS, "no block on rapid crawl of 3 posts")
    except Exception as e:
        check(results, "3.7 Crawl rate / bot detection", FAIL, str(e))


# ── 3.8 Login required for crawling ─────────────────────────────────────────
print("\n── 3.8 Login required for crawling ──")
try:
    driver2 = make_driver(headless=True)
    driver2.get(f"https://blog.naver.com/{BLOG_ID}")
    WebDriverWait(driver2, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
    src = driver2.page_source
    if "nidlogin" in driver2.current_url or "로그인" in src[:500]:
        check(results, "3.8 Login required for crawling", FAIL, "redirected to login — login required for crawling")
    else:
        check(results, "3.8 Login required for crawling", PASS, "public blog accessible without login")
    driver2.quit()
except Exception as e:
    check(results, "3.8 Login required for crawling", FAIL, str(e))


driver.quit()
print_summary(results)
