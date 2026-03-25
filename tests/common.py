"""Shared utilities for verification scripts"""

import os, time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
STANDARD_BLOG_ID = os.getenv("STANDARD_BLOG_ID")  # blog to crawl for style analysis
MY_BLOG_ID       = os.getenv("MY_BLOG_ID")         # blog to write/publish to

PASS, FAIL = "PASS", "FAIL"

def check(results, name, status, note=""):
    results[name] = (status, note)
    icon = "✅" if status == PASS else "❌"
    print(f"{icon} {name}: {status}" + (f" — {note}" if note else ""))

def make_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_with_qr(driver, timeout=60):
    """Open Naver login page with QR tab and wait for login completion."""
    driver.get("https://nid.naver.com/nidlogin.login")
    WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
    try:
        driver.find_element(By.ID, "qrcode").click()
    except:
        pass
    print("   👉  Please log in via QR code in the browser window.")
    WebDriverWait(driver, timeout).until(
        lambda d: "nidlogin" not in d.current_url and "/nid" not in d.current_url
    )
    print(f"   Logged in. URL: {driver.current_url}")

def dismiss_naver_popups(driver):
    """Dismiss all known Naver Blog editor popups."""
    # '작성 중인 글' dialog → 취소
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".se-popup-button-cancel")
        if el.is_displayed():
            el.click(); time.sleep(0.5)
    except: pass
    # 도움말 panel → 닫기
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".se-help-panel-close-button")
        if el.is_displayed():
            el.click(); time.sleep(0.3)
    except: pass
    # '내돈내산 기능 이용안내' modal (layer_popup_wrap) → 취소
    try:
        layer = driver.find_element(By.CSS_SELECTOR, "[class*='layer_popup_wrap']")
        if layer.is_displayed():
            for btn in layer.find_elements(By.TAG_NAME, "button"):
                if btn.text.strip() in ["취소", "닫기"]:
                    btn.click(); time.sleep(0.5); break
    except: pass


def print_summary(results):
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    passed = sum(1 for s, _ in results.values() if s == PASS)
    failed = sum(1 for s, _ in results.values() if s == FAIL)
    print(f"PASS: {passed}  FAIL: {failed}")
    if failed:
        print("\nFailed:")
        for name, (status, note) in results.items():
            if status == FAIL:
                print(f"  ❌ {name}: {note}")
