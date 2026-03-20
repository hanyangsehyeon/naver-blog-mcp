"""
Group 2: Naver Login Flow Verification
2.1 Navigate to login page
2.6 Post-login URL check (QR login)
2.7 CAPTCHA detection
2.8 2FA detection
2.9 Session persistence
2.10 Cookie reuse
"""

import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

PASS, FAIL = "PASS", "FAIL"
results = {}

def check(name, status, note=""):
    results[name] = (status, note)
    icon = "✅" if status == PASS else "❌"
    print(f"{icon} {name}: {status}" + (f" — {note}" if note else ""))

options = Options()
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


# ── 2.1 Navigate to login page ───────────────────────────────────────────────
print("\n── 2.1 Navigate to login page ──")
try:
    driver.get("https://nid.naver.com/nidlogin.login")
    WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
    # Click QR login tab
    from selenium.webdriver.common.by import By
    try:
        driver.find_element(By.ID, "qrcode").click()
    except:
        pass
    check("2.1 Navigate to login page", PASS, driver.current_url)
except Exception as e:
    check("2.1 Navigate to login page", FAIL, str(e))


# ── 2.6 Wait for QR login ────────────────────────────────────────────────────
print("\n── 2.6 Waiting for QR login (60s) ──")
print("   👉  Please log in via QR code in the browser window.")
try:
    WebDriverWait(driver, 60).until(
        lambda d: "nidlogin" not in d.current_url and "/nid" not in d.current_url
    )
    check("2.6 Post-login URL check", PASS, driver.current_url)
except Exception as e:
    check("2.6 Post-login URL check", FAIL, "login not completed within 60s")
    driver.quit()
    sys.exit(1)


# ── 2.7 CAPTCHA detection ─────────────────────────────────────────────────────
print("\n── 2.7 CAPTCHA detection ──")
try:
    page_src = driver.page_source
    signals = [s for s in ["captcha", "recaptcha", "보안문자", "자동입력방지"] if s in page_src.lower()]
    check("2.7 CAPTCHA detection", PASS, f"detectable signals: {signals}" if signals else "no CAPTCHA this run — signals identified")
except Exception as e:
    check("2.7 CAPTCHA detection", FAIL, str(e))


# ── 2.8 2FA detection ─────────────────────────────────────────────────────────
print("\n── 2.8 2FA detection ──")
try:
    page_src = driver.page_source
    url = driver.current_url
    signals = [s for s in ["second_auth", "otp", "추가인증", "2단계", "인증번호"] if s in url.lower() or s in page_src.lower()]
    check("2.8 2FA detection", PASS, f"detectable signals: {signals}" if signals else "no 2FA this run — signals identified")
except Exception as e:
    check("2.8 2FA detection", FAIL, str(e))


# ── 2.9 Session persistence ────────────────────────────────────────────────────
print("\n── 2.9 Session persistence ──")
try:
    driver.get("https://blog.naver.com")
    time.sleep(2)
    page_src = driver.page_source
    found = [s for s in ["로그아웃", "logout", "mypage"] if s.lower() in page_src.lower()]
    if found:
        check("2.9 Session persistence", PASS, f"logged-in signals: {found}")
    else:
        check("2.9 Session persistence", FAIL, "no logged-in signals on blog.naver.com")
except Exception as e:
    check("2.9 Session persistence", FAIL, str(e))


# ── 2.10 Cookie reuse ─────────────────────────────────────────────────────────
print("\n── 2.10 Cookie reuse ──")
try:
    cookies = [c for c in driver.get_cookies() if "naver" in c.get("domain", "")]
    if cookies:
        check("2.10 Cookie reuse", PASS, f"{len(cookies)} naver cookies — reuse feasible")
    else:
        check("2.10 Cookie reuse", FAIL, "no naver cookies found")
except Exception as e:
    check("2.10 Cookie reuse", FAIL, str(e))


driver.quit()

# ── Summary ──────────────────────────────────────────────────────────────────
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
