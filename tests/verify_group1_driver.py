"""
Group 1: Driver Setup Verification
Checks 1.1 ~ 1.6
"""

import os
import sys
import subprocess
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

results = {}


def check(name, status, note=""):
    results[name] = (status, note)
    icon = "✅" if status == PASS else ("❌" if status == FAIL else "⚠️")
    print(f"{icon} {name}: {status}" + (f" — {note}" if note else ""))


# ── 1.6 .env loading ────────────────────────────────────────────────────────
print("\n── 1.6 .env loading ──")
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(env_path):
        check("1.6 .env loading", FAIL, ".env file not found — create it first")
    else:
        load_dotenv(env_path)
        naver_id = os.getenv("NAVER_ID")
        naver_pw = os.getenv("NAVER_PW")
        blog_id  = os.getenv("BLOG_ID")
        missing = [k for k, v in [("NAVER_ID", naver_id), ("NAVER_PW", naver_pw), ("BLOG_ID", blog_id)] if not v]
        if missing:
            check("1.6 .env loading", FAIL, f"missing keys: {missing}")
        else:
            check("1.6 .env loading", PASS, f"BLOG_ID={blog_id}")
except Exception as e:
    check("1.6 .env loading", FAIL, str(e))


# ── Driver imports ───────────────────────────────────────────────────────────
print("\n── Driver imports ──")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    check("driver imports", PASS)
except ImportError as e:
    check("driver imports", FAIL, str(e))
    print("\nCannot continue without selenium. Exiting.")
    sys.exit(1)


# ── 1.1 Basic driver init ────────────────────────────────────────────────────
print("\n── 1.1 Basic driver init (non-headless) ──")
driver = None
try:
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    title = driver.title
    check("1.1 Basic driver init", PASS, f"opened, title='{title}'")
except Exception as e:
    check("1.1 Basic driver init", FAIL, str(e))
finally:
    if driver:
        driver.quit()
        driver = None


# ── 1.3 Non-headless visible window ─────────────────────────────────────────
print("\n── 1.3 Non-headless mode ──")
try:
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.google.com")
    title = driver.title
    check("1.3 Non-headless mode", PASS, f"title='{title}'")
except Exception as e:
    check("1.3 Non-headless mode", FAIL, str(e))
finally:
    if driver:
        driver.quit()
        driver = None


# ── 1.2 Headless mode ───────────────────────────────────────────────────────
print("\n── 1.2 Headless mode ──")
try:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.google.com")
    title = driver.title
    if title:
        check("1.2 Headless mode", PASS, f"title='{title}'")
    else:
        check("1.2 Headless mode", FAIL, "title empty in headless")
except Exception as e:
    check("1.2 Headless mode", FAIL, str(e))
finally:
    if driver:
        driver.quit()
        driver = None


# ── 1.4 Window size in headless ─────────────────────────────────────────────
print("\n── 1.4 Window size in headless ──")
try:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.google.com")
    size = driver.get_window_size()
    if size["width"] == 1920 and size["height"] == 1080:
        check("1.4 Window size in headless", PASS, f"{size}")
    else:
        check("1.4 Window size in headless", FAIL, f"got {size}, expected 1920x1080")
except Exception as e:
    check("1.4 Window size in headless", FAIL, str(e))
finally:
    if driver:
        driver.quit()
        driver = None


# ── 1.5 Driver teardown (zombie check) ──────────────────────────────────────
print("\n── 1.5 Driver teardown ──")
try:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.google.com")
    driver.quit()
    driver = None
    time.sleep(1)
    result = subprocess.run(["pgrep", "-f", "chromedriver"], capture_output=True, text=True)
    zombies = result.stdout.strip()
    if zombies:
        check("1.5 Driver teardown", FAIL, f"zombie chromedriver PIDs: {zombies}")
    else:
        check("1.5 Driver teardown", PASS, "no zombie processes")
except Exception as e:
    check("1.5 Driver teardown", FAIL, str(e))
finally:
    if driver:
        driver.quit()


# ── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("SUMMARY")
print("="*50)
passed = sum(1 for s, _ in results.values() if s == PASS)
failed = sum(1 for s, _ in results.values() if s == FAIL)
print(f"PASS: {passed}  FAIL: {failed}  SKIP: {len(results) - passed - failed}")
if failed:
    print("\nFailed items:")
    for name, (status, note) in results.items():
        if status == FAIL:
            print(f"  ❌ {name}: {note}")
